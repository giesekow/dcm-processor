import requests
import json
import time
import sys
from datetime import datetime

def get_config(params = None):
  config_dict = None

  if isinstance(params, dict):
    config_dict = params.get("fhir")

  return config_dict

def get_new_token(auth_server_url, client_id, client_secret):
  token_req_payload = {'grant_type': 'client_credentials'}
  token_response = requests.post(auth_server_url,data=token_req_payload, verify=False, allow_redirects=False,auth=(client_id, client_secret))
  time.sleep(1)
  if token_response.status_code !=200:
    print("Failed to obtain token from the OAuth 2.0 server", file=sys.stderr)
    return None
  else:
    tokens = json.loads(token_response.text)
    token = tokens['access_token']
    return token
    
def get_pseudononymized_bundle(auth_server_url, client_id, client_secret, interface_url, bundle):
  token = get_new_token(auth_server_url, client_id, client_secret)
  api_call_headers = {'Authorization': 'Bearer ' + token, 'Content-Type':'application/json'}
  response = requests.post(interface_url,headers=api_call_headers,data=json.dumps(bundle))
  time.sleep(2)
  if response.status_code !=401:
    token = get_new_token(auth_server_url, client_id, client_secret)
    response = requests.post(interface_url,headers=api_call_headers,data=json.dumps(bundle))
    time.sleep(5)
  if response.status_code ==200:
    pse_bundle = json.loads(response.text)
    return pse_bundle
  else:
    print('PSE server not responsive')
    raise Exception("Server Not reponding")
        
def get_pseudonyms_from_bundle(pse_bundle):
  pse_dict = None
  entries = pse_bundle.get("entry",None)
  if entries is not None:
    for entry in entries:
      if  entry['resource']['resourceType'] == 'Patient':
        pse_dict = entry['resource']['identifier'][0]['value']
  return pse_dict

def create_fhir_entry(resourceType, system, ID):
  entry = {
    "resource": {
      "resourceType": resourceType,
      "identifier": [
        {
          "use": "official",
          "system": system,
          "value": ID,
          "period": {
            "start": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+01:00"),
            "end": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+01:00")
          }
        }
      ]
    }
  }
  return entry

def create_fhir_bundle(entries):
  bundle = {
    "resourceType": "Bundle",
    "entry": entries
  }
  return bundle

# pat_entry = create_fhir_entry("Patient", identifier_system, 123456)
# accN_entry = create_fhir_entry("ImagingStudy", identifier_system, 123456789)
# bundle = create_fhir_bundle([pat_entry,accN_entry])

def get_fhir_pseudonym(ptid, params):
  config_dict = get_config(params)
  
  if config_dict is None:
    return None
  
  interface_url = config_dict.get('interface_url')
  auth_server_url = config_dict.get('auth_server_url')
  client_id = config_dict.get('client_id')
  client_secret = config_dict.get('client_secret')
  identifier_system = config_dict.get('identifier_system')

  if (interface_url is None) or (auth_server_url is None) or (client_id is None) or (client_secret) or (identifier_system is None):
    return None
  
  pat_entry = create_fhir_entry("Patient", identifier_system, ptid)
  
  bundle = create_fhir_bundle([pat_entry,])
  
  try:
    pse_bundle = get_pseudononymized_bundle(auth_server_url, client_id, client_secret, interface_url, bundle)
    pse_dict = get_pseudonyms_from_bundle(pse_bundle)
    return pse_dict
  except Exception as e:
    return None