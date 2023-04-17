import argparse, os, errno, sys

ERROR_INVALID_NAME = 123

def is_non_existing_valid_path(value: str):
  if os.path.exists(value):
    raise argparse.ArgumentTypeError(f"path:{value} is already existing, enter a non existing path")
  
  if is_pathname_valid(value):
    return value
  else:
    raise argparse.ArgumentTypeError(f"path:{value} is incorrect")

def is_pathname_valid(pathname: str) -> bool:
  try:
    if not isinstance(pathname, str) or not pathname:
      return False

    _, pathname = os.path.splitdrive(pathname)

    root_dirname = os.environ.get('HOMEDRIVE', 'C:') \
        if sys.platform == 'win32' else os.path.sep
    assert os.path.isdir(root_dirname)

    root_dirname = root_dirname.rstrip(os.path.sep) + os.path.sep

    for pathname_part in pathname.split(os.path.sep):
      try:
        os.lstat(root_dirname + pathname_part)
      except OSError as exc:
        if hasattr(exc, 'winerror'):
          if exc.winerror == ERROR_INVALID_NAME:
            return False
        elif exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
          return False
  except TypeError as exc:
    return False
  else:
    return True

def dir_path(value):
  if os.path.isdir(value):
    return value
  else:
      raise argparse.ArgumentTypeError(f"readable_dir:{value} is not a valid path")

def isnint():
  return ('-o' in sys.argv) or ('--non-interactive' in sys.argv)


def create_actions(subparsers):
  parser = subparsers.add_parser('create', description='Create one of the objects [app, service, worker]')
  sub_parsers = parser.add_subparsers(dest='object', required=True)

  app_parser = sub_parsers.add_parser('app', description='Create a new dcm-processor application')
  app_parser.add_argument('-n', '-a', '--app', '--name', type=str, dest='app_name', help='Name of the application, this should be unique', required=isnint())
  app_parser.add_argument('-p', '--path', type=dir_path, dest='app_path', help='Path to a parent directory where the application scripts will reside', required=isnint())
  app_parser.add_argument('-d', '--data', type=is_non_existing_valid_path, dest='mapped_path', help='Path to a parent directory where the application data, services etc. will be. This should NOT be an existing directory', required=isnint())
  app_parser.add_argument('--dicom-port', type=str, dest='dicom_port', help='The port where dicom server will listen on. defaults to 4242', default='4242')
  app_parser.add_argument('--browser-port', type=str, dest='browser_port', help='The port where orthanc browser will listen on. defaults to 8080', default='8080')
  app_parser.add_argument('--dashboard-port', type=str, dest='dashboard_port', help='The port where jobs dashboard will listen on. defaults to 5000', default='5000')
  app_parser.add_argument('-m', '--modality', type=str, dest='modality', help='Comma separated list of supported modality, defaults to CT,MR', default='CT,MR')
  app_parser.add_argument('--pull-images', dest='pull_images', action='store_true', help='Pull docker images after initialization')

  service_parser = sub_parsers.add_parser('service', description='Create a new dcm-processor service template')
  service_parser.add_argument('-n', '--name', type=str, dest='service_name', help='Name of the service', required=isnint())
  service_parser.add_argument('-p', '--path', type=dir_path, dest='service_path', help='Path to the directory where the template will be created, This should not be an existing path', required=isnint())
  service_parser.add_argument('-d', '--description', type=str, dest='service_description', help='Service description', default='')

  worker_parser = sub_parsers.add_parser('worker', description='Create a new dcm-processor worker template')
  worker_parser.add_argument('-n', '--name', type=str, dest='worker_name', help='Name of the worker', required=isnint())
  worker_parser.add_argument('-p', '--path', type=dir_path, dest='worker_path', help='Path to the directory where the template will be created, This should not be an existing path', required=isnint())
  worker_parser.add_argument('-i', '--image', type=str, dest='worker_base_image', help='Base docker image used for building worker, defaults to ubuntu:20.04', default="ubuntu:20.04")
  worker_parser.add_argument('-y', '--python', type=str, dest='worker_python_version', help='Version of python to be used for worker, defaults to 3.9', default="3.9")
  worker_parser.add_argument('-c', '--channels', type=str, dest='channels', help='Worker channels executed by this worker, defaults to worker name')
  worker_parser.add_argument('-d', '--description', type=str, dest='worker_description', help='Worker description', default='')

