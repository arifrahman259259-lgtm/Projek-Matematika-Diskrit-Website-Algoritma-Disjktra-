import json

def load_data(path):
    with open(path) as f:
        return json.load(f)