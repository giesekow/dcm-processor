#!/usr/bin/env python3

from __future__ import print_function
import os, argparse, json, dotenv, sys
import inquirer as inq
from ruamel.yaml import YAML
from . import files as FILES
from . import worker as WORKER

GIT_CODE_URL="https://github.com/giesekow/dcm-processor.git"


def parse_args():
  parent_parser = argparse.ArgumentParser(description='A Command line tool for the dicom processor library', add_help=False)
  parent_parser.add_argument('action', metavar='action', type=str, help='action to be performed, options [create, init, install, remove, backup, build]')
  parent_parser.add_argument('object', metavar='object', type=str, help='action object, options [service, app]')
  

  args = parent_parser.parse_args()
  return args

def main():
  args = parse_args()
  action = args.action

  action_lower = str(action).lower()

  if action_lower == "create":
    handle_create(args)
  elif action_lower == "init":
    handle_init(args)
  elif action_lower == "install":
    handle_install(args)
  elif action_lower == "remove":
    handle_remove(args)
  elif action_lower == "backup":
    handle_backup(args)
  elif action_lower == "set":
    handle_set(args)
  elif action_lower == "start":
    handle_start(args)
  elif action_lower == "stop":
    handle_stop(args)
  elif action_lower == "restart":
    handle_restart(args)
  else:
    print("Command not implemented!")

def write_json(data, filename):
  with open(filename, "w") as fp:
    json.dump(data, fp, indent=2)

def read_json(filename):
  with open(filename, "r") as fp:
    return json.load(fp)

  return None

def create_default_config():
  home_dir = os.path.expanduser("~")
  config_path = os.path.join(home_dir, ".dcm-processor", "config.json")
  os.system(f"mkdir -p {os.path.join(home_dir, '.dcm-processor')}")
  config = {
    "apps": {}
  }
  write_json(config, config_path)

def load_config(key=None):
  home_dir = os.path.expanduser("~")
  config_path = os.path.join(home_dir, ".dcm-processor", "config.json")
  config = {}

  if os.path.isfile(config_path):
    config = read_json(config_path)
  else:
    create_default_config()
    config = read_json(config_path)

  data = config

  if not key is None:
    if isinstance(key, str):
      ks = key.split(".")
      for k in ks:
        if not data is None:
          data = data.get(k)

  return data

def update_config(key, data):
  home_dir = os.path.expanduser("~")
  config_path = os.path.join(home_dir, ".dcm-processor", "config.json")
  config = {}

  if os.path.isfile(config_path):
    config = read_json(config_path)
  else:
    create_default_config()
    config = read_json(config_path)

  config[key] = data

  write_json(config, config_path)



def handle_create(args):
  object_lower = str(args.object).lower()
  if object_lower == "service":
    create_service(args)
  if object_lower == "app":
    create_app(args)
  if object_lower == "worker":
    create_worker(args)

def create_app(args):
  questions = [
    inq.Text("app_name", message="Enter app name"),
    inq.Path("app_path", message="Enter app base folder", exists=True, path_type=inq.Path.DIRECTORY, normalize_to_absolute_path=True),
    inq.Path("mapped_path", message="Enter app mapped folder base", exists=False, path_type=inq.Path.DIRECTORY, normalize_to_absolute_path=True),
    inq.Text("dicom_port", message="Enter orthanc DICOM port", default="4242"),
    inq.Text("browser_port", message="Enter orthanc browser port", default="8080"),
    inq.Text("modality", message="Supported Modality (comma separated)", default="CT,MR"),
    inq.List("init_app", message="Initialize app after creation ?", choices=["Yes", "No"]),
  ]
  
  answers = inq.prompt(questions)
  app_path = answers['app_path']
  mapped_path = answers['mapped_path']
  app_name = answers['app_name']
  initapp = answers['init_app']
  dicom_port = answers['dicom_port']
  browser_port = answers['browser_port']
  modality = answers['modality']

  existing_apps = load_config("apps")

  if app_name in existing_apps:
    print(f"There exist a configured app with name '{app_name}'")

  base_path = os.path.abspath(os.path.join(app_path, app_name))
  code_base_path = os.path.join(base_path)

  __initialize_app(base_path=base_path)

  dotenv.set_key(os.path.join(code_base_path, ".env"), "BASEDIR", os.path.abspath(mapped_path))
  dotenv.set_key(os.path.join(code_base_path, ".env"), "ORTHANC_DICOM_PORT", dicom_port)
  dotenv.set_key(os.path.join(code_base_path, ".env"), "ORTHANC_BROWSER_PORT", browser_port)
  dotenv.set_key(os.path.join(code_base_path, ".env"), "SUPPORTED_MODALITY", modality)

  app_config = {
    "name": app_name,
    "base_dir": base_path
  }

  existing_apps[app_name] = app_config
  update_config("apps", existing_apps)

  if initapp == "Yes":
    init_app(args, app_name)

