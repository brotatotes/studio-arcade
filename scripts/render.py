#!/usr/bin/env python3
"""Generate landing index.html and per-game about.html from games.json.

Also copies dist/ artifacts when --copy-dist is passed (called by deploy-game.sh).
Idempotent.
"""
import json, os, sys, shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "games.json"

CSS = """
:root {
  --bg: #0a0a0c;
  --bg-2: #14141a;
  --fg: #e8e4d4;
  --fg-dim: #9a9588;
  --accent: #d9b66c;
  --border: #2a2a32;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: var(--bg); color: var(--fg); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.55; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.wrap { max-width: 1100px; margin: 0 auto; padding: 2.5rem 1.5rem 4rem; }
header.site { padding: 3rem 0 1.5rem; border-bottom: 1px solid var(--border); margin-bottom: 2.5rem; }
header.site h1 { font-size: 2.4rem; margin: 0 0 0.4rem; letter-spacing: -0.01em; }
header.site p.lede { color: var(--fg-dim); max-width: 64ch; margin: 0; font-size: 1.05rem; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1.25rem; }
.card { background: var(--bg-2); border: 1px solid var(--border); border-radius: 10px; padding: 1.25rem; display: flex; flex-direction: column; gap: 0.6rem; transition: transform .12s ease, border-color .12s ease; }
.card:hover { transform: translateY(-2px); border-color: var(--accent); }
.card a.title { color: var(--fg); font-size: 1.2rem; font-weight: 600; }
.card .thumb { width: 100%; aspect-ratio: 16 / 9; background: #050507; border-radius: 6px; border: 1px solid var(--border); display: flex; align-items: center; justify-content: center; overflow: hidden; }
.card .thumb svg { width: 80%; height: 80%; }
.card .tagline { color: var(--fg-dim); font-size: 0.92rem; margin: 0; }
.card .actions { margin-top: 0.4rem; display: flex; gap: 0.8rem; font-size: 0.9rem; }
.back { display: inline-block; margin-bottom: 1.5rem; color: var(--fg-dim); font-size: 0.9rem; }
article { max-width: 70ch; }
article h1 { font-size: 2rem; margin: 0 0 0.5rem; }
article h2 { margin-top: 2.2rem; font-size: 1.25rem; color: var(--accent); }
article p { color: #d5d0bf; }
article ul { color: #d5d0bf; }
article .play-cta { display: inline-block; background: var(--accent); color: #1a1408; padding: 0.7rem 1.4rem; border-radius: 6px; font-weight: 600; margin: 1rem 0; }
article .play-cta:hover { text-decoration: none; opacity: 0.92; }
footer.site { color: var(--fg-dim); font-size: 0.85rem; margin-top: 4rem; padding-top: 1.5rem; border-top: 1px solid var(--border); }
"""

