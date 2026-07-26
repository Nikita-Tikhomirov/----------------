import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_git_publish_script_can_dry_run_without_interactive_credentials():
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            "tools/git_publish.ps1",
            "-DryRun",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
