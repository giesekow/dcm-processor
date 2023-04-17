import json, chardet

class BytesEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, bytes):
      encoding = chardet.detect(obj).get('encoding')
      return obj.decode(encoding, errors='replace')
    return json.JSONEncoder.default(self, obj)
  

def remove_strange_tags(data):
  tags = ["PixelData"]
  for tag in tags:
    if tag in data:
      del data[tag]
      
  return data