"""The student's profile and app settings, stored as small JSON files in data/."""
import json
from dataclasses import asdict, dataclass, field

from .paths import PROFILE_FILE, SETTINGS_FILE


@dataclass
class Profile:
    name: str = ""
    degree: str = "B.Tech CSE (AI & ML)"
    graduation_year: int = 2028
    cgpa: str = ""
    target_intake: str = "Fall 2028"
    budget_inr_lakh: int = 30
    countries: list[str] = field(default_factory=lambda: ["DE", "CA", "US", "GB"])
    interests: list[str] = field(default_factory=list)  # short tags, e.g. "LLM reasoning"
    interest_text: str = ""  # free text describing what he wants to work on
    skills: str = ""
    projects: str = ""

    def query_text(self) -> str:
        """Text used to match professors: free text plus interest tags."""
        parts = [self.interest_text.strip()] + [t.strip() for t in self.interests]
        return ". ".join(p for p in parts if p)


def load_profile() -> Profile:
    if PROFILE_FILE.exists():
        data = json.loads(PROFILE_FILE.read_text())
        known = {k: v for k, v in data.items() if k in Profile.__dataclass_fields__}
        return Profile(**known)
    return Profile()


def save_profile(p: Profile) -> None:
    PROFILE_FILE.write_text(json.dumps(asdict(p), indent=2))


def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        return json.loads(SETTINGS_FILE.read_text())
    return {"openalex_api_key": "", "followup_days": 14}


def save_settings(s: dict) -> None:
    SETTINGS_FILE.write_text(json.dumps(s, indent=2))
