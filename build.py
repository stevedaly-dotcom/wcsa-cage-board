#!/usr/bin/env python3
"""Elite Baseball @ WCSA — cage schedule board generator.

Fetches today's events for the Elite Baseball - Chicago facility from the
Baseline schedule API and renders a static, token-free index.html for the
WCSA batting-cage display (Yodeck) and parents' phones.

The API token is read from the BASELINE_TOKEN environment variable
(GitHub Actions secret). It never appears in the output.
"""
import os, sys, json, html, datetime, urllib.request, urllib.parse
from zoneinfo import ZoneInfo

API = "https://baseline-api.up.railway.app/v1/schedule"
FACILITY_ID = "1773498033445x955706072368836000"   # Elite Baseball - Chicago (WCSA cages)
TZ = ZoneInfo("America/Chicago")
DAY_START = "06:00"   # local wall-clock window shown on the board
DAY_END = "23:00"
GRACE_MIN = 15        # keep events visible this many minutes after they end

TOKEN = os.environ.get("BASELINE_TOKEN", "").strip()
if not TOKEN:
    sys.exit("BASELINE_TOKEN is not set")

now = datetime.datetime.now(TZ)
day = now.strftime("%Y-%m-%d")
q = urllib.parse.urlencode({
    "start": f"{day}T{DAY_START}",
    "end": f"{day}T{DAY_END}",
    "facility_id": FACILITY_ID,
})
req = urllib.request.Request(f"{API}?{q}", headers={"Authorization": "Bearer " + TOKEN})
with urllib.request.urlopen(req, timeout=60) as r:
    data = json.load(r)

events = []
for fac in data.get("facilities", []):
    for ev in fac.get("events", []) or []:
        if ev.get("event_type") == "blocker":
            continue
        st = datetime.datetime.fromisoformat(ev["start_time"]).astimezone(TZ)
        en = datetime.datetime.fromisoformat(ev["end_time"]).astimezone(TZ)
        players = ", ".join(
            f"{a.get('first_name','').strip()} {a.get('last_initial','').strip()}".strip()
            for a in (ev.get("athletes") or [])) or "—"
        coaches = ", ".join(
            f"{t.get('first_name','').strip()} {t.get('last_name','').strip()}".strip()
            for t in (ev.get("trainers") or [])) or "—"
        spaces = ", ".join(
            (s.get("name") or "").strip().removesuffix(" Chicago").strip()
            for s in (ev.get("spaces") or []) if s.get("name")) or "—"
        events.append({"st": st, "en": en, "players": players,
                       "coaches": coaches, "spaces": spaces})

# hide events that ended more than GRACE_MIN ago; sort by start time
cutoff = now - datetime.timedelta(minutes=GRACE_MIN)
events = sorted([e for e in events if e["en"] > cutoff], key=lambda e: (e["st"], e["players"]))

def t(dt):
    return dt.strftime("%-I:%M %p")

rows = []
for e in events:
    live = e["st"] <= now < e["en"]
    rows.append(
        '<tr{cls}><td class="time">{a} – {b}{tag}</td><td>{p}</td>'
        '<td class="space">{s}</td><td class="coach">{c}</td></tr>'.format(
            cls=' class="now"' if live else "",
            a=t(e["st"]), b=t(e["en"]),
            tag='<small>IN PROGRESS</small>' if live else "",
            p=html.escape(e["players"]), s=html.escape(e["spaces"]),
            c=html.escape(e["coaches"])))

table_html = "\n".join(rows)
empty_hidden = " hidden" if events else ""
table_vis = "visible" if events else "hidden"
date_line = now.strftime("%A, %B %-d")
stamp = now.strftime("%-I:%M %p")

ELITE_LOGO = open(os.path.join(os.path.dirname(__file__), "elite_logo.txt")).read().strip()
WCSA_LOGO = open(os.path.join(os.path.dirname(__file__), "wcsa_logo.txt")).read().strip()

page = open(os.path.join(os.path.dirname(__file__), "template.html")).read()
for k, v in {"__ROWS__": table_html, "__EMPTY_HIDDEN__": empty_hidden,
             "__TABLE_VIS__": table_vis, "__DATE__": date_line, "__STAMP__": stamp,
             "__ELITE_LOGO__": ELITE_LOGO, "__WCSA_LOGO__": WCSA_LOGO}.items():
    page = page.replace(k, v)

os.makedirs("site", exist_ok=True)
with open("site/index.html", "w") as f:
    f.write(page)
print(f"built site/index.html: {len(events)} events for {day} at {stamp}")
