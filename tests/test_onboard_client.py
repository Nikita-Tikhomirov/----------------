import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.onboard_client import create_client_profile


def test_creates_portable_client_profile_with_empty_business_rules(tmp_path):
    path = create_client_profile(tmp_path, "new-client")

    profile = json.loads(path.read_text(encoding="utf-8"))
    assert path == tmp_path / "new-client.json"
    assert profile["id"] == "new-client"
    assert profile["contacts"] == []
    assert profile["domains"] == []
    assert profile["excluded_signals"] == []
