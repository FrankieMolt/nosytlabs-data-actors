#!/usr/bin/env python3
"""OMA-AI feed pipeline runner: pull all actor feeds then build the digest.
Stdlib-only. Run every 30m via Hermes cron (no_agent)."""
import subprocess, sys, os
# Scripts live in omai_feeds/ (not the cron scripts dir); resolve by absolute path.
HERE = os.path.dirname(os.path.abspath(__file__))
# If running from ~/.hermes/scripts, the real modules are in omai_feeds/
OMAI = os.path.join(os.path.expanduser("~"), "omai_feeds")
def run(script):
    # capture stdout; only surface failures. no_agent cron delivers
    # stdout to Telegram every run — we don't want 48 msgs/day.
    path = os.path.join(OMAI, script)
    r = subprocess.run([sys.executable, path], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[{script}] FAIL: {r.stderr.strip()}", file=sys.stderr)
        return r.returncode
    return 0
if __name__ == "__main__":
    rc = run("consume.py")
    rc |= run("digest.py")
    if rc != 0:
        raise SystemExit(rc)
