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