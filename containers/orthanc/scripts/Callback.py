from pprint import pprint
import orthanc
import json, os, requests
import threading

SUPPORTED_MODALITY = os.getenv("SUPPORTED_MODALITY", "CT,MR")

def OnChange(changeType, level, resource):
  if changeType == orthanc.ChangeType.STABLE_SERIES:
    t = threading.Thread(target=stableSeries, args=(resource,))
    t.start()

def stableSeries(seriesId):
  TARGET = '/tmp/nifti'
  series = json.loads(orthanc.RestApiGet(f"/series/{seriesId}"))
  instances = series['Instances']
  
  if len(instances) > 3:
    patientId = json.loads(orthanc.RestApiGet(f"/series/{seriesId}/patient")) ['ID']
    studyId = json.loads(orthanc.RestApiGet(f"/series/{seriesId}/study")) ['ID']
    data = json.loads(orthanc.RestApiGet(f"/instances/{instances[0]}/simplified-tags"))
    ActionSource = data.get("ActionSource")

    if not ActionSource is None:
      return

    modality = data.get("Modality")
    if modality is None:
      return

    mods = SUPPORTED_MODALITY.split(",")
    mods = [str(s).lower() for s in mods]

    if not str(modality).lower().strip() in mods:
      print(f"Modality {modality} not supported, skipping!")
      remove_series(seriesId)
      return

    print("Stable Series Received, Storing series on disk :" + seriesId)

    dcmpath = os.path.join(TARGET, 'dicom', seriesId)
    os.system(f"mkdir -p {dcmpath}")

    for i, instance in enumerate(instances):
      dicom = orthanc.RestApiGet(f"/instances/{instance}/file")
      with open(os.path.join(dcmpath, f"{instance}.dcm"), "wb") as file:
        file.write(dicom)
      
    urlAddress = f"{os.getenv('SCHEDULER_HOST')}:{os.getenv('SCHEDULER_PORT')}/stable-series"

    data["patientId"] = patientId
    data["studyId"] = studyId
    data["seriesId"] = seriesId
    data["dcmpath"] = f"dicom/{seriesId}"

    headers = {}
    headers["Content-Type"] = "application/json"
    response = requests.post(urlAddress, json=data, headers=headers)
    if response.status_code != 200:
      print(response.reason, flush=True)
  else:
    print('EXIT: No valied DICOM Series for NIFTI Conversion!')


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

orthanc.RegisterOnChangeCallback(OnChange)
