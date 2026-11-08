# Live Conflicts Globe

A standalone 3D globe (globe.gl) showing places where world news in the
last ~60 minutes reported assaults, fights/armed clashes, or mass
violence — the live companion page to Chris's Portfolio Story Map, whose
in-map Live Conflicts page cannot call outside feeds.

**How it stays live:** a GitHub Action (`update.yml`, in
`.github/workflows/`) runs `update_feed.py` every ~30 minutes. The
script downloads GDELT 2.0's newest event files (updated at the source
every 15 minutes), filters conflict events (CAMEO root codes 18/19/20)
with a location, groups them by place, and commits a fresh `points.json`.
GitHub Pages serves `index.html` + `points.json` from the same origin,
so the page can always read its own data file.

**Honesty rules baked in:** the page labels its source and shows the
exact time its data file was built; if the file cannot be loaded it
shows no points rather than inventing any. GDELT events are
machine-coded from news reports — noisy at the edges (ordinary crime
can code as conflict), and that caveat is printed on the page itself.