def __initialize_app(base_path):
  code_base_path = os.path.join(base_path)

  os.system(f"mkdir -p {os.path.join(base_path)}")

  initial_files = {
    ".env": FILES.ENV,
    "docker-compose.yml": FILES.DOCKER_COMPOSE,
    "orthanc.json": FILES.ORTHANC,
    "build_volumes.sh": FILES.BUILD_VOLUMES,
    "build.sh": FILES.BUILD,
    "clean.sh": FILES.CLEAN,
    "init.sh": FILES.INIT,
    "rebuild.sh": FILES.REBUILD,
    "run.sh": FILES.RUN,
    "service.sh": FILES.SERVICE,
    "stop.sh": FILES.STOP,
    "settings.json": FILES.SETTINGS
  }

  ## Write initial files.
  for filename in initial_files:
    with open(os.path.join(code_base_path, filename), "w") as file:
      file.write(initial_files[filename])

def create_worker(args):
  questions = [
    inq.Text("worker_name", message="Enter worker name"),
    inq.Path("worker_path", message="Enter workers folder", exists=True, path_type=inq.Path.DIRECTORY, normalize_to_absolute_path=True),
    inq.Text("worker_base_image", message="Enter worker base image", default="ubuntu:18.04"),
    inq.Text("worker_python_version", message="Enter worker python version", default="3.7"),
    inq.Text("channels", message="Enter job channels (comma separated)", default="default"),
    inq.Text("worker_description", message="Enter worker description"),
  ]

  answers = inq.prompt(questions)
  worker_name = answers['worker_name']
  python_version = answers['worker_python_version']
  base_image = answers["worker_base_image"]
  channels = answers["channels"]

  worker_settings = {
    "name": worker_name,
    "scripts": ["script.sh"],
    "entryScriptPaths": ["/scripts"],
    "baseImage": base_image,
    "environments": [
      {
        "name": "base",
        "requirements": ["requirements.txt"],
        "entryRequirementPaths": ["/requirements"],
        "channels": [s.strip() for s in str(channels).strip().split(",")],
        "pythonVersion": python_version
      }
    ]
  }

  fullpath = os.path.join(answers['worker_path'], answers['worker_name'])
  os.system(f"mkdir -p {fullpath}")
  
  os.system(f"touch {os.path.join(fullpath, 'requirements.txt')}")

  files = {
    "settings.json": json.dumps(worker_settings, indent=2),
    "script.sh": "#!/bin/bash"
  }

  for fn in files:
    with open(os.path.join(fullpath, fn), 'w') as txt:
      txt.write(files[fn])

def create_service(args):
  questions = [
    inq.Text("service_name", message="Enter service name"),
    inq.Path("service_path", message="Enter service folder", exists=True, path_type=inq.Path.DIRECTORY, normalize_to_absolute_path=True),
    inq.Text("service_description", message="Enter service description"),
  ]

  answers = inq.prompt(questions)
  service_name = answers['service_name']

  fullpath = os.path.join(answers['service_path'], answers['service_name'])
  modulePath = os.path.join(fullpath, "module")
  registryPath = os.path.join(fullpath, "registry")

  os.system(f"mkdir -p {modulePath}")
  os.system(f"mkdir -p {registryPath}")

  os.system(f"echo 'from .main import callback' > {os.path.join(registryPath, '__init__.py')}")

  os.system(f"echo 'from .main import worker' > {os.path.join(modulePath, '__init__.py')}")
  os.system(f"touch {os.path.join(modulePath, 'requirements.txt')}")
  os.system(f"touch {os.path.join(modulePath, 'script.sh')}")

  callback_code = [
    '\n',
    'def callback(jobName, headers, params, added_params, **kwargs):\n',
    '\tinjected_params = {"custom-data": "Some new data"}\n',
    '\n',
    '\t# Check header information etc. to see if you have to execute job\n'
    '\t# If Yes return True with the additional injected params\n'
    '\t# If No return False with additional injected params\n'
    '\n'
    '\treturn True, injected_params'
  ]
  worker_code = [
    'import os\n',
    '\n',
    'DATA = os.getenv("DATA")\n',
    'LOGS = os.getenv("LOGS")\n',
    'MODULES = os.getenv("MODULE")\n',
    '\n',
    'def worker(jobName, headers, params, added_params, **kwargs):\n',
    '\tprint(f"{jobName} can be handled here")\n',
    '\tprint(f"I can log info into the {LOGS} folder")\n',
    '\tprint(f"I can write and read from the {DATA} folder")\n',
    '\tprint(f"I can access other service modules from the {MODULES} folder")\n'
  ]
  settings = [
    {
      "jobName": service_name,
      "worker": f"{service_name}.worker",
      "callback": f"{service_name}.callback",
      "dependsOn": None,
      "channel": "default",
      "timeout": "1h",
      "params": {},
      "sortPosition": 0,
      "description": answers['service_description']
    }
  ]

  with open(os.path.join(registryPath, 'main.py'), 'w') as txt:
    txt.writelines(callback_code)

  with open(os.path.join(registryPath, 'settings.json'), 'w') as txt:
    json.dump(settings, txt, indent=2)

  with open(os.path.join(modulePath, 'main.py'), 'w') as txt:
    txt.writelines(worker_code)



