def dicomAnonymizer(jobName, headers, params, added_params, **kwargs):
  injected_params = {}

  if "seriesId" in headers:
    seriesId = headers.get("seriesId")
    injected_params["deleted"] = [f"dicom/{seriesId}"]
  
  return True, injected_params
  
def systemcleaner(jobName, headers, params, added_params, **kwargs):
  return True, {}

def storageManager(jobName, headers, params, added_params, **kwargs):
  return True, {}