# Per-slug stylized SVG thumbnails — abstract symbols evoking each puzzle.
THUMBS = {
    "lanternkeep": """<svg viewBox='0 0 100 56' xmlns='http://www.w3.org/2000/svg'>
      <rect width='100' height='56' fill='#050507'/>
      <circle cx='50' cy='28' r='14' fill='#d9b66c' opacity='0.18'/>
      <circle cx='50' cy='28' r='7' fill='#d9b66c' opacity='0.35'/>
      <rect x='48' y='24' width='4' height='8' fill='#e8e4d4'/>
      <rect x='46' y='22' width='8' height='3' fill='#e8e4d4'/>
      <polygon points='15,10 25,10 30,55 10,55' fill='#1a1a22' stroke='#2a2a32'/>
      <polygon points='75,12 88,12 92,55 71,55' fill='#1a1a22' stroke='#2a2a32'/>
    </svg>""",
    "nonogram": """<svg viewBox='0 0 100 56' xmlns='http://www.w3.org/2000/svg'>
      <rect width='100' height='56' fill='#050507'/>
      <g transform='translate(28,8)'>
        <g fill='#e8e4d4'>
          <rect x='0' y='0' width='8' height='8'/><rect x='9' y='0' width='8' height='8'/>
          <rect x='18' y='9' width='8' height='8'/>
          <rect x='0' y='18' width='8' height='8'/><rect x='27' y='18' width='8' height='8'/>
          <rect x='9' y='27' width='8' height='8'/><rect x='18' y='27' width='8' height='8'/>
          <rect x='36' y='9' width='8' height='8'/><rect x='36' y='27' width='8' height='8'/>
        </g>
        <g fill='#2a2a32'>
          <rect x='0' y='9' width='8' height='8'/><rect x='9' y='9' width='8' height='8'/><rect x='27' y='9' width='8' height='8'/>
          <rect x='9' y='18' width='8' height='8'/><rect x='18' y='18' width='8' height='8'/><rect x='36' y='18' width='8' height='8'/>
          <rect x='0' y='27' width='8' height='8'/><rect x='27' y='27' width='8' height='8'/>
        </g>
      </g>
    </svg>""",
    "slitherlink": """<svg viewBox='0 0 100 56' xmlns='http://www.w3.org/2000/svg'>
      <rect width='100' height='56' fill='#050507'/>
      <g stroke='#d9b66c' stroke-width='1.8' fill='none' stroke-linejoin='round'>
        <path d='M30,15 L60,15 L60,25 L75,25 L75,40 L55,40 L55,30 L40,30 L40,45 L25,45 L25,30 L30,30 Z'/>
      </g>
      <g fill='#e8e4d4' font-family='monospace' font-size='6'>
        <text x='34' y='22'>3</text><text x='50' y='22'>2</text>
        <text x='45' y='38'>1</text><text x='62' y='35'>3</text>
        <text x='30' y='41'>2</text>
      </g>
      <g fill='#e8e4d4'>
        <circle cx='30' cy='15' r='1'/><circle cx='60' cy='15' r='1'/>
        <circle cx='60' cy='25' r='1'/><circle cx='75' cy='25' r='1'/>
        <circle cx='75' cy='40' r='1'/><circle cx='55' cy='40' r='1'/>
        <circle cx='55' cy='30' r='1'/><circle cx='40' cy='30' r='1'/>
        <circle cx='40' cy='45' r='1'/><circle cx='25' cy='45' r='1'/>
        <circle cx='25' cy='30' r='1'/>
      </g>
    </svg>""",
    "hashi": """<svg viewBox='0 0 100 56' xmlns='http://www.w3.org/2000/svg'>
      <rect width='100' height='56' fill='#050507'/>
      <g stroke='#e8e4d4' stroke-width='1.2'>
        <line x1='25' y1='15' x2='70' y2='15'/><line x1='25' y1='17' x2='70' y2='17'/>
        <line x1='25' y1='15' x2='25' y2='42'/>
        <line x1='70' y1='15' x2='70' y2='42'/><line x1='72' y1='15' x2='72' y2='42'/>
        <line x1='25' y1='42' x2='70' y2='42'/>
      </g>
      <g fill='#0a0a0c' stroke='#d9b66c' stroke-width='1.5'>
        <circle cx='25' cy='15' r='5'/><circle cx='70' cy='15' r='5'/>
        <circle cx='25' cy='42' r='5'/><circle cx='70' cy='42' r='5'/>
      </g>
      <g fill='#e8e4d4' font-family='monospace' font-size='6' text-anchor='middle'>
        <text x='25' y='17'>3</text><text x='70' y='17'>4</text>
        <text x='25' y='44'>2</text><text x='70' y='44'>3</text>
      </g>
    </svg>""",
    "sudoku": """<svg viewBox='0 0 100 56' xmlns='http://www.w3.org/2000/svg'>
      <rect width='100' height='56' fill='#050507'/>
      <g stroke='#2a2a32' stroke-width='0.5' fill='none'>
        <g transform='translate(34,8)'>
          <rect width='33' height='40' fill='#0a0a0c' stroke='#d9b66c' stroke-width='1'/>
          <line x1='11' y1='0' x2='11' y2='40'/>
          <line x1='22' y1='0' x2='22' y2='40' stroke='#d9b66c'/>
          <line x1='11' y1='0' x2='11' y2='40' stroke='#d9b66c'/>
          <line x1='0' y1='13' x2='33' y2='13'/>
          <line x1='0' y1='26' x2='33' y2='26' stroke='#d9b66c'/>
        </g>
      </g>
      <g fill='#e8e4d4' font-family='monospace' font-size='7' text-anchor='middle'>
        <text x='40' y='18'>5</text><text x='51' y='18'>3</text><text x='62' y='18'>·</text>
        <text x='40' y='31'>·</text><text x='51' y='31'>·</text><text x='62' y='31'>4</text>
        <text x='40' y='44'>9</text><text x='51' y='44'>·</text><text x='62' y='44'>1</text>
      </g>
    </svg>""",
    "akari": """<svg viewBox='0 0 100 56' xmlns='http://www.w3.org/2000/svg'>
      <rect width='100' height='56' fill='#050507'/>
      <g transform='translate(30,8)'>
        <g fill='#e8e4d4'>
          <rect x='0' y='0' width='40' height='40' opacity='0.06'/>
        </g>
        <g fill='#0a0a0c'>
          <rect x='8' y='0' width='8' height='8'/>
          <rect x='24' y='8' width='8' height='8'/>
          <rect x='0' y='24' width='8' height='8'/>
          <rect x='32' y='32' width='8' height='8'/>
        </g>
        <g fill='#e8e4d4' font-family='monospace' font-size='5' text-anchor='middle'>
          <text x='12' y='6'>2</text><text x='28' y='14'>1</text><text x='4' y='30'>0</text><text x='36' y='38'>2</text>
        </g>
        <g fill='#d9b66c'>
          <circle cx='4' cy='12' r='2.5'/><circle cx='20' cy='4' r='2.5'/>
          <circle cx='36' cy='20' r='2.5'/><circle cx='12' cy='28' r='2.5'/>
          <circle cx='28' cy='36' r='2.5'/>
        </g>
      </g>
    </svg>""",
    "shikaku": """<svg viewBox='0 0 100 56' xmlns='http://www.w3.org/2000/svg'>
      <rect width='100' height='56' fill='#050507'/>
      <g transform='translate(28,6)' fill='none' stroke-width='1.4'>
        <rect width='44' height='44' fill='#0a0a0c' stroke='#2a2a32'/>
        <rect x='0' y='0' width='22' height='14' stroke='#d9b66c'/>
        <rect x='22' y='0' width='22' height='22' stroke='#d9b66c'/>
        <rect x='0' y='14' width='14' height='30' stroke='#d9b66c'/>
        <rect x='14' y='22' width='14' height='22' stroke='#d9b66c'/>
        <rect x='28' y='22' width='16' height='22' stroke='#d9b66c'/>
      </g>
      <g fill='#e8e4d4' font-family='monospace' font-size='6' text-anchor='middle'>
        <text x='39' y='15'>6</text><text x='61' y='17'>8</text>
        <text x='35' y='32'>6</text><text x='49' y='38'>6</text><text x='64' y='38'>6</text>
        <text x='35' y='49'></text>
      </g>
    </svg>""",
    "starbattle": """<svg viewBox='0 0 100 56' xmlns='http://www.w3.org/2000/svg'>
      <rect width='100' height='56' fill='#050507'/>
      <g transform='translate(30,8)'>
        <rect width='40' height='40' fill='#0a0a0c' stroke='#2a2a32'/>
        <g stroke='#2a2a32' stroke-width='0.4'>
          <line x1='10' y1='0' x2='10' y2='40'/><line x1='20' y1='0' x2='20' y2='40'/><line x1='30' y1='0' x2='30' y2='40'/>
          <line x1='0' y1='10' x2='40' y2='10'/><line x1='0' y1='20' x2='40' y2='20'/><line x1='0' y1='30' x2='40' y2='30'/>
        </g>
        <g stroke='#d9b66c' stroke-width='1' fill='none'>
          <path d='M0,15 L15,15 L15,0'/>
          <path d='M25,0 L25,20 L40,20'/>
          <path d='M0,25 L25,25 L25,40'/>
        </g>
        <g fill='#d9b66c'>
          <polygon points='5,5 6.2,8 9.5,8 7,10 8,13 5,11 2,13 3,10 0.5,8 3.8,8'/>
          <polygon points='25,15 26.2,18 29.5,18 27,20 28,23 25,21 22,23 23,20 20.5,18 23.8,18'/>
          <polygon points='15,35 16.2,38 19.5,38 17,40 18,43 15,41 12,43 13,40 10.5,38 13.8,38'/>
          <polygon points='35,5 36.2,8 39.5,8 37,10 38,13 35,11 32,13 33,10 30.5,8 33.8,8'/>
        </g>
      </g>
    </svg>""",
    "yajilin": """<svg viewBox='0 0 100 56' xmlns='http://www.w3.org/2000/svg'>
      <rect width='100' height='56' fill='#050507'/>
      <g transform='translate(28,6)'>
        <rect width='44' height='44' fill='#0a0a0c' stroke='#2a2a32'/>
        <g stroke='#2a2a32' stroke-width='0.4'>
          <line x1='11' y1='0' x2='11' y2='44'/><line x1='22' y1='0' x2='22' y2='44'/><line x1='33' y1='0' x2='33' y2='44'/>
          <line x1='0' y1='11' x2='44' y2='11'/><line x1='0' y1='22' x2='44' y2='22'/><line x1='0' y1='33' x2='44' y2='33'/>
        </g>
        <g fill='#0a0a0c' stroke='#2a2a32' stroke-width='0.4'>
          <rect x='22' y='0' width='11' height='11'/>
          <rect x='0' y='22' width='11' height='11'/>
          <rect x='33' y='33' width='11' height='11'/>
        </g>
        <g fill='#e8e4d4' font-family='monospace' font-size='5' text-anchor='middle'>
          <text x='27.5' y='8'>2→</text>
          <text x='5.5' y='29'>1↓</text>
        </g>
        <g stroke='#d9b66c' stroke-width='1.6' fill='none' stroke-linejoin='round'>
          <path d='M5.5,5.5 L16.5,5.5 L16.5,16.5 L27.5,16.5 L27.5,27.5 L38.5,27.5 L38.5,16.5 L27.5,16.5'/>
          <path d='M5.5,16.5 L5.5,38.5 L27.5,38.5'/>
        </g>
      </g>
    </svg>""",
    "kurodoko": """<svg viewBox='0 0 100 56' xmlns='http://www.w3.org/2000/svg'>
      <rect width='100' height='56' fill='#050507'/>
      <g transform='translate(28,6)'>
        <rect width='44' height='44' fill='#0a0a0c' stroke='#2a2a32'/>
        <g stroke='#2a2a32' stroke-width='0.4'>
          <line x1='11' y1='0' x2='11' y2='44'/><line x1='22' y1='0' x2='22' y2='44'/><line x1='33' y1='0' x2='33' y2='44'/>
          <line x1='0' y1='11' x2='44' y2='11'/><line x1='0' y1='22' x2='44' y2='22'/><line x1='0' y1='33' x2='44' y2='33'/>
        </g>
        <g fill='#1a1a22'>
          <rect x='11' y='0' width='11' height='11'/>
          <rect x='33' y='11' width='11' height='11'/>
          <rect x='0' y='22' width='11' height='11'/>
          <rect x='22' y='33' width='11' height='11'/>
        </g>
        <g fill='#e8e4d4' font-family='monospace' font-size='6' text-anchor='middle'>
          <text x='5.5' y='8'>4</text>
          <text x='27.5' y='19'>5</text>
          <text x='16.5' y='30'>3</text>
          <text x='38.5' y='41'>4</text>
        </g>
        <g fill='#d9b66c'>
          <circle cx='5.5' cy='5.5' r='1.2'/><circle cx='27.5' cy='16.5' r='1.2'/>
          <circle cx='16.5' cy='27.5' r='1.2'/><circle cx='38.5' cy='38.5' r='1.2'/>
        </g>
      </g>
    </svg>""",
    "aquarium": """<svg viewBox='0 0 100 56' xmlns='http://www.w3.org/2000/svg'>
      <rect width='100' height='56' fill='#050507'/>
      <g transform='translate(26,8)'>
        <rect width='48' height='40' fill='#0a0a0c' stroke='#d9b66c' stroke-width='1'/>
        <g stroke='#d9b66c' stroke-width='0.8' fill='none'>
          <path d='M16,0 L16,24 L32,24 L32,0'/>
          <path d='M0,16 L16,16'/>
          <path d='M32,12 L48,12'/>
          <path d='M16,32 L48,32'/>
        </g>
        <g fill='#3a6f9c' opacity='0.85'>
          <rect x='0' y='24' width='16' height='16'/>
          <rect x='16' y='28' width='16' height='12'/>
          <rect x='32' y='20' width='16' height='20'/>
        </g>
        <g fill='#e8e4d4' font-family='monospace' font-size='5' text-anchor='middle'>
          <text x='8' y='-1'>2</text><text x='24' y='-1'>3</text><text x='40' y='-1'>4</text>
          <text x='-3' y='10'>1</text><text x='-3' y='22'>2</text><text x='-3' y='34'>3</text>
        </g>
      </g>
    </svg>""",
    "hitori": """<svg viewBox='0 0 100 56' xmlns='http://www.w3.org/2000/svg'>
      <rect width='100' height='56' fill='#050507'/>
      <g transform='translate(28,6)'>
        <rect width='44' height='44' fill='#0a0a0c' stroke='#2a2a32'/>
        <g stroke='#2a2a32' stroke-width='0.4'>
          <line x1='11' y1='0' x2='11' y2='44'/><line x1='22' y1='0' x2='22' y2='44'/><line x1='33' y1='0' x2='33' y2='44'/>
          <line x1='0' y1='11' x2='44' y2='11'/><line x1='0' y1='22' x2='44' y2='22'/><line x1='0' y1='33' x2='44' y2='33'/>
        </g>
        <g fill='#1a1a22'>
          <rect x='11' y='0' width='11' height='11'/>
          <rect x='33' y='11' width='11' height='11'/>
          <rect x='0' y='22' width='11' height='11'/>
          <rect x='22' y='33' width='11' height='11'/>
        </g>
        <g fill='#e8e4d4' font-family='monospace' font-size='6' text-anchor='middle'>
          <text x='5.5' y='8'>2</text><text x='16.5' y='8'>3</text><text x='27.5' y='8'>1</text>
          <text x='5.5' y='19'>4</text><text x='16.5' y='19'>2</text><text x='38.5' y='19'>3</text>
          <text x='16.5' y='30'>1</text><text x='27.5' y='30'>4</text><text x='38.5' y='30'>2</text>
          <text x='5.5' y='41'>3</text><text x='16.5' y='41'>1</text><text x='38.5' y='41'>4</text>
        </g>
        <g fill='#e8e4d4' font-family='monospace' font-size='6' text-anchor='middle'>
          <text x='16.5' y='8' fill='#1a1a22'>3</text>
          <text x='38.5' y='19' fill='#1a1a22'>3</text>
          <text x='5.5' y='30' fill='#1a1a22'>4</text>
          <text x='27.5' y='41' fill='#1a1a22'>4</text>
        </g>
      </g>
    </svg>""",
}