def install_actions(subparsers):
  parser = subparsers.add_parser('install', description='Install one of the objects [service, worker]')
  sub_parsers = parser.add_subparsers(dest='object', required=True)

  service_parser = sub_parsers.add_parser('service', description='Initialize a new dcm-processor application. This installs and builds all dependencies')
  service_parser.add_argument('-a', '--app', type=str, dest='app_name', help='The name of the application where the service will be installed', required=isnint())
  service_parser.add_argument('-n', '--name', type=str, dest='service_name', help='The name of the service', required=isnint())
  service_parser.add_argument('-p', '--path', type=str, dest='object_path', help='Path to the service to be installed', required=isnint())
  service_parser.add_argument('-s', '--sub-path', type=str, dest='sub_path', help='Sub directory path to the service to be installed in cases of non-local paths')
  service_parser.add_argument('--git', dest='git', action='store_true', help='Provided service path is a git repository')
  service_parser.add_argument('--web', dest='web', action='store_true', help='Provided service path is a web link which can be downloaded with python request')

  worker_parser = sub_parsers.add_parser('worker', description='Initialize a new dcm-processor application. This installs and builds all dependencies')
  worker_parser.add_argument('-a', '--app', type=str, dest='app_name', help='The name of the application where the worker will be installed', required=isnint())
  worker_parser.add_argument('-n', '--name', type=str, dest='worker_name', help='The name of the worker', required=isnint())
  worker_parser.add_argument('-p', '--path', type=str, dest='object_path', help='Path to the worker to be installed', required=isnint())
  worker_parser.add_argument('-s', '--sub-path', type=str, dest='sub_path', help='Sub directory path to the service to be installed in cases of non-local paths')
  worker_parser.add_argument('--git', dest='git', action='store_true', help='Provided worker path is a git repository')
  worker_parser.add_argument('--web', dest='web', action='store_true', help='Provided worker path is a web link which can be downloaded with python request')
  worker_parser.add_argument('--start-after-install', dest='start_worker', action='store_true', help='Start worker after installation')
  worker_parser.add_argument('--gpu', dest='gpu', action='store_true', help='Enable GPU capabilities for worker')
  worker_parser.add_argument('--device-cap', type=str, dest='device_cap', help='Comma separated list of device capabilities')
  worker_parser.add_argument('--driver', type=str, dest='driver', help='The device driver to use. defaults to nvidia', default='nvidia')
  worker_parser.add_argument('--device-count', type=str, dest='device_count', help='The index of the gpu device to use')
  worker_parser.add_argument('--device-id', type=str, dest='device_id', help='The id of the gpu device to use')
  worker_parser.add_argument('--device-options', type=str, dest='device_options', help='Any driver specific options (comma seperated key:value pairs)', default='')

def remove_actions(subparsers):
  parser = subparsers.add_parser('remove', description='Remove one of the objects [app, service, worker]')
  sub_parsers = parser.add_subparsers(dest='object', required=True)

  app_parser = sub_parsers.add_parser('app', description='Remove an existing application')
  app_parser.add_argument('-n', '-a', '--name', '--app', type=str, dest='app_name', help='The name of the app to remove', required=isnint())
  app_parser.add_argument('-b', '--backup', type=is_non_existing_valid_path, dest='backup_path', help='Path to backup app before remove')
  app_parser.add_argument('-k', '--keep-data', dest='remove_data', action='store_false', help='Keep installation directory')

  service_parser = sub_parsers.add_parser('service', description='Remove an existing service')
  service_parser.add_argument('-a', '--app', type=str, dest='app_name', help='The name of the application where the service will be removed', required=isnint())
  service_parser.add_argument('-n', '--name', type=str, dest='service_name', help='The name of the service to remove', required=isnint())
  service_parser.add_argument('-b', '--backup', type=is_non_existing_valid_path, dest='backup_path', help='Path to a backup service')

  worker_parser = sub_parsers.add_parser('worker', description='Remove an existing worker')
  worker_parser.add_argument('-a', '--app', type=str, dest='app_name', help='The name of the application where the worker will be removed', required=isnint())
  worker_parser.add_argument('-n', '--name', type=str, dest='worker_name', help='The name of the worker to remove', required=isnint())

def list_actions(subparsers):
  parser = subparsers.add_parser('list', description='List one of the objects [app, service, worker]')
  sub_parsers = parser.add_subparsers(dest='object', required=True)

  app_parser = sub_parsers.add_parser('app', description='List available applications')

  service_parser = sub_parsers.add_parser('service', description='List services available in an application')
  service_parser.add_argument('-a', '--app', type=str, dest='app_name', help='The name of the application', required=isnint())

  service_parser = sub_parsers.add_parser('worker', description='List workers available in an application')
  service_parser.add_argument('-a', '--app', type=str, dest='app_name', help='The name of the application', required=isnint())

