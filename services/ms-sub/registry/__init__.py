import os

def callback(jobName, headers, params, added_params, **kwargs):
  pps = headers.get("PerformedProcedureStepDescription", "")
  return str(pps).find('mssub') >= 0, {}
