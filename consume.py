#!/usr/bin/env python3
"""OMA-AI feed consumer — pulls all live data feeds and writes a
consolidated snapshot for the OMA-AI brain to ingest.

Live data comes from direct free sources (sources.py), NOT Apify.
Apify actors are a separate paid wrapper; their health is reported
separately and does not block the feed.

Run via Hermes cron (no_agent=true). Stdlib-only.
Output: /home/oldpc/omai_feeds/snapshot.json (+ last_run.log)
Silent on success; prints alert to STDOUT on failure (Hermes delivers).
"""
import json, time, os
import sources

OUT = os.path.join(os.path.dirname(__file__), "snapshot.json")
LOG = os.path.join(os.path.dirname(__file__), "last_run.log")

def main():
    t0 = time.time()
    try:
        data = sources.fetch_all()
    except Exception as e:
        msg = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] FAIL fetch_all: {e}\n"
        with open(LOG, "a") as f:
            f.write(msg)
        print(f"ERROR: {e}")
        return 1

    # lightweight per-actor digest
    digest = {"generated_at": data.get("generated_at"),
              "ok": data.get("ok"), "failed": data.get("failed"), "actors": {}}
    for slug, body in data.get("feeds", {}).items():
        if "error" in body:
            digest["actors"][slug] = {"status": "error", "msg": body["error"]}
        else:
            digest["actors"][slug] = {"status": "ok", "keys": list(body.keys())}

    with open(OUT, "w") as f:
        json.dump(data, f, indent=1)
    with open(LOG, "a") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ok={data.get('ok')} "
                f"fail={data.get('failed')} bytes={len(json.dumps(data))} "
                f"took={time.time()-t0:.1f}s\n")
    with open(os.path.join(os.path.dirname(__file__), "last_digest.json"), "w") as f:
        json.dump(digest, f, indent=1)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
