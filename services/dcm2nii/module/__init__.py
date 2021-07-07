import os
import glob

DATA = os.getenv("DATA")
dir_path = os.path.dirname(os.path.realpath(__file__))

def worker(jobName, headers, params, added_params, **kwargs):
  a_params = added_params.get(jobName)
  
  if (not DATA is None) and (not a_params is None):
    base = a_params.get("base")
    filename = a_params.get("filename")
    ext = a_params.get("ext", ".nii.gz")
    dcmpath = headers.get("dcmpath")

    if (not base is None) and (not filename is None) and (not dcmpath is None):
      dcm2niix = os.path.join(dir_path, "dcm2niix")
      fullbase = os.path.join(DATA, base)
      tmpfolder = os.path.join(fullbase, filename)
      fulldcmpath = os.path.join(DATA, dcmpath)
      command = f"{dcm2niix} -z y -b n -f {filename} -o {tmpfolder} {fulldcmpath}"
      os.system(f"mkdir -p {tmpfolder}")
      os.system(command)
      selected_file = get_max_file(tmpfolder)
      if not selected_file is None:
        fullFilename = f"{filename}{ext}"
        os.system(f"mv {selected_file} {os.path.join(fullbase, fullFilename)}")
        os.system(f"rm -rf {tmpfolder}")

def get_max_file(searchpath):
  searchText = os.path.join(searchpath, "*.nii.gz")
  filenames = glob.glob(searchText)
  if len(filenames) == 1:
    return filenames[0]
  elif len(filenames) > 1:
    ind = 0
    m_size = os.path.getsize(filenames[0])
    for i in range(1, len(filenames)):
      c_size = os.path.getsize(filenames[i])
      if c_size > m_size:
        ind = i
        m_size = c_size
    return filenames[ind]
  else:
    return None