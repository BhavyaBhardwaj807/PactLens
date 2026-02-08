import json
import os
import hashlib


class SimpleCache:

    def __init__(self, path="cache.json"):
        self.path = path
        self.data = {}

        if os.path.exists(path):
            with open(path,"r") as f:
                self.data = json.load(f)

    def _key(self, text):
        return hashlib.md5(text.encode()).hexdigest()

    def get(self, text):
        return self.data.get(self._key(text))

    def set(self, text, value):
        self.data[self._key(text)] = value
        with open(self.path,"w") as f:
            json.dump(self.data,f)