def handle_init(args):
  object_lower = str(args.object).lower()
  if object_lower == "app":
    init_app(args)

def init_app(args, app_name=None):
  existing_apps = load_config("apps")

  if len(existing_apps.keys()) == 0:
    print("There are no existing apps")
    return

  if app_name is None:
    questions = [
      inq.List("app_name", message="Select app to initial", choices=list(existing_apps.keys())),
    ]

    answers = inq.prompt(questions)
    app_name = answers['app_name']

  config = existing_apps.get(app_name)

  if config is None:
    print("Unable to load app configuration!")
    return

  base_dir = config.get("base_dir")
    
  if base_dir is None:
    print("Error in configuration filename")
    return

  build_script = os.path.join(base_dir, "build.sh")
  build_volumes_script = os.path.join(base_dir, "build_volumes.sh")
  run_script = os.path.join(base_dir, "run.sh")
  init_script = os.path.join(base_dir, "init.sh")
  stop_script = os.path.join(base_dir, "stop.sh")

  if not os.path.isfile(build_script):
    print("Missing build script!")
    return

  if not os.path.isfile(build_volumes_script):
    print("Missing build_volumes script!")
    return

  if not os.path.isfile(run_script):
    print("Missing run script!")
    return

  if not os.path.isfile(init_script):
    print("Missing init script!")
    return

  if not os.path.isfile(stop_script):
    print("Missing stop script!")
    return

  
  proxies = load_config("proxies")
  if not proxies is None:
    # Patch build script
    code_lines = ["#!/bin/bash\n","\n", "docker-compose build"] + [f" --build-arg {k}={proxies[k]}" for k in proxies.keys()] + [" --force-rm\n"] + ["docker-compose pull\n"]
    with open(build_script, "w") as sc:
      sc.writelines(code_lines)

  cwd = os.getcwd()

  cli_dir = os.path.dirname(os.path.realpath(__file__))
  cli_services = os.path.join(cli_dir, "services")
  print("copying base services....")
  os.system(f"cp -r {cli_services} {os.path.join(base_dir, 'services')}")

  os.chdir(os.path.join(base_dir))
  os.system(f"bash build_volumes.sh && bash build.sh && bash run.sh && bash stop.sh && bash init.sh")
  os.chdir(os.path.join(cwd))

  os.system(f"rm -rf {os.path.join(base_dir, 'services')}")



def handle_install(args):
  object_lower = str(args.object).lower()
  if object_lower == "service":
    install_service(args)
  if object_lower == "worker":
    install_worker(args)

def install_service(args):
  existing_apps = load_config("apps")
  if len(existing_apps.keys()) == 0:
    print("There are no existing apps")
    return

  questions = [
    inq.List("app_name", message="Select app to install service to", choices=list(existing_apps.keys())),
    inq.Text("service_name", message="Enter service name"),
    inq.Path("service_path", message="Enter service folder", exists=True, path_type=inq.Path.DIRECTORY, normalize_to_absolute_path=True),
  ]

  answers = inq.prompt(questions)
  app_name = answers['app_name']
  service_name = answers['service_name']
  service_path = answers['service_path']

  config = existing_apps.get(app_name)

  if config is None:
    print("Unable to load app configuration!")
    return

  base_dir = config.get("base_dir")
    
  if base_dir is None:
    print("Error in configuration filename")
    return

  service_script = os.path.join(base_dir, "service.sh")

  if not os.path.isfile(service_script):
    print("Missing build script!")
    return

  service_dir = os.path.abspath(service_path)

  cwd = os.getcwd()

  os.chdir(os.path.abspath(os.path.join(base_dir)))
  os.system(f"bash service.sh install {service_name} -p {service_dir}")
  os.chdir(cwd)

