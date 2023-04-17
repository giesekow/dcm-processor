import os

def dicomAnonymizer(jobName, headers, params, added_params, **kwargs):
  injected_params = {}

  if "id" in headers:
    patientId = headers.get("id")
    injected_params["deleted"] = [os.path.join("dicom", patientId)]
  
  return True, injected_params
  
def systemcleaner(jobName, headers, params, added_params, **kwargs):
  return True, {}

def storageManager(jobName, headers, params, added_params, **kwargs):
  return True, {}
