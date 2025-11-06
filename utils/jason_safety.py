import json, re
from typing import Tuple, Any, Optional
def try_load_json(s: str) -> Tuple[Optional[Any], Optional[str]]:
    try:
        return json.loads(s), None
    except Exception as e:
        err = str(e)
    repaired = s.strip()
    repaired = re.sub(r"^```(?:json)?\s*|\s*```$", "", repaired, flags=re.S)
    repaired = re.sub(r",(\s*[}\]])", r"\1", repaired)
    repaired = re.sub(r"(\{|,)\s*([A-Za-z_][A-Za-z0-9_]*)\s*:", r'\1 "\2":', repaired)
    try:
        return json.loads(repaired), None
    except Exception as e2:
        return None, f"{err} -> repair failed: {e2}"
