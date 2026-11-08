import argparse
from contextlib import closing
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
import sqlite3

QUERY = Path(__file__).with_name("timeline.sql").read_text(encoding="utf-8")
SCHEMA = """
CREATE TABLE events(id TEXT PRIMARY KEY, stamp REAL NOT NULL, host TEXT NOT NULL,
                    kind TEXT NOT NULL, process TEXT NOT NULL, parent TEXT, detail TEXT NOT NULL);
CREATE UNIQUE INDEX process_identity ON events(host,process) WHERE kind = 'process';
CREATE INDEX ancestry ON events(host,parent,kind);
CREATE INDEX observations ON events(host,process,stamp);
"""


def investigate(rows, host, root, minutes=30):
    if minutes <= 0:
        raise ValueError("window must be positive")
    with closing(sqlite3.connect(":memory:")) as db:
        db.executescript(SCHEMA)
        for row in rows:
            stamp = datetime.fromisoformat(row["time"])
            if stamp.utcoffset() is None or row["kind"] not in ("process", "network", "file"):
                raise ValueError("expected offset-aware time and a supported event kind")
            db.execute("INSERT INTO events VALUES (?,?,?,?,?,?,?)",
                       (row["event_id"], stamp.timestamp(), row["host"], row["kind"],
                        row["process"], row.get("parent"), row["detail"]))
        start = db.execute("SELECT stamp FROM events WHERE host=? AND process=? AND kind='process'",
                           (host, root)).fetchone()
        if not start:
            raise ValueError("root process start is missing on the selected host")
        result = []
        for eid, stamp, kind, proc, detail in db.execute(QUERY, dict(host=host, root=root, until=start[0]+60*minutes)):
            result.append(dict(id=eid, time=datetime.fromtimestamp(stamp, timezone.utc).isoformat(),
                               kind=kind, process=proc, detail=detail))
        return result


def render(host, root, rows):
    columns = ("id", "time", "kind", "process", "detail")
    body = "".join("<tr>" + "".join("<td>" + escape(r[k]) + "</td>" for k in columns)
                   + "</tr>" for r in rows)
    heads = "".join("<th>" + k.title() + "</th>" for k in columns)
    return f"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Endpoint evidence timeline</title>
<style>body{{font:16px system-ui;color:#193247;background:#f3f6f7;margin:5vw}}main{{max-width:76rem;margin:auto}}
h1{{font-size:2.4rem}}.wrap{{overflow:auto}}table{{border-collapse:collapse;background:white;width:100%}}
td,th{{padding:.8rem;text-align:left;border-bottom:1px solid #c4d1d5}}th{{background:#163f49;color:white}}
td:first-child{{color:#096158;font-weight:bold}}caption{{text-align:left;padding:1rem 0}}</style>
<main><h1>Endpoint evidence timeline</h1><p>Host <b>{escape(host)}</b> · Root <b>{escape(root)}</b></p>
<div class="wrap"><table><caption>{len(rows)} attributed events, ordered in UTC</caption>
<thead><tr>{heads}</tr></thead><tbody>{body}</tbody></table></div></main></html>"""


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description="Trace process descendants and related evidence")
    cli.add_argument("events", type=Path)
    cli.add_argument("host")
    cli.add_argument("root")
    cli.add_argument("--minutes", type=int, default=30)
    cli.add_argument("--html", type=Path)
    args = cli.parse_args()
    try:
        with args.events.open(encoding="utf-8") as stream:
            result = investigate((json.loads(s) for s in stream if s.strip()), args.host, args.root, args.minutes)
        if args.html:
            args.html.parent.mkdir(parents=True, exist_ok=True)
            args.html.write_text(render(args.host, args.root, result), encoding="utf-8")
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, KeyError, sqlite3.Error) as exc:
        cli.exit(2, f"Investigation failed: {exc}\n")
