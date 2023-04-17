import os

def callback(jobName, headers, params, added_params, **kwargs):
  injected_params = {}
  has_items = False
  
  if "seriesIds" in headers:
    seriesIds = headers.get("seriesIds", [])
    baseDir = os.path.join("nifti", headers.get("id"))
    injected_params["outputs"] = {}
    for seriesId in seriesIds:

      nifti_params = {
        "type": "nifti",
        "path": os.path.join(baseDir, f"{seriesId}.nii.gz"),
        "base": baseDir,
        "filename": f"{seriesId}",
        "ext": ".nii.gz"
      }

      json_params = {
        "type": "json",
        "path": os.path.join(baseDir, f"{seriesId}.json"),
        "base": baseDir,
        "filename": f"{seriesId}",
        "ext": ".json"
      }
      
      injected_params["outputs"][f"{seriesId}"] = { "nifti": nifti_params, "json": json_params }
      has_items = True

  if not params is None:
    clean = params.get("clean", False)
    if clean and has_items:
      injected_params['deleted'] = [baseDir]

  return True, injected_params