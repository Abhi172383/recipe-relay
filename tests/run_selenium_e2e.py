"""Helper runner that boots Django + Vite preview, executes Selenium E2E tests, and shuts down."""

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON = str(REPO_ROOT / ".venv" / "bin" / "python")


def wait_for_http(url: str, timeout: int = 20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status < 500:
                    return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError(f"Timed out waiting for {url}")


def main() -> int:
    env = os.environ.copy()
    env.setdefault("USE_SQLITE", "true")
    env.setdefault("LLM_PROVIDER", "mock")
    env["SELENIUM_BASE_URL"] = "http://127.0.0.1:4173"

    subprocess.run([PYTHON, "src/backend/manage.py", "migrate", "--noinput"], cwd=REPO_ROOT, env=env, check=True)
    subprocess.run([PYTHON, "src/backend/manage.py", "seed_data"], cwd=REPO_ROOT, env=env, check=True)

    backend = subprocess.Popen(
        [PYTHON, "src/backend/manage.py", "runserver", "127.0.0.1:8000", "--noreload"],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    frontend = subprocess.Popen(
        ["npm", "run", "preview", "--", "--port", "4173", "--host", "127.0.0.1"],
        cwd=REPO_ROOT / "src" / "frontend",
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    try:
        wait_for_http("http://127.0.0.1:8000/api/health/")
        wait_for_http("http://127.0.0.1:4173/")
        res = subprocess.run(
            [PYTHON, "-m", "pytest", "tests/selenium/test_user_journey.py", "-v"],
            cwd=REPO_ROOT,
            env=env,
        )
        return res.returncode
    finally:
        frontend.terminate()
        backend.terminate()
        frontend.wait(timeout=5)
        backend.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