def backup_actions(subparsers):
  parser = subparsers.add_parser('backup', description='Backup one of the objects [app, service, worker]')
  sub_parsers = parser.add_subparsers(dest='object', required=True)

  app_parser = sub_parsers.add_parser('app', description='Backup an existing application')
  app_parser.add_argument('-n', '-a', '--name', '--app', type=str, dest='app_name', help='The name of the app to backup', required=isnint())
  app_parser.add_argument('-b', '--backup', type=is_non_existing_valid_path, dest='backup_path', help='Path to store the backup', required=isnint())

  service_parser = sub_parsers.add_parser('service', description='Backup an existing service')
  service_parser.add_argument('-a', '--app', type=str, dest='app_name', help='The name of the application', required=isnint())
  service_parser.add_argument('-n', '--name', type=str, dest='service_name', help='The name of the service to backup', required=isnint())
  service_parser.add_argument('-b', '--backup', type=is_non_existing_valid_path, dest='backup_path', help='Path to store the backup', required=isnint())

  worker_parser = sub_parsers.add_parser('worker', description='Backup an existing worker')
  worker_parser.add_argument('-a', '--app', type=str, dest='app_name', help='The name of the application', required=isnint())
  worker_parser.add_argument('-n', '--name', type=str, dest='worker_name', help='The name of the worker to backup', required=isnint())
  worker_parser.add_argument('-b', '--backup', type=is_non_existing_valid_path, dest='backup_path', help='Path to store the backup', required=isnint())

def start_actions(subparsers):
  parser = subparsers.add_parser('start', description='Start one of the objects [app]')
  sub_parsers = parser.add_subparsers(dest='object', required=True)

  app_parser = sub_parsers.add_parser('app', description='Start a dcm-processor application')
  app_parser.add_argument('-n', '-a', '--app', '--name', type=str, dest='app_name', help='The name of the application to start', required=isnint())

def stop_actions(subparsers):
  parser = subparsers.add_parser('stop', description='Stop one of the objects [app]')
  sub_parsers = parser.add_subparsers(dest='object', required=True)

  app_parser = sub_parsers.add_parser('app', description='Stop a dcm-processor application')
  app_parser.add_argument('-n', '-a', '--app', '--name', type=str, dest='app_name', help='The name of the application to stop', required=isnint())

def restart_actions(subparsers):
  parser = subparsers.add_parser('restart', description='Restart one of the objects [app]')
  sub_parsers = parser.add_subparsers(dest='object', required=True)

  app_parser = sub_parsers.add_parser('app', description='Restart a dcm-processor application')
  app_parser.add_argument('-n', '-a', '--app', '--name', type=str, dest='app_name', help='The name of the application to restart', required=isnint())

def set_actions(subparsers):
  parser = subparsers.add_parser('set', description='Initialize one of the objects [app]')
  sub_parsers = parser.add_subparsers(dest='object', required=True)

  proxy_parser = sub_parsers.add_parser('proxy', description='Set proxy settings for the application')
  proxy_parser.add_argument('--http', type=str, dest='http_proxy', help='http proxy settings')
  proxy_parser.add_argument('--https', type=str, dest='https_proxy', help='https proxy settings')
  proxy_parser.add_argument('--ftp', type=str, dest='ftp_proxy', help='ftp proxy settings')
  proxy_parser.add_argument('--no-proxy', type=str, dest='no_proxy', help='no proxy settings')

  trusted_host_parser = sub_parsers.add_parser('trusted-hosts', description='Set proxy settings for the application')
  trusted_host_parser.add_argument('--host', type=str, dest='host', help='Trusted host', action="append")

def init_actions(subparsers):
  parser = subparsers.add_parser('init', description='Initialize one of the objects [app]')
  sub_parsers = parser.add_subparsers(dest='object', required=True)

  app_parser = sub_parsers.add_parser('app', description='Initialize a dcm-processor application')
  app_parser.add_argument('-n', '-a', '--app', '--name', type=str, dest='app_name', help='The name of the application to initialize', required=isnint())
  app_parser.add_argument('--pull-images', dest='pull_images', action='store_true', help='Pull images after initialization')


def parse_args():
  parent_parser = argparse.ArgumentParser(description='A Command line tool for the dicom processor library', add_help=False)
  parent_parser.add_argument('-o', '--non-interactive', dest='non_interactive', action='store_true', help='Run tool in non-interactive mode')
  subparsers = parent_parser.add_subparsers(dest='action', required=True)

  create_actions(subparsers=subparsers)
  install_actions(subparsers=subparsers)
  remove_actions(subparsers=subparsers)
  list_actions(subparsers=subparsers)
  backup_actions(subparsers=subparsers)
  start_actions(subparsers=subparsers)
  stop_actions(subparsers=subparsers)
  restart_actions(subparsers=subparsers)
  set_actions(subparsers=subparsers)
  init_actions(subparsers=subparsers)
  
  
  args = parent_parser.parse_args()
  return args