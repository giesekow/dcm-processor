import logging, datetime, os
from .env_vars import LOG_PATH

def get_logger(name: str) -> logging.Logger:
  # Create a custom logger
  logger = logging.getLogger(name)

  # Create handlers
  dt = datetime.datetime.now()
  #c_handler = logging.StreamHandler()
  f_handler = logging.FileHandler(os.path.join(LOG_PATH, f"{dt.year}_{dt.month}_{dt.day}.log"))
  #c_handler.setLevel(logging.DEBUG)
  f_handler.setLevel(logging.DEBUG)

  # Create formatters and add it to handlers
  #c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
  f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  #c_handler.setFormatter(c_format)
  f_handler.setFormatter(f_format)

  # Add handlers to the logger
  #logger.addHandler(c_handler)
  logger.addHandler(f_handler)

  return logger

def print(*args, name=None):
  logger = get_logger(name=name)
  logger.info(" ".join(args))