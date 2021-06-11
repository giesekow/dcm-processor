import os, shutil, requests

DATA = os.getenv('DATA', '/data')
CLEAN_ORTHANC = os.getenv('CLEAN_ORTHANC', 0)

def worker(jobName, headers, params, added_params, **kwargs):
  try:
    for j in list(added_params.values()):
      if "deleted" in j:
        tmp = j["deleted"]
        fns = []

        if isinstance(tmp, list) or isinstance(tmp, tuple):
          fns = tmp
        elif isinstance(tmp, str):
          fns = [tmp]

        for fn in fns:
          try:
            ffn = os.path.join(DATA, fn)
            if os.path.exists(ffn):
              if os.path.isfile(ffn):
                os.remove(os.path.join(DATA, fn))
              elif os.path.isdir(ffn):
                shutil.rmtree(ffn)
          except:
            pass
  except:
    pass
  
  if int(CLEAN_ORTHANC) != 0:
    print("Cleaning Orthanc", flush=True)
    clean_orthanc(jobName, headers, params, added_params, **kwargs)

def clean_orthanc(jobName, headers, params, added_params, **kwargs):
  ORTHANC_REST_USERNAME = os.getenv('ORTHANC_REST_USERNAME', "anduin")
  ORTHANC_REST_PASSWORD = os.getenv('ORTHANC_REST_PASSWORD', "anduin")
  ORTHANC_REST_URL = os.getenv('ORTHANC_REST_URL', "http://orthanc:8042")

  header = {'content-type': 'application/json'}
  authOrthanc = (ORTHANC_REST_USERNAME, ORTHANC_REST_PASSWORD)
  url = ORTHANC_REST_URL

  seriesId = headers.get("seriesId")
  # Get Series Parent Patient
  if not seriesId is None:
    resp = requests.get(f"{url}/series/${seriesId}", auth=authOrthanc, headers=header)
    if resp.status_code == 200:
      studyId = resp.json()["ParentStudy"]
      resp = requests.delete(f"{url}/series/${seriesId}", auth=authOrthanc, headers=header)
      if resp.status_code == 200:
        resp = requests.get(f"{url}/studies/${studyId}", auth=authOrthanc, headers=header)
        if resp.status_code == 200:
          resp_data = resp.json()
          series = resp_data["Series"]
          if len(series) == 0:
            patientId = resp_data["ParentPatient"]
            resp = requests.delete(f"{url}/studies/${studyId}", auth=authOrthanc, headers=header)
            if resp.status_code == 200:
              resp = requests.get(f"{url}/patients/${patientId}", auth=authOrthanc, headers=header)
              if resp.status_code == 200:
                resp_data = resp.json()
                studies = resp_data["Studies"]
                if len(studies) == 0:
                  resp = requests.delete(f"{url}/patients/${patientId}", auth=authOrthanc, headers=header)
