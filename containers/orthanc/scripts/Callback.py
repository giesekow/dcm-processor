from pprint import pprint
import orthanc
import json, os, requests
import threading

SUPPORTED_MODALITY = os.getenv("SUPPORTED_MODALITY", "CT,MR")

def OnChange(changeType, level, resource):
  if changeType == orthanc.ChangeType.STABLE_PATIENT:
    t = threading.Thread(target=stablePatient, args=(resource,))
    t.start()

def stablePatient(patientId):
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
      can_process, tags = process_series(seriesId, baseDir)
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

def process_series(seriesId, baseDir):
  TARGET = '/tmp/nifti'
  series = json.loads(orthanc.RestApiGet(f"/series/{seriesId}"))
  instances = series['Instances']
  
  if len(instances) > 3:
    data = json.loads(orthanc.RestApiGet(f"/instances/{instances[0]}/simplified-tags"))
    ActionSource = data.get("ActionSource")

    if not ActionSource is None:
      return False, data

    modality = data.get("Modality")
    if modality is None:
      return False, data

    mods = SUPPORTED_MODALITY.split(",")
    mods = [str(s).lower() for s in mods]

    if not str(modality).lower().strip() in mods:
      print(f"Modality {modality} not supported, skipping!")
      remove_series(seriesId)
      return

    print("Stable Series Received, Storing series on disk: " + seriesId, flush=True)

    dcmpath = os.path.join(TARGET, baseDir , seriesId)
    os.system(f"mkdir -p {dcmpath}")

    for i, instance in enumerate(instances):
      dicom = orthanc.RestApiGet(f"/instances/{instance}/file")
      with open(os.path.join(dcmpath, f"{instance}.dcm"), "wb") as file:
        file.write(dicom)

    return True, data
  else:
    print('EXIT: No valied DICOM Series for NIFTI Conversion!')
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
  tags = json.loads(dicom.GetInstanceSimplifiedJson())

  ActionSource = tags.get('ActionSource')
  Action = tags.get('Action')
  ActionDestination = tags.get('ActionDestination')

  if ActionSource == "dcm-processor":
    if Action == 'store-data':
      try:
        print(f"Storing Data From {ActionSource} To {ActionDestination}")
        orthanc.RestApiPost(f"/modalities/{ActionDestination}/store", instanceId)
      except ValueError as e:
        print(f"Value Error: {e}")
      except:
        print("Error posting to modality")

orthanc.RegisterOnStoredInstanceCallback(OnStoredInstance)
orthanc.RegisterOnChangeCallback(OnChange)
