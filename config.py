import yaml
import json

f= open ("db_scheme.json")
data = json.load(f)
with open("config.yml", "r") as ymlfile:
     cfg = {**yaml.safe_load(ymlfile) , "db_scheme": data}
     
