DOCKERFILE = """
FROM BASE_IMAGE

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Berlin

WORKDIR /app


# Copy script files
COPY entrypoint.sh ./
COPY install.py ./
COPY start.py ./
COPY envs.py ./

RUN mkdir -p /settings
RUN mkdir -p /environments

COPY ./settings/. /settings/.

# Install all required dependencies

RUN apt-get update && \
    apt-get install -y software-properties-common tzdata git && \
    apt-get update -y && \
    apt-get install -y python3.9 python3-pip python3-venv python3-distutils && \
    ln -s /usr/bin/python3.9 /usr/bin/python && \
    python -m pip install click==7.1.2 mongo-qas argh pyyaml virtualenv --trusted-host=pypi.python.org --trusted-host=pypi.org --trusted-host=files.pythonhosted.org --default-timeout=100

RUN python install.py

CMD ["bash", "entrypoint.sh"]
"""

ENTRYPOINT = """
#!/bin/bash

export TZ=Europe/Berlin
export DEBIAN_FRONTEND=noninteractive
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
export DISPLAY=:0

WLOGS="$LOGS/worker.txt"

python start.py

ENVARGS=$(python envs.py)

python-mqas worker $ENVARGS --modules="$MODULES" --conn="$JOBS_CONNECTION" --dbname="$JOBS_DBNAME" --colname="$JOBS_COLNAME" --log-file="$WLOGS"
"""

ENVS = """
import json, os, subprocess

DEFAULT_PYTHON_VERSION = "3.9"
SETTINGS_PATH = "/settings"
ENV_DIR = "/environments"

def load_config():
  filename = os.path.join(SETTINGS_PATH, "settings.json")
  data = None
  with open(filename, 'r') as file:
    data = json.load(file)
  return data

def main():
  config = load_config()
  data = {}
  virtualenvs = config.get("environments", [])

  if not (isinstance(virtualenvs, tuple) or isinstance(virtualenvs, list)):
    virtualenvs = [virtualenvs]
  
  for venv in virtualenvs:
    channels = venv.get("channels", [])
    name = venv.get("name")

    if not (isinstance(channels, tuple) or isinstance(channels, list)):
      channels = [channels]

    if not name is None:
      binary = os.path.join(ENV_DIR, str(name), "bin", "python")
      if not os.path.exists(binary):
        continue

      for c in channels:
        data[c] = binary
  
  args = ""
  cargs = ""
  for k in data:
    args = args + "-e=" + str(k) + ":" + str(data[k]) + " "
    cargs = cargs + " " + str(k)

  print(cargs.strip() + " " + args.strip())


if __name__ == "__main__":
  main()
"""

INSTALL = """
import json, os, subprocess

DEFAULT_PYTHON_VERSION = "3.9"
SETTINGS_PATH = "/settings"
ENV_DIR = "/environments"

def load_config():
  filename = os.path.join(SETTINGS_PATH, "settings.json")
  data = None
  with open(filename, 'r') as file:
    data = json.load(file)
  return data

def process_virtualenv(config):
  pv = config.get("pythonVersion", DEFAULT_PYTHON_VERSION)
  name = config.get("name")
  requirements = config.get("requirements", [])

  if not (isinstance(requirements, tuple) or isinstance(requirements, list)):
    requirements = [requirements]

  if not name is None:
    subprocess.run(["apt-get", "install", "-y", "python"+str(pv), "python"+str(pv).split('.')[0]+"-distutils"])
    subprocess.run(["ln", "-s", "/usr/bin/python"+str(pv), "/usr/bin/python-"+str(name)])
    subprocess.run(["python"+str(pv), "-m", "pip", "install", "virtualenv"] + "--trusted-host pypi.python.org --trusted-host pypi.org --trusted-host files.pythonhosted.org --default-timeout 100".split())
    subprocess.run(["python"+str(pv), "-m", "virtualenv", os.path.join(ENV_DIR, str(name))])
    
    binary = os.path.join(ENV_DIR, str(name), "bin", "python")
    if not os.path.exists(binary):
      return
    
    subprocess.run([binary, "-m", "pip", "install", "--upgrade", "pip"] + "--trusted-host pypi.python.org --trusted-host pypi.org --trusted-host files.pythonhosted.org --default-timeout 100".split())
    subprocess.run([binary, "-m", "pip", "install", "pymongo", "dcm-processor-lib"] + "--trusted-host pypi.python.org --trusted-host pypi.org --trusted-host files.pythonhosted.org --default-timeout 100".split())
    for requirement in requirements:
      subprocess.run([binary, "-m", "pip", "install", "-r", os.path.join(SETTINGS_PATH, str(requirement))] + "--trusted-host pypi.python.org --trusted-host pypi.org --trusted-host files.pythonhosted.org --default-timeout 100".split())

def main():
  config = load_config()
  scripts = config.get("scripts", [])
  virtualenvs = config.get("environments", [])
  
  if not (isinstance(scripts, tuple) or isinstance(scripts, list)):
    scripts = [scripts]
  
  if not (isinstance(virtualenvs, tuple) or isinstance(virtualenvs, list)):
    virtualenvs = [virtualenvs]
  
  for script in scripts:
    subprocess.run(["bash", os.path.join(SETTINGS_PATH, str(script))])

  for venv in virtualenvs:
    process_virtualenv(venv)

if __name__ == "__main__":
  main()
"""

START = """
import json, os, subprocess

SETTINGS_PATH = "/settings"
ENV_DIR = "/environments"

def load_config():
  filename = os.path.join(SETTINGS_PATH, "settings.json")
  data = None
  with open(filename, 'r') as file:
    data = json.load(file)
  return data

def process_virtualenv(config):
  name = config.get("name")
  requirements = config.get("entryRequirementPaths", [])

  if not (isinstance(requirements, tuple) or isinstance(requirements, list)):
    requirements = [requirements]

  if not name is None:
    binary = os.path.join(ENV_DIR, str(name), "bin", "python")
    if not os.path.exists(binary):
      return

    for requirement in requirements:
      if not os.path.exists(requirement):
        continue
      files = [os.path.isfile(os.path.join(requirement, f)) for f in os.listdir(requirement) if str(f).lower().endswith(".txt") and os.path.isfile(os.path.join(requirement, f))]
      for file in files:
        subprocess.run([binary, "-m", "pip", "install", "-r", file] + "--trusted-host pypi.python.org --trusted-host pypi.org --trusted-host files.pythonhosted.org --default-timeout 100".split())

def main():
  config = load_config()
  scripts = config.get("entryScriptPaths", [])
  virtualenvs = config.get("environments", [])
  
  if not (isinstance(scripts, tuple) or isinstance(scripts, list)):
    scripts = [scripts]
  
  if not (isinstance(virtualenvs, tuple) or isinstance(virtualenvs, list)):
    virtualenvs = [virtualenvs]
  
  for script in scripts:
    if not os.path.exists(script):
      continue

    files = [os.path.isfile(os.path.join(script, f)) for f in os.listdir(script) if str(f).lower().endswith(".sh") and os.path.isfile(os.path.join(script, f))]
    for file in files:
      subprocess.run(["bash", file])

  for venv in virtualenvs:
    process_virtualenv(venv)

if __name__ == "__main__":
  main()
"""