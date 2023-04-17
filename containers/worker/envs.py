import json, os

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