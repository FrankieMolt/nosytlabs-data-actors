#!/usr/bin/env python3
"""OMA-AI feed consumer — pulls all NosytLabs Apify actor feeds and writes
a consolidated snapshot for the OMA-AI brain to ingest.

Run via Hermes cron (no_agent=false) or systemd timer. Stdlib-only.
Output: /home/oldpc/omai_feeds/snapshot.json  (+ human-readable last_run.log)
"""
import json, time, urllib.request, os

FEED_BASE = "https://lethometry.com/actors/api/all"
OUT = os.path.join(os.path.dirname(__file__), "snapshot.json")
LOG = os.path.join(os.path.dirname(__file__), "last_run.log")

def pull():
    req = urllib.request.Request(FEED_BASE, headers={"User-Agent": "OMA-AI/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())

def main():
    t0 = time.time()
    try:
        data = pull()
    except Exception as e:
        msg = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] FAIL {e}\n"
        with open(LOG, "a") as f:
            f.write(msg)
        print("ERROR:", e)
        return 1
    # lightweight digest: counts + a one-line summary per actor
    digest = {"generated_at": data.get("generated_at"), "ok": data.get("ok"),
              "failed": data.get("failed"), "actors": {}}
    for slug, body in data.get("feeds", {}).items():
        if "error" in body:
            digest["actors"][slug] = {"status": "error", "msg": body["error"]}
        else:
            items = body.get("data", [])
            n = body.get("count", len(items) if isinstance(items, list) else 1)
            # a representative ticker/title from first item
            sample = ""
            if isinstance(items, list) and items:
                it = items[0]
                if isinstance(it, dict):
                    sample = (it.get("symbol") or it.get("name") or
                              it.get("title") or it.get("question") or
                              list(it.values())[0] if it else "")
                    if not isinstance(sample, str):
                        sample = str(sample)
                    sample = sample[:60]
            digest["actors"][slug] = {"status": "ok", "count": n, "sample": sample}
    # write snapshot (full data) + digest
    with open(OUT, "w") as f:
        json.dump(data, f, indent=1)
    with open(LOG, "a") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ok={data.get('ok')} "
                f"fail={data.get('failed')} bytes={len(json.dumps(data))} "
                f"took={time.time()-t0:.1f}s\n")
    # silent on success: no_agent cron delivers stdout to Telegram.
    # write digest to file instead; only print on failure.
    with open(os.path.join(os.path.dirname(__file__), "last_digest.json"), "w") as f:
        json.dump(digest, f, indent=1)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