def install_worker(args):
  existing_apps = load_config("apps")
  if len(existing_apps.keys()) == 0:
    print("There are no existing apps")
    return

  questions = [
    inq.List("app_name", message="Select app to install worker to", choices=list(existing_apps.keys())),
    inq.Text("worker_name", message="Enter worker name"),
    inq.Path("worker_path", message="Enter worker folder", exists=True, path_type=inq.Path.DIRECTORY, normalize_to_absolute_path=True),
    inq.List("start_worker", message="Start worker after installation ?", choices=["Yes", "No"], default="No"),
    inq.List("config_gpu", message="Configure GPU device reservation ?", choices=["Yes", "No"], default="No"),
  ]

  answers = inq.prompt(questions)
  app_name = answers['app_name']
  worker_name = answers['worker_name']
  worker_path = answers['worker_path']
  config_gpu = answers['config_gpu']
  start_worker_after_install = answers['start_worker']
  device_config = {}

  if config_gpu == "Yes":
    device_answers = inq.prompt([
      inq.Text("device_cap", message="Enter device capabilities (comman separated list)", default="gpu"),
      inq.Text("driver", message="Enter device driver", default="nvidia"),
      inq.List("is_deviceid_or_count", message="How would you want to configure the reservation ?", choices=["Device Count", "Device ID"], default="Device Count"),
    ])

    caps = device_answers["device_cap"]
    driv = device_answers["driver"]
    is_dev_or_count = device_answers['is_deviceid_or_count']

    caps = str(caps).split(",")

    if len(caps) > 0:
      device_config["capabilities"] = caps

    if driv != "":
      device_config["driver"] = driv  

    if is_dev_or_count == "Device Count":
      count_answers = inq.prompt([
        inq.Text("count", message="Enter Device Count (integer) leave empty to use all devices"),
        inq.Text("device_options", message="Enter driver specific options (comma seperated key:value pairs)"),
      ])

      cnt = count_answers["count"]
      opts = count_answers["device_options"]

      if cnt != "":
        device_config["count"] = int(cnt)
      else:
        device_config["count"] = "all"
        
      if opts != "":
        opts = str(opts).split(",")         
        for opt in opts:
          keyval = opt.split(":")
          if len(keyval) > 1:

            if not "options" in device_config:
              device_config["options"] = {}
            
            device_config[keyval[0]] = keyval[1]

    else:
      deviceid_answers = inq.prompt([
        inq.Text("deviceids", message="Enter Device IDs (comman separated list)"),
        inq.Text("device_options", message="Enter driver specific options (comma seperated key:value pairs)"),
      ])

      devids = deviceid_answers["deviceids"]
      opts = deviceid_answers["device_options"]

      if devids != "":
        device_config["device_ids"] = str(devids).split(",")
        
      if opts != "":
        opts = str(opts).split(",")         
        for opt in opts:
          keyval = opt.split(":")
          if len(keyval) > 1:

            if not "options" in device_config:
              device_config["options"] = {}
            
            device_config[keyval[0]] = keyval[1]

  worker_name = str(worker_name).lower()

  if worker_name == "worker":
    print("Worker name cannot be 'worker'")
    return

  config = existing_apps.get(app_name)

  if config is None:
    print("Unable to load app configuration!")
    return

  existing_workers = config.get("workers")

  if existing_workers is None:
    existing_workers = {}

  if worker_name in existing_workers:
    print(f"Worker with name {worker_name} already exist remove worker first!")
    return

  base_dir = config.get("base_dir")

  workers_dir = os.path.join(base_dir, "workers")

  os.system(f"mkdir -p {workers_dir}")

  # check required files
  settingsfile = os.path.join(worker_path, "settings.json")

  if not os.path.isfile(settingsfile):
    print("Worker missing settings.json!")
    return
  
  worker_settings = {}

  with open(settingsfile) as jsonFile:
    worker_settings = json.load(jsonFile)

  worker_base_dir = os.path.join(workers_dir, worker_name)

  __initialize_worker(base_path=worker_base_dir, settings=worker_settings)

  os.system(f"cp -r {os.path.join(worker_path)} {os.path.join(workers_dir, worker_name, 'settings')}")

  docker_compose_config = {
    'build': f"./workers/{worker_name}",
    'depends_on': ['mongo'],
    'environment': {
      'JOBS_CONNECTION': '${JOBS_CONNECTION}',
      'JOBS_DBNAME': '${JOBS_DBNAME}',
      'JOBS_COLNAME': '${JOBS_COLNAME}',
      'ORTHANC_REST_USERNAME': '${ORTHANC_REST_USERNAME}',
      'ORTHANC_REST_PASSWORD': '${ORTHANC_REST_PASSWORD}',
      'ORTHANC_REST_URL': '${ORTHANC_REST_URL}',
      'ORTHANC_DEFUALT_STORE': '${ORTHANC_DEFUALT_STORE}',
      'DATA': '/data',
      'MODULES': '/modules',
      'LOGS': '/logs'
    },
    'volumes': [
      '${BASEDIR}${MODULES}:/modules:cached',
      '${BASEDIR}${DATA}:/data:rw',
      '${BASEDIR}${LOGS}:/logs:rw'
    ]
  }

  if "image" in worker_settings:
    img = worker_settings.get("image")

    if not img is None:
      del docker_compose_config["build"]
      docker_compose_config["image"] = img

  if config_gpu == "Yes" and "capabilities" in device_config:
    docker_compose_config["deploy"] = {
      "resources": {
        "reservations": {
          "devices": [device_config]
        }
      }
    }

  yaml = YAML(typ="safe", pure=True)
  yaml.default_flow_style = False
  data = {}
  with open(os.path.join(base_dir, "docker-compose.yml"), 'r') as f: 
    data = yaml.load(f)
  
  with open(os.path.join(base_dir, "docker-compose.yml"), 'w') as f: 
    data["services"][str(worker_name)] = docker_compose_config
    yaml.dump(data, f)

  existing_workers[worker_name] = {
    "base_dir": worker_name,
  }

  config["workers"] = existing_workers
  existing_apps[app_name] = config
  update_config("apps", existing_apps)
  print(f"Worker successfully install as {worker_name}")

  cwd = os.getcwd()
  os.chdir(os.path.join(base_dir))

  if "build" in worker_settings:
    os.system(f"docker-compose build --force-rm {worker_name}")

    del docker_compose_config["build"]
    docker_compose_config["image"] = f"{base_dir}_{worker_name}"

    data = {}
    with open(os.path.join(base_dir, "docker-compose.yml"), 'r') as f: 
      data = yaml.load(f)
    
    with open(os.path.join(base_dir, "docker-compose.yml"), 'w') as f: 
      data["services"][str(worker_name)] = docker_compose_config
      yaml.dump(data, f)

    os.system(f"rm -rf {os.path.join(worker_base_dir)}")

  if start_worker_after_install == "Yes":
    os.system(f"docker-compose up -d {worker_name}")

  os.chdir(cwd)

