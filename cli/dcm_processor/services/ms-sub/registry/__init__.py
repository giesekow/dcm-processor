import os

def callback(jobName, headers, params, added_params, **kwargs):
  series = []

  for study in headers.get("studies", []):
    for s in study.get("series", []):
      series.append(s)

  count = 0
  seriesId = None
  for s in series:
    tags = s.get("tags", {})
    pps = tags.get("PerformedProcedureStepDescription", "")
    if str(pps).lower().find('mssub') >= 0:
      seriesId = s.get("id")
      count += 1

  injected_params = {
    "storage": {
      "type": "nifti",
      "seriesId": seriesId,
      "permanent": True,
      "path": os.path.join("ms-sub", headers.get("id"), f"{headers.get('id')}_sub.nii.gz")
    },
    "sub_file": os.path.join("ms-sub", headers.get("id"), f"{headers.get('id')}_sub.nii.gz")
  }

  return count > 0, injected_params
