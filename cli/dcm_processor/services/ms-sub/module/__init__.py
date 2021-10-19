import os
from .sub import get_dicoms, process
import pydicom
DATA = os.getenv("DATA")
dir_path = os.path.dirname(os.path.realpath(__file__))

def worker(jobName, headers, params, added_params, **kwargs):
  
  if (not DATA is None):
    dcmpath = os.path.join(DATA,headers.get("dcmpath"))
    series = headers.get("seriesIds", [])

    sel_series = []
    for s in series:
      pth = os.path.join(dcmpath, s)
      files = get_dicoms(pth)
      if len(files) > 0:
        ds = pydicom.dcmread(files[0])
        studydate = ds.StudyDate
        pps = ds.PerformedProcedureStepDescription
        if str(pps).lower().find("mssub") >= 0:
          sel_series.append({"seriesId": s, "studyDate": int(studydate)})

    sel_series = sorted(sel_series, key=lambda x: x.get("studyDate"))

    if len(sel_series) >= 2:
      pre_series = sel_series[0].get("seriesId")
      post_series = sel_series[1].get("seriesId")
      conversions = added_params.get("dcm2nii", {}).get("conversions", {})
      sub_file = added_params.get(jobName, {}).get("sub_file")
      pre_path = None
      post_path = None

      if str(pre_series) in conversions:
        pre_path = os.path.join(DATA, conversions.get(str(pre_series), {}).get("output"))

      if str(post_series) in conversions:
        post_path = os.path.join(DATA, conversions.get(str(post_series), {}).get("output"))
      
      if (not pre_path is None) and (not post_path is None):
        patient_folder = os.path.join(DATA, 'ms-sub', headers.get("id"))
        
        if not os.path.isdir(patient_folder):
          os.makedirs(patient_folder)

        process(pre_path, post_path, patient_folder, sub_file)