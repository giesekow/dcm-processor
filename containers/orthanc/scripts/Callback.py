from pprint import pprint
import orthanc
import json, os, requests
import threading, copy
import numpy as np


SUPPORTED_MODALITY = os.getenv("SUPPORTED_MODALITY", "CT,MR")
PENDING_INSTANCES = []

JUNK_FILES = os.getenv("JUNK_FILES", ",".join(["sbi","surv","bersi","racker","ssde","results", "mip", "mono", "spectal", "scout", "localizer", "lokali", "konturen", "sectrareconstruction", "zeffect", "iodoinekein", "smartplan", "doseinf"])).split(",")
ACCEPTED_FILES = os.getenv("ACCEPTED_FILES", "primary").split(",")

def OnChange(changeType, level, resource):
  global PENDING_INSTANCES
  if changeType == orthanc.ChangeType.STABLE_PATIENT:
    if len(PENDING_INSTANCES) > 0:
      pending_instance = copy.deepcopy(PENDING_INSTANCES)
      PENDING_INSTANCES = []
      t = threading.Thread(target=stablePatient, args=(resource, pending_instance))
      t.start()

def stablePatient(patientId, pending_instances):
  patient = json.loads(orthanc.RestApiGet(f"/patients/{patientId}"))
  studies = patient.get("Studies", [])
  savedStudies = []
  patientSeries = []
  patientStudies = []
  baseDir = os.path.join("dicom", patientId)
  for studyId in studies:
    study = json.loads(orthanc.RestApiGet(f"/studies/{studyId}"))
    series = study.get("Series", [])
    savedSeries = []
    for seriesId in series:
      can_process, tags = process_series(seriesId, baseDir, pending_instances)
      if can_process:
        savedSeries.append({"id": seriesId, "tags": tags})
        patientSeries.append(seriesId)
    
    if len(savedSeries) > 0:
      patientStudies.append(studyId)
      savedStudies.append({
        "id": studyId,
        "series": savedSeries,
        "tags": study.get("MainDicomTags", {})
      })

  if len(savedStudies) > 0:
    print(f"Stable patient sending it to job scheduler: {patientId}", flush=True)
    data = {
      "id": patientId,
      "tags": patient.get("MainDicomTags", {}),
      "studies": savedStudies,
      "studyIds": patientStudies,
      "seriesIds": patientSeries
    }

    urlAddress = f"{os.getenv('SCHEDULER_HOST')}:{os.getenv('SCHEDULER_PORT')}/stable-patient"
    data["dcmpath"] = baseDir

    headers = {}
    headers["Content-Type"] = "application/json"
    response = requests.post(urlAddress, json=data, headers=headers)
    if response.status_code != 200:
      print(response.reason, flush=True)

def process_series(seriesId, baseDir, pending_instances):
  TARGET = '/tmp/nifti'
  series = json.loads(orthanc.RestApiGet(f"/series/{seriesId}"))
  instances = series['Instances']

  instances, rem_instances = remove_unlabelled_localizers(list([i for i in instances if i in pending_instances]))
  remove_instances_from_pending(pending_instances, rem_instances)
  
  if len(instances) > 3:
    data = json.loads(orthanc.RestApiGet(f"/instances/{instances[0]}/simplified-tags"))
    ActionSource = data.get("ActionSource")

    if not ActionSource is None:
      remove_instances_from_pending(pending_instances, instances)
      remove_series(seriesId)
      return False, data

    modality = data.get("Modality")
    if modality is None:
      remove_instances_from_pending(pending_instances, instances)
      remove_series(seriesId)
      return False, data

    mods = SUPPORTED_MODALITY.split(",")
    mods = [str(s).lower() for s in mods]

    if not str(modality).lower().strip() in mods:
      print(f"Modality {modality} not supported, skipping!")
      remove_instances_from_pending(pending_instances, instances)
      remove_series(seriesId)
      return False, data
    
    image_type = data.get("ImageType", "")
    s_desc = data.get("SeriesDescription", "")
    i_comm = data.get("ImageComments", "")

    if isinstance(image_type, list): image_type = ",".join(image_type)
    if isinstance(s_desc, list): s_desc = ",".join(s_desc)
    if isinstance(i_comm, list): i_comm = ",".join(i_comm)

    image_type = f"{image_type},{s_desc},{i_comm}".strip()

    if image_type == "":
      remove_instances_from_pending(pending_instances, instances)
      remove_series(seriesId)
      return False, data
    
    image_type = str(image_type).lower()

    is_accepted = False
    for af in ACCEPTED_FILES:
      if image_type.__contains__(str(af).lower()):
        is_accepted = True
        break

    if not is_accepted:
      remove_instances_from_pending(pending_instances, instances)
      remove_series(seriesId)
      return False, data

    for jf in JUNK_FILES:
      if image_type.__contains__(str(jf).lower()):
        remove_instances_from_pending(pending_instances, instances)
        remove_series(seriesId)
        return False, data

    print("Stable Series Received, Storing series on disk: " + seriesId, flush=True)

    dcmpath = os.path.join(TARGET, baseDir , seriesId)
    os.system(f"mkdir -p {dcmpath}")
    hasData = False

    for i, instance in enumerate(instances):
      if not instance in pending_instances:
        continue

      pending_instances.remove(instance)
      dicom = orthanc.RestApiGet(f"/instances/{instance}/file")

      with open(os.path.join(dcmpath, f"{instance}.dcm"), "wb") as file:
        file.write(dicom)
        hasData = True
    
    if not hasData:
      remove_instances_from_pending(pending_instances, instances)
      remove_series(seriesId)  

    return hasData, data
  else:
    print('EXIT: No valied DICOM Series for NIFTI Conversion!')
    remove_instances_from_pending(pending_instances, instances)
    remove_series(seriesId)
    return False, {}

