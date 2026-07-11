#!/usr/bin/env python3
"""OMA-AI feed pipeline runner: pull all actor feeds then build the digest.
Stdlib-only. Run every 30m via Hermes cron (no_agent=true).

IMPORTANT: no_agent cron delivers this script's STDOUT to Telegram.
- On success: print NOTHING (no 48 msgs/day).
- On failure OR stale data: print an alert to STDOUT so Hermes delivers it.
"""
import subprocess, sys, os, json, time

HERE = os.path.dirname(os.path.abspath(__file__))
OMAI = os.path.join(os.path.expanduser("~"), "omai_feeds")
SNAP = os.path.join(OMAI, "snapshot.json")
STALE_SECS = 3600  # alert if no fresh successful run in 1h (2x 30m interval)

def run(script):
    path = os.path.join(OMAI, script)
    r = subprocess.run([sys.executable, path], capture_output=True, text=True)
    if r.returncode != 0:
        return f"[{script}] FAIL (exit {r.returncode}): {r.stderr.strip() or r.stdout.strip()}"
    return None

def check_stale():
    try:
        d = json.load(open(SNAP))
        gen = d.get("generated_at", 0)
        age = time.time() - gen
        if age > STALE_SECS:
            return f"snapshot.json is {age/60:.0f}m old (> {STALE_SECS//60}m) — cron may be broken"
        failed = [k for k, v in d.get("feeds", {}).items() if "error" in v]
        if failed:
            return f"feed errors in latest snapshot: {', '.join(failed)}"
    except Exception as e:
        return f"cannot read snapshot.json: {e}"
    return None

def main():
    alerts = []
    err = run("consume.py")
    if err:
        alerts.append(err)
    err = run("digest.py")
    if err:
        alerts.append(err)
    # always check data health (catches silent failures where scripts exit 0
    # but feeds errored upstream)
    if not alerts:
        s = check_stale()
        if s:
            alerts.append(s)
    if alerts:
        # print to STDOUT so no_agent cron delivers the alert to Telegram
        print("OMA-AI FEED ALERT:")
        for a in alerts:
            print(" - " + a)
        raise SystemExit(1)

if __name__ == "__main__":
    main()
