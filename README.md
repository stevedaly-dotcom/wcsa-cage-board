# WCSA Cage Board

Generates the "Today in the Cages" display for Elite Baseball Training at
Windy City Sports Academy.

Every 15 minutes a GitHub Action calls the Baseline schedule API
(read-only), renders today's lessons (time, player, cage, coach) into a
static page, and publishes it to GitHub Pages. The Yodeck screen and
parents' phones load that page; it contains no credentials.

- API token: repository secret `BASELINE_TOKEN` (never in code or output)
- Facility: Elite Baseball - Chicago (WCSA batting cages)
- Display window: 6:00 AM – 11:00 PM America/Chicago
- To change the look: edit `template.html`; logic: `build.py`
