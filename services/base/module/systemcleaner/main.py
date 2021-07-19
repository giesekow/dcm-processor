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
    clean_orthanc(jobName, headers, params, added_params, **kwargs)

def clean_orthanc(jobName, headers, params, added_params, **kwargs):
  ORTHANC_REST_USERNAME = os.getenv('ORTHANC_REST_USERNAME', "anduin")
  ORTHANC_REST_PASSWORD = os.getenv('ORTHANC_REST_PASSWORD', "anduin")
  ORTHANC_REST_URL = os.getenv('ORTHANC_REST_URL', "http://orthanc:8042")

  header = {'content-type': 'application/json'}
  authOrthanc = (ORTHANC_REST_USERNAME, ORTHANC_REST_PASSWORD)
  url = ORTHANC_REST_URL

  seriesIds = headers.get("seriesIds", [])
  for seriesId in seriesIds:
    if not seriesId is None:
      resp = requests.get(f"{url}/series/{seriesId}", auth=authOrthanc, headers=header)
      if resp.status_code == 200:
        studyId = resp.json().get("ParentStudy")
        patientId = None
        resp = requests.get(f"{url}/studies/{studyId}", auth=authOrthanc, headers=header)
        if resp.status_code == 200:
          study = resp.json()
          series = study.get("Series", [])
          for sId in series:
            if str(sId) == str(seriesId):
              try:
                requests.delete(f"{url}/series/{sId}", auth=authOrthanc, headers=header)
              except:
                pass
            else:
              resp = requests.get(f"{url}/series/{sId}", auth=authOrthanc, headers=header)
              if resp.status_code == 200:
                s = resp.json()
                instances = s.get("Instances")
                if len(instances) > 0:
                  instanceId = instances[0]
                  resp = requests.get(f"{url}/instances/{instanceId}", auth=authOrthanc, headers=header)
                  if resp.status_code == 200:
                    inst = resp.json()
                    ref = inst.get("ReferenceSeries")
                    if (not ref is None) and str(ref) == str(seriesId):
                      try:
                        requests.delete(f"{url}/series/{sId}", auth=authOrthanc, headers=header)
                      except:
                        pass

          resp = requests.get(f"{url}/studies/{study.get('ID')}", auth=authOrthanc, headers=header)
          patientId = study.get("ParentPatient")
          if resp.status_code == 200:
            study = resp.json()
            series = study.get("Series")
            if len(series) == 0:
              try:
                requests.delete(f"{url}/studies/{study.get('ID')}", auth=authOrthanc, headers=header)
              except:
                pass

        if not patientId is None:
          resp = requests.get(f"{url}/patients/{patientId}", auth=authOrthanc, headers=header)
          if resp.status_code == 200:
            patient = resp.json()
            studies = patient.get('Studies')
            print("studies", studies, flush=True)

            if len(studies) == 0:
              try:
                requests.delete(f"{url}/patients/{patient.get('ID')}", auth=authOrthanc, headers=header)
              except:
                pass
        else:
          print("Undefined patient ID")