LANDING_TMPL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Arcade — Eight Constraint-Deduction Puzzles</title>
<style>{css}</style>
</head>
<body>
<div class="wrap">
  <header class="site">
    <h1>Arcade</h1>
    <p class="lede">Eight constraint-deduction puzzle games. Each shipped with verified correctness, difficulty calibration, legibility, and soft-lock fuzz testing. No accounts, no ads, no tracking — just open and play.</p>
  </header>
  <main>
    <div class="grid">
{cards}
    </div>
  </main>
  <footer class="site">
    <p>Open source · MIT licensed · <a href="https://github.com/brotatotes/studio-arcade">source on GitHub</a></p>
  </footer>
</div>
</body>
</html>
"""

CARD_TMPL = """      <div class="card">
        <div class="thumb">{thumb}</div>
        <a class="title" href="{slug}/">{title}</a>
        <p class="tagline">{tagline}</p>
        <div class="actions">
          <a href="{slug}/">Play →</a>
          <a href="{slug}/about.html">About</a>
        </div>
      </div>"""

ABOUT_TMPL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title} — Arcade</title>
<style>{css}</style>
</head>
<body>
<div class="wrap">
  <a class="back" href="../">← arcade</a>
  <article>
    <h1>{title}</h1>
    <p class="tagline" style="color:var(--fg-dim);font-size:1.05rem;">{tagline}</p>

    <a class="play-cta" href="./">▶ Play {title}</a>

    <h2>About</h2>
    {description_html}

    <h2>How to play</h2>
    <p>{rules}</p>

    <h2>Features</h2>
    <ul>
{features}
    </ul>

    <p style="margin-top:2.5rem;"><a href="../">← back to arcade</a></p>
  </article>
  <footer class="site">
    <p>Open source · MIT licensed · <a href="https://github.com/brotatotes/studio-arcade">source on GitHub</a></p>
  </footer>
</div>
</body>
</html>
"""

