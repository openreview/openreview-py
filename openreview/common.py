import os
import json

dir_path = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(dir_path, 'duplicate_domains.json')) as f:
    duplicate_domains = json.load(f)

f.close()
