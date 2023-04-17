import SimpleITK as sitk
import time, os, requests
import numpy as np
import os.path

def get_slope_and_intercept(image):
  arr = sitk.GetArrayFromImage(image)
  dtype = arr.dtype
  intercept = 0
  slope = 1
  changed = False

  if dtype in ["float32", "float64", "float", "int32", "int64", "int", "int16"]:
    min_val = 0
    max_val = 2**16
    img_min = np.min(arr)

    if img_min < min_val:
      intercept =  (min_val - img_min)

    img_max = np.max(arr) + intercept

    if img_max > max_val:
      slope = (max_val / img_max)

    changed = True

  return slope, intercept, dtype, changed

def write_slices(writer, series_tag_values, new_img, out_dir, i):
  image_slice = new_img[:, :, i]

  # Tags shared by the series.
  list(map(lambda tag_value: image_slice.SetMetaData(tag_value[0], tag_value[1]), series_tag_values))

  # Slice specific tags.
  #   Instance Creation Date
  image_slice.SetMetaData("0008|0012", time.strftime("%Y%m%d"))
  #   Instance Creation Time
  image_slice.SetMetaData("0008|0013", time.strftime("%H%M%S"))

  # Setting the type to CT so that the slice location is preserved and
  # the thickness is carried over.
  # image_slice.SetMetaData("0008|0060", "CT")

  # (0020, 0032) image position patient determines the 3D spacing between
  # slices.
  #   Image Position (Patient)
  image_slice.SetMetaData("0020|0032", '\\'.join(map(str, new_img.TransformIndexToPhysicalPoint((0, 0, i)))))
  #   Instance Number
  image_slice.SetMetaData("0020|0013", str(i + 1))

  # Write to the output directory and add the extension dcm, to force
  # writing in DICOM format.
  writer.SetFileName(os.path.join(out_dir, str(i + 1).zfill(5) + '.dcm'))
  writer.Execute(image_slice)

def nifti_to_dicom(filename, outpath, headers):

  reader = sitk.ImageFileReader()
  reader.SetFileName(filename)

  new_img = reader.Execute()
  slope, intercept, pixel_dtype, dtype_changed = get_slope_and_intercept(new_img)

  writer = sitk.ImageFileWriter()
  writer.KeepOriginalImageUIDOn()

  modification_time = time.strftime("%H%M%S")
  modification_date = time.strftime("%Y%m%d")

  direction = new_img.GetDirection()
  series_tag_values = headers
  series_tag_values = series_tag_values + [
    ("0008|0031", modification_time),  # Series Time
    ("0008|0021", modification_date),  # Series Date
    ('0020|0011', modification_date + modification_time), # Series Number
    ("0008|0008", "DERIVED\\SECONDARY"),  # Image Type
    ("0020|000e", "1.2.826.0.1.3680043.2.1125."
      + modification_date + ".1" + modification_time),  # Series Instance UID
    ("0020|0037", '\\'.join(map(str, (direction[0], direction[3], direction[6],
                                      direction[1], direction[4],
                                      direction[7])))),  # Image Orientation
  ]

  if dtype_changed:
    series_tag_values = series_tag_values + [
      ('0028|1053', str(slope)),  # rescale slope
      ('0028|1052', str(intercept)),  # rescale intercept
      ('0028|0100', '16'),  # bits allocated
      ('0028|0101', '16'),  # bits stored
      ('0028|0102', '15'),  # high bit
      ('0028|0103', '1')]  # pixel representation

  # Write slices to output directory
  list(map(lambda i: write_slices(writer, series_tag_values, new_img, outpath, i), range(new_img.GetDepth())))

def load_and_update_meta(inPath, outPath, tags):
  series_IDs = sitk.ImageSeriesReader.GetGDCMSeriesIDs(inPath)
  if not series_IDs:
    print("ERROR: given directory \""+inPpath+"\" does not contain a DICOM series.")
    return
    
  series_file_names = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(inPath, series_IDs[0])

  series_reader = sitk.ImageSeriesReader()
  series_reader.SetFileNames(series_file_names)

  series_reader.MetaDataDictionaryArrayUpdateOn()
  series_reader.LoadPrivateTagsOn()
  image = series_reader.Execute()

  writer = sitk.ImageFileWriter()
  writer.KeepOriginalImageUIDOn()

  direction = image.GetDirection()

  modification_time = time.strftime("%H%M%S")
  modification_date = time.strftime("%Y%m%d")
  series_tag_values = [(k.replace("-", "|"), tags[k]) for k in tags.keys()]
  series_tag_values += [
    ("0008|0031", modification_time),  # Series Time
    ("0008|0021", modification_date),  # Series Date
    ('0020|0011', modification_date + modification_time), # Series Number
    ("0008|0008", "DERIVED\\SECONDARY"),  # Image Type
    ("0020|000e", "1.2.826.0.1.3680043.2.1125."
      + modification_date + ".1" + modification_time),  # Series Instance UID
    ("0020|0037", '\\'.join(map(str, (direction[0], direction[3], direction[6],
                                      direction[1], direction[4],
                                      direction[7])))),  # Image Orientation
  ]

  list(map(lambda i: write_slices(writer, series_tag_values, image, outPath, i), range(image.GetDepth())))

def upload_file(path, headers, authOrthanc, URL):

  f = open(path, "rb")
  content = f.read()
  f.close()

  try:
    resp = requests.post(URL + "/instances", data=content, auth=authOrthanc, headers=headers)
    if resp.status_code == 200:
      return resp.json()["ParentSeries"]
    else:
      return None

  except Exception as e:
    print(f"Error: {e}")
    return False

def import_dicom_to_orthanc(dcmpath, orthanc_url, username, password):
  success_count = 0
  total_file_count = 0

  headers = { 'content-type' : 'application/dicom' }
  authOrthanc = (username, password)

  URL = orthanc_url

  seriesId = None

  if os.path.isfile(dcmpath):
    # Upload a single file
    total_file_count += 1
    seriesId = upload_file(dcmpath, headers, URL)
    if not seriesId is None:
      success_count += 1

  else:
    # Recursively upload a directory
    for root, dirs, files in os.walk(dcmpath):
      for f in files:
        total_file_count += 1
        seriesId = upload_file(os.path.join(root, f), headers, authOrthanc, URL)
        if not seriesId is None:
          success_count += 1

  if success_count == total_file_count:
    print("\nSummary: all %d DICOM file(s) have been imported successfully" % success_count)
  else:
    print("\nSummary: %d out of %d files have been imported successfully as DICOM instances" % (success_count, total_file_count))

  return seriesId