# Per-game playable wrapper — adds a small "← arcade" link above the embedded game iframe
PLAY_WRAPPER_BAR = """<style>
#arcade-bar { position: fixed; top: 0; left: 0; right: 0; z-index: 9999; background: rgba(10,10,12,0.92); color: #e8e4d4; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 6px 14px; font-size: 13px; border-bottom: 1px solid #2a2a32; backdrop-filter: blur(6px); }
#arcade-bar a { color: #d9b66c; text-decoration: none; margin-right: 16px; }
#arcade-bar a:hover { text-decoration: underline; }
body { padding-top: 28px !important; }
</style>
<div id="arcade-bar"><a href="../">← arcade</a><a href="about.html">about this game</a></div>"""


def render_description(desc):
    paras = [p.strip() for p in desc.split("\n\n") if p.strip()]
    return "\n    ".join(f"<p>{p}</p>" for p in paras)


def build_landing(manifest):
    cards = []
    for g in manifest["games"]:
        thumb = THUMBS.get(g["slug"], "")
        cards.append(CARD_TMPL.format(
            slug=g["slug"], title=g["title"], tagline=g["tagline"], thumb=thumb,
        ))
    return LANDING_TMPL.format(css=CSS, cards="\n".join(cards))


def build_about(g):
    features = "\n".join(f"      <li>{f}</li>" for f in g["features"])
    return ABOUT_TMPL.format(
        css=CSS, title=g["title"], tagline=g["tagline"],
        description_html=render_description(g["description"]),
        rules=g["rules"], features=features,
    )


