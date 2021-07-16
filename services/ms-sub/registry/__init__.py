import os

def callback(jobName, headers, params, added_params, **kwargs):
  series = []
  for study in headers.get("studies", []):
    for s in study.get("series", []):
      series.append(s)

  count = 0
  for s in series:
    tags = s.get("tags", {})
    pps = tags.get("PerformedProcedureStepDescription", "")
    if str(pps).find('mssub') >= 0:
      count += 1

  return count > 0, {}
