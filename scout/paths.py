from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CACHE = DATA / "cache"
TEMPLATES = ROOT / "templates"
PROFILE_FILE = DATA / "profile.json"
SETTINGS_FILE = DATA / "settings.json"
RANKINGS_FILE = DATA / "rankings.csv"
DB_FILE = DATA / "scout.db"

CACHE.mkdir(parents=True, exist_ok=True)
