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