def inject_arcade_bar(index_html_path):
    """Insert the arcade nav bar into the game's index.html, idempotent."""
    p = Path(index_html_path)
    html = p.read_text()
    if "id=\"arcade-bar\"" in html:
        return
    # Inject right after <body> open tag
    if "<body>" in html:
        html = html.replace("<body>", "<body>\n" + PLAY_WRAPPER_BAR, 1)
    else:
        html = PLAY_WRAPPER_BAR + html
    p.write_text(html)


def copy_dist(slug, source_dist):
    target = REPO / slug
    target.mkdir(exist_ok=True)
    for fname in ("index.html", "bundle.js"):
        src = source_dist / fname
        if src.exists():
            shutil.copy2(src, target / fname)
    # Also copy README.html if present (rename to game-readme.html to avoid clash)
    src_readme = source_dist / "README.html"
    if src_readme.exists():
        shutil.copy2(src_readme, target / "game-readme.html")
    inject_arcade_bar(target / "index.html")


def main():
    manifest = json.loads(MANIFEST.read_text())

    copy_for = None
    source_dist = None
    if "--copy-dist" in sys.argv:
        i = sys.argv.index("--copy-dist")
        copy_for = sys.argv[i + 1]
        source_dist = Path(sys.argv[i + 2])

    if copy_for:
        copy_dist(copy_for, source_dist)
        print(f"[copy] {copy_for} ← {source_dist}")

    # Write landing
    (REPO / "index.html").write_text(build_landing(manifest))
    print("[gen] index.html")

    # Write per-game about pages
    for g in manifest["games"]:
        target = REPO / g["slug"]
        target.mkdir(exist_ok=True)
        (target / "about.html").write_text(build_about(g))
        print(f"[gen] {g['slug']}/about.html")


if __name__ == "__main__":
    main()