def remove_series(seriesId):
  study = json.loads(orthanc.RestApiGet(f"/series/{seriesId}/study"))
  series = study.get("Series", [])
  removeStudy = False
  removePatient = False
  if len(series) <= 1:
    removeStudy = True

  if removeStudy:
    patient = json.loads(orthanc.RestApiGet(f"/series/{seriesId}/patient"))
    studies = patient.get("Studies", [])
    if len(studies) <= 1:
      removePatient = True

  if removePatient:
    pid = patient.get('ID')
    orthanc.RestApiDelete(f"/patients/{pid}")
  elif removeStudy:
    sid = study.get('ID')
    orthanc.RestApiDelete(f"/studies/{sid}")
  else:
    orthanc.RestApiDelete(f"/series/{seriesId}")

def OnStoredInstance(dicom, instanceId):
  global PENDING_INSTANCES
      
  tags = json.loads(dicom.GetInstanceSimplifiedJson())

  ActionSource = tags.get('ActionSource')
  Action = tags.get('Action')
  ActionDestination = tags.get('ActionDestination')

  if ActionSource == "dcm-processor":
    if Action == 'store-data' and not (ActionDestination is None):
      try:
        print(f"Storing Data From {ActionSource} To {ActionDestination}")
        orthanc.RestApiPost(f"/modalities/{ActionDestination}/store", instanceId)
      except ValueError as e:
        print(f"Value Error: {e}")
      except:
        print("Error posting to modality")
  elif ActionSource is None:
    PENDING_INSTANCES.append(instanceId)

def remove_instances_from_pending(pending_instances, rem_instances):
  for instance in rem_instances:
    if instance in pending_instances:
      pending_instances.remove(instance)


# Filtering instances
def remove_unlabelled_localizers(instances):
  im_orientations = []
  removed_instances = []
  remaining_instances = []

  for instance in instances:
    tags = json.loads(orthanc.RestApiGet(f"/instances/{instance}/simplified-tags"))
    
    is_valid = _is_valid_imaging_dicom(tags, instance)
    
    if is_valid:
      ImageOrientationPatient = tags.get("ImageOrientationPatient")
      ImageOrientationPatient = [float(f) for f in str(ImageOrientationPatient).split('\\')]
      im_orientations.append(str([np.round(item,2) for item in ImageOrientationPatient]))
    else:
      im_orientations.append(f"remove_{instance}")

  values, counts = np.unique(im_orientations, return_counts=True)

  if len(counts) > 1:
    to_keep = values[np.argmax(counts)]
    
    for i,x in enumerate(im_orientations):
      if str(x).__contains__("remove"):
        removed_instances.append(instances[i])
      elif x != to_keep:
        removed_instances.append(instances[i])
      else:
        remaining_instances.append(instances[i])
  else:
    remaining_instances = instances

  return remaining_instances, removed_instances

def _is_valid_imaging_dicom(header, instance):
  """
  Function will do some basic checks to see if this is a valid imaging dicom
  """
  # if it is philips and multiframe dicom then we assume it is ok
  try:
    if is_manufacturer(header, 'philips'):
      if is_multiframe_dicom(instance):
        return True
    if "SeriesInstanceUID" not in header:
      return False
    if "InstanceNumber" not in header:
      return False
    if "ImageOrientationPatient" not in header or len(header.get("ImageOrientationPatient")) < 6:
      return False
    if "ImagePositionPatient" not in header or len(header.get("ImagePositionPatient")) < 3:
      return False
    if "ImageType" in header:
      if "LOCALIZER" in header.get("ImageType"):
        return False
      if "OTHER" in header.get("ImageType"):
        return False
    
    # for all others if there is image position patient we assume it is ok
    if 	"ImageOrientationPatient" not in header:
      return False
    
    return True
  except (KeyError, AttributeError):
    return False

def is_manufacturer(header, manufucturer):
  if not ('Manufacturer' in header) or not ('Modality' in header):
    return False  # we try generic conversion in these cases

  # check if Modality is mr
  if header.get("Modality").upper() != 'MR':
    return False

  # check if manufacturer is Philips
  if not (manufucturer.upper() in header.get("Manufacturer").upper()):
    return False

  return True

def is_multiframe_dicom(instance):
  try:
    tag_value = orthanc.RestApiGet(f"/instances/{instance}/content/0002-0002")
    if tag_value == '1.2.840.10008.5.1.4.1.1.4.1':
      return True
  except Exception as e:
    print(f"ACCESS ERROR: {e}")
    
  return False

orthanc.RegisterOnStoredInstanceCallback(OnStoredInstance)
orthanc.RegisterOnChangeCallback(OnChange)
