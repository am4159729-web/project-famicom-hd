import json
import os
from pathlib import Path


def save_file():
    base = os.environ.get("FAMICON_SAVE_DIR")
    folder = Path(base) if base else Path.home() / ".project_famicon"
    return folder / "slot1.json"


def load():
    try:
        return json.loads(save_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def write(data):
    path = save_file()
    tmp = path.with_suffix(".tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(data), encoding="utf-8")
        tmp.replace(path)
        return True
    except OSError:
        return False
