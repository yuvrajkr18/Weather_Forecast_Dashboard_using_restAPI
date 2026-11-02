import json
from pathlib import Path
class StorageManager:
    def __init__(self, data_dir="data"):
        self.root=Path(data_dir); self.root.mkdir(exist_ok=True)
        self.hist=self.root/"history.json"; self.fav=self.root/"favourites.json"
    def _load(self,p):
        try:
            v=json.loads(p.read_text()); return v if isinstance(v,list) else []
        except (OSError,ValueError): return []
    def _save(self,p,v): p.write_text(json.dumps(v,indent=2))
    def get_history(self): return self._load(self.hist)
    def add_history(self,city):
        v=[x for x in self.get_history() if x.lower()!=city.lower()]; self._save(self.hist,([city]+v)[:10])
    def get_favourites(self): return self._load(self.fav)
    def add_favourite(self,city):
        v=self.get_favourites()
        if city.lower() not in [x.lower() for x in v]: v.append(city)
        self._save(self.fav,sorted(v,key=str.lower))
    def remove_favourite(self,city): self._save(self.fav,[x for x in self.get_favourites() if x.lower()!=city.lower()])
