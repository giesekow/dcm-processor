import os

def callback(jobName, headers, params, added_params, **kwargs):
  injected_params = {}
  
  if "seriesIds" in headers:
    seriesIds = headers.get("seriesIds", [])
    baseDir = os.path.join("nifti", headers.get("id"))
    injected_params["conversions"] = {}
    for seriesId in seriesIds:
      out_params = {
        "output": os.path.join(baseDir, f"{seriesId}.nii.gz"),
        "base": baseDir,
        "filename": f"{seriesId}",
        "ext": ".nii.gz"
      }
      injected_params["conversions"][f"{seriesId}"] = out_params

    # Add files to be stored into pacs
    '''
    injected_params["storage"] = {
      "path": os.path.join("nifti", f"{seriesId}.nii.gz"),
      "type": "nifti",
      "destination": "pac",
      "tags": {"Series Description": "Exported With dcm2nii"}
    }
    '''
    # Add files to be deleted
    # injected_params["deleted"] = ["nifti"]

  return True, injected_params