def __initialize_worker(base_path, settings):
  code_base_path = os.path.join(base_path)

  os.system(f"mkdir -p {os.path.join(base_path)}")

  if "image" in settings:
    img = settings.get("image")
    if not img is None:
      return

  base_image = settings.get("baseImage", "ubuntu:18.04")

  initial_files = {
    "Dockerfile": WORKER.DOCKERFILE.replace("BASE_IMAGE", base_image),
    "entrypoint.sh": WORKER.ENTRYPOINT,
    "envs.py": WORKER.ENVS,
    "install.py": WORKER.INSTALL,
    "start.py": WORKER.START
  }

  ## Write initial files.
  for filename in initial_files:
    with open(os.path.join(code_base_path, filename), "w") as file:
      file.write(initial_files[filename])

def handle_remove(args):
  object_lower = str(args.object).lower()
  if object_lower == "service":
    remove_service(args)
  if object_lower == "app":
    remove_app(args)
  if object_lower == "worker":
    remove_worker(args)

def remove_app(args):
  existing_apps = load_config("apps")

  if len(existing_apps.keys()) == 0:
    print("There are no existing apps")
    return

  questions = [
    inq.List("app_name", message="Select app to remove", choices=list(existing_apps.keys())),
    inq.List("remove_base_dir", message="Remove app base directory ?", choices=["Yes", "No"]),
    inq.List("remove_mapped_dir", message="Remove app mapped folders directory ?", choices=["Yes", "No"]),
    inq.Text("backup_path", message="Enter backup folder (leave empty to skip backup)")
  ]

  answers = inq.prompt(questions)
  app_name = answers['app_name']
  backup_path = answers['backup_path']
  remove_base = answers['remove_base_dir']
  remove_mapped = answers['remove_mapped_dir']

  config = existing_apps.get(app_name)

  if config is None:
    print("Unable to load app configuration!")
    return

  base_dir = config.get("base_dir")

  del existing_apps[app_name]
  update_config("apps", existing_apps)
    
  if base_dir is None:
    print("Error in configuration filename")
    return

  clean_script = os.path.join(base_dir, "clean.sh")

  if not os.path.isfile(clean_script):
    print("Missing clean script!")
    return

  env_file = os.path.join(base_dir, ".env")
  if not os.path.isfile(env_file):
    print("Missing .env file!")
    return

  dotenv.load_dotenv(os.path.abspath(os.path.join(base_dir, '.env')))
  mapped_folder = os.environ.get("BASEDIR")

  if backup_path != "":
    backup_dir = os.path.abspath(backup_path)
    os.system(f"mkdir -p {backup_dir}")
    os.system(f"cp -r {os.path.abspath(os.path.join(base_dir))} {os.path.join(backup_dir, app_name)}")

    if not mapped_folder is None:
      os.system(f"cp -r {os.path.abspath(mapped_folder)} {os.path.join(backup_dir, app_name, 'mapped_folder')}")

  cwd = os.getcwd()

  os.chdir(os.path.abspath(os.path.join(base_dir)))
  os.system(f"bash clean.sh")
  os.chdir(cwd)

  if remove_base == "Yes":
    os.system(f"rm -rf {os.path.abspath(os.path.join(base_dir))}")
  
  if remove_mapped == "Yes":
    os.system(f"rm -rf {os.path.abspath(os.path.join(mapped_folder))}")

def remove_service(args):
  existing_apps = load_config("apps")
  if len(existing_apps.keys()) == 0:
    print("There are no existing apps")
    return

  questions = [
    inq.List("app_name", message="Select app to remove service from", choices=list(existing_apps.keys())),
    inq.Text("service_name", message="Enter service name"),
    inq.Text("backup_path", message="Enter backup folder (leave empty to skip backup)")
  ]

  answers = inq.prompt(questions)
  app_name = answers['app_name']
  service_name = answers['service_name']
  service_path = answers['backup_path']

  config = existing_apps.get(app_name)

  if config is None:
    print("Unable to load app configuration!")
    return

  base_dir = config.get("base_dir")
    
  if base_dir is None:
    print("Error in configuration filename")
    return

  service_script = os.path.join(base_dir, "service.sh")

  if not os.path.isfile(service_script):
    print("Missing service script!")
    return

  

  cwd = os.getcwd()
  os.chdir(os.path.abspath(os.path.join(base_dir)))

  if service_path != "":
    service_dir = os.path.abspath(service_path)
    os.system(f"bash service.sh remove {service_name} -b {service_dir}")
  else:
    os.system(f"bash service.sh remove {service_name}")

  os.chdir(cwd)

def remove_worker(args):
  existing_apps = load_config("apps")
  if len(existing_apps.keys()) == 0:
    print("There are no existing apps")
    return

  questions = [
    inq.List("app_name", message="Select app to remove worker from", choices=list(existing_apps.keys())),
    inq.Text("worker_name", message="Enter worker name")
  ]

  answers = inq.prompt(questions)
  app_name = answers['app_name']
  worker_name = answers['worker_name']
  worker_name = str(worker_name).lower()

  config = existing_apps.get(app_name)

  if config is None:
    print("Unable to load app configuration!")
    return

  base_dir = config.get("base_dir")
    
  if base_dir is None:
    print("Error in configuration filename")
    return

  existing_workers = config.get("workers")
  if not worker_name in existing_workers:
    print(f"Worker with name {worker_name} does not exist!")
    return


  cwd = os.getcwd()
  os.chdir(os.path.join(base_dir))
  os.system(f"docker-compose rm -f -s {worker_name}")
  os.system(f"docker rmi {base_dir}_{worker_name}")
  os.chdir(cwd)


  yaml = YAML(typ="safe", pure=True)
  yaml.default_flow_style = False
  data = {}
  with open(os.path.join(base_dir, "docker-compose.yml"), 'r') as f: 
    data = yaml.load(f)
  
  with open(os.path.join(base_dir, "docker-compose.yml"), 'w') as f: 
    del data["services"][worker_name]
    yaml.dump(data, f)

  del existing_workers[worker_name]
  config["workers"] = existing_workers
  existing_apps[app_name] = config
  update_config("apps", existing_apps)

  print(f"Worker successfully removed!")



def handle_backup(args):
  object_lower = str(args.object).lower()
  if object_lower == "service":
    backup_service(args)
  if object_lower == "app":
    backup_app(args)

def backup_service(args):
  existing_apps = load_config("apps")

  if len(existing_apps.keys()) == 0:
    print("There are no existing apps")
    return

  questions = [
    inq.List("app_name", message="Select app to backup service", choices=list(existing_apps.keys())),
    inq.Text("service_name", message="Enter service name"),
    inq.Text("backup_path", message="Enter backup folder")
  ]

  answers = inq.prompt(questions)
  app_name = answers['app_name']
  service_name = answers['service_name']
  service_path = answers['backup_path']

  config = existing_apps.get(app_name)

  if config is None:
    print("Unable to load app configuration!")
    return

  base_dir = config.get("base_dir")
    
  if base_dir is None:
    print("Error in configuration filename")
    return

  service_script = os.path.join(base_dir, "service.sh")

  if not os.path.isfile(service_script):
    print("Missing service script!")
    return

  if service_path != "":
    service_dir = os.path.abspath(service_path)
    cwd = os.getcwd()
    os.chdir(os.path.abspath(os.path.join(base_dir)))
    os.system(f"bash service.sh backup {service_name} -b {service_dir}")
    os.chdir(cwd)
  else:
    print("Backup path not provided!")
    return

def backup_worker(args):
  existing_apps = load_config("apps")

  if len(existing_apps.keys()) == 0:
    print("There are no existing apps")
    return

  questions = [
    inq.List("app_name", message="Select app to backup worker", choices=list(existing_apps.keys())),
    inq.Text("worker_name", message="Enter worker name"),
    inq.Text("backup_path", message="Enter backup folder")
  ]

  answers = inq.prompt(questions)
  app_name = answers['app_name']
  worker_name = answers['worker_name']
  backup_path = answers['backup_path']

  worker_name = str(worker_name).lower()

  config = existing_apps.get(app_name)

  if config is None:
    print("Unable to load app configuration!")
    return

  base_dir = config.get("base_dir")
    
  if base_dir is None:
    print("Error in configuration filename")
    return

  existing_workers = config.get("workers")

  if not worker_name in existing_workers:
    print(f"Worker with name {worker_name} does not exist!")
    return

  worker_dir = existing_workers[worker_name]["base_dir"]

  backup_path_full = os.path.abspath(os.path.join(backup_path, worker_name))

  os.system(f"cp -r {os.path.join(base_dir, 'workers', worker_dir)} {backup_path_full}")

  yaml = YAML(typ="safe", pure=True)
  yaml.default_flow_style = False
  data = {}

  with open(os.path.join(base_dir, "docker-compose.yml"), 'r') as f: 
    data = yaml.load(f)

  try:
    docker_config = data["services"][worker_name]
    write_json(docker_config, os.path.join(backup_path_full, "docker-compose.json"))
  except Exception as e:
    print(e)
    

  print("Worker successfully backed up!")

def backup_app(args):
  existing_apps = load_config("apps")

  if len(existing_apps.keys()) == 0:
    print("There are no existing apps")
    return

  questions = [
    inq.List("app_name", message="Select app to backup", choices=list(existing_apps.keys())),
    inq.Text("backup_path", message="Enter backup folder")
  ]

  answers = inq.prompt(questions)
  app_name = answers['app_name']
  backup_path = answers['backup_path']

  config = existing_apps.get(app_name)

  if config is None:
    print("Unable to load app configuration!")
    return

  base_dir = config.get("base_dir")
    
  if base_dir is None:
    print("Error in configuration filename")
    return

  env_file = os.path.join(base_dir, ".env")
  if not os.path.isfile(env_file):
    print("Missing .env file!")
    return

  dotenv.load_dotenv(os.path.abspath(os.path.join(base_dir, '.env')))
  mapped_folder = os.environ.get("BASEDIR")

  if backup_path != "":
    backup_dir = os.path.abspath(backup_path)
    os.system(f"mkdir -p {backup_dir}")
    os.system(f"cp -r {os.path.abspath(os.path.join(base_dir))} {os.path.join(backup_dir, app_name)}")

    if not mapped_folder is None:
      os.system(f"cp -r {os.path.abspath(mapped_folder)} {os.path.join(backup_dir, app_name, 'mapped_folder')}")



def handle_start(args):
  object_lower = str(args.object).lower()
  if object_lower == "app":
    start_app(args)

def start_app(args, app_name=None):
  existing_apps = load_config("apps")

  if len(existing_apps.keys()) == 0:
    print("There are no existing apps")
    return

  if app_name is None:
    questions = [
      inq.List("app_name", message="Select app to start", choices=list(existing_apps.keys())),
    ]

    answers = inq.prompt(questions)
    app_name = answers['app_name']

  config = existing_apps.get(app_name)

  if config is None:
    print("Unable to load app configuration!")
    return

  base_dir = config.get("base_dir")
    
  if base_dir is None:
    print("Error in configuration filename")
    return

  run_script = os.path.join(base_dir, "run.sh")

  if not os.path.isfile(run_script):
    print("Missing run script!")
    return

  cwd = os.getcwd()

  os.chdir(os.path.join(base_dir))
  os.system(f"bash run.sh")
  os.chdir(os.path.join(cwd))



def handle_stop(args):
  object_lower = str(args.object).lower()
  if object_lower == "app":
    stop_app(args)

def stop_app(args, app_name=None):
  existing_apps = load_config("apps")

  if len(existing_apps.keys()) == 0:
    print("There are no existing apps")
    return

  if app_name is None:
    questions = [
      inq.List("app_name", message="Select app to start", choices=list(existing_apps.keys())),
    ]

    answers = inq.prompt(questions)
    app_name = answers['app_name']

  config = existing_apps.get(app_name)

  if config is None:
    print("Unable to load app configuration!")
    return

  base_dir = config.get("base_dir")
    
  if base_dir is None:
    print("Error in configuration filename")
    return

  stop_script = os.path.join(base_dir, "stop.sh")

  if not os.path.isfile(stop_script):
    print("Missing stop script!")
    return

  cwd = os.getcwd()

  os.chdir(os.path.join(base_dir))
  os.system(f"bash stop.sh")
  os.chdir(os.path.join(cwd))




def handle_restart(args):
  object_lower = str(args.object).lower()
  if object_lower == "app":
    restart_app(args)

def restart_app(args, app_name=None):
  existing_apps = load_config("apps")

  if len(existing_apps.keys()) == 0:
    print("There are no existing apps")
    return

  if app_name is None:
    questions = [
      inq.List("app_name", message="Select app to start", choices=list(existing_apps.keys())),
    ]

    answers = inq.prompt(questions)
    app_name = answers['app_name']

  config = existing_apps.get(app_name)

  if config is None:
    print("Unable to load app configuration!")
    return

  base_dir = config.get("base_dir")
    
  if base_dir is None:
    print("Error in configuration filename")
    return

  run_script = os.path.join(base_dir, "run.sh")

  if not os.path.isfile(run_script):
    print("Missing run script!")
    return

  cwd = os.getcwd()

  os.chdir(os.path.join(base_dir))
  os.system(f"bash run.sh")
  os.chdir(os.path.join(cwd))




def handle_set(args):
  object_lower = str(args.object).lower()
  if object_lower == "proxy":
    set_proxy(args)
  
def set_proxy(args):
  questions = [
    inq.Text("http_proxy", message="Enter http proxy"),
    inq.Text("https_proxy", message="Enter https proxy"),
    inq.Text("ftp_proxy", message="Enter ftp proxy"),
    inq.Text("no_proxy", message="Enter no proxy urls (comma separated)"),
  ]

  answers = inq.prompt(questions)
  
  p_settings = {
    "http_proxy": answers["http_proxy"],
    "https_proxy": answers["https_proxy"],
    "ftp_proxy": answers["ftp_proxy"],
    "no_proxy": answers["no_proxy"],
  }

  update_config("proxies", p_settings)
  print("Proxy settings updated!")
  
def set_trusted_hosts(args):
  questions = [
    inq.Text("trusted_hosts", message="Enter pip trusted hosts"),
  ]

  answers = inq.prompt(questions)
  
  th = answers["trusted_hosts"]
  th = str(th).split(",")
  
  update_config("trusted_hosts", th)
  print("Trusted hosts updated!")


if __name__ == "__main__":
  main()