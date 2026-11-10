"""Generates cyber-themed SVG stat cards for the GitHub profile README.
Run by .github/workflows/stats.yml using the built-in GITHUB_TOKEN (no secrets needed)."""
import os, json, datetime, urllib.request
from xml.sax.saxutils import escape

USER = os.environ.get("GH_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "Itsgauravvv"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
C, M, P, G = "#00F0FF", "#FF2BD6", "#7B2FFF", "#39FF14"
NEON = [C, M, G, "#B388FF", "#FFD60A", "#FF6B35"]
MONO = "'Courier New',Consolas,monospace"

QUERY = """
query($login:String!){ user(login:$login){
  name followers{totalCount}
  pullRequests{totalCount} issues{totalCount}
  repositories(ownerAffiliations:OWNER,isFork:false,first:100,orderBy:{field:PUSHED_AT,direction:DESC}){
    totalCount
    nodes{ stargazerCount languages(first:10,orderBy:{field:SIZE,direction:DESC}){ edges{ size node{ name } } } }
  }
  contributionsCollection{
    totalCommitContributions totalPullRequestContributions totalIssueContributions
    contributionCalendar{ totalContributions weeks{ contributionDays{ date contributionCount } } }
  }
}}"""

def fetch():
    if os.environ.get("MOCK"):
        import random
        random.seed(3)
        start = datetime.date.today() - datetime.timedelta(days=364)
        start -= datetime.timedelta(days=(start.weekday() + 1) % 7)
        weeks, d = [], start
        while d <= datetime.date.today():
            days = []
            for _ in range(7):
                if d <= datetime.date.today():
                    days.append({"date": d.isoformat(), "contributionCount": random.choice([0,0,0,1,2,3,5,8,12])})
                d += datetime.timedelta(days=1)
            weeks.append({"contributionDays": days})
        return {"name": "Mock", "followers": {"totalCount": 12}, "pullRequests": {"totalCount": 7}, "issues": {"totalCount": 3},
                "repositories": {"totalCount": 24, "nodes": [{"stargazerCount": 5, "languages": {"edges": [
                    {"size": 5000, "node": {"name": "Python"}}, {"size": 3000, "node": {"name": "C++"}},
                    {"size": 2000, "node": {"name": "TypeScript"}}, {"size": 900, "node": {"name": "HTML"}},
                    {"size": 500, "node": {"name": "CSS"}}, {"size": 300, "node": {"name": "Jupyter Notebook"}}]}}]},
                "contributionsCollection": {"totalCommitContributions": 310, "totalPullRequestContributions": 7, "totalIssueContributions": 3,
                                            "contributionCalendar": {"totalContributions": 420, "weeks": weeks}}}
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "User-Agent": "cyber-stats"})
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(data["errors"])
    return data["data"]["user"]

def frame(w, h, title, inner):
    peri = 2 * (w + h)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#05060f"/><stop offset="1" stop-color="#130628"/></linearGradient>
<filter id="g" x="-20%" y="-40%" width="140%" height="180%"><feGaussianBlur stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="14" fill="url(#bg)" stroke="{C}" stroke-opacity=".45" stroke-width="1.5"/>
<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="14" fill="none" stroke="{M}" stroke-width="2.5" stroke-dasharray="70 {peri}" filter="url(#g)"><animate attributeName="stroke-dashoffset" from="0" to="-{peri+70}" dur="7s" repeatCount="indefinite"/></rect>
<text x="24" y="34" font-family="{MONO}" font-size="15" font-weight="bold" fill="{C}" letter-spacing="3" filter="url(#g)">{escape(title)}</text>
<line x1="24" y1="46" x2="{w-24}" y2="46" stroke="{C}" stroke-opacity=".25"/>
{inner}
</svg>'''

def fade(i, step=0.12):
    return f'<animate attributeName="opacity" from="0" to="1" dur=".5s" begin="{i*step:.2f}s" fill="freeze"/>'

def num(n):
    return f"{n:,}"

def streaks(days):
    counts = [d["contributionCount"] for d in days]
    longest = run = 0
    for c in counts:
        run = run + 1 if c > 0 else 0
        longest = max(longest, run)
    cur, i = 0, len(counts) - 1
    if i >= 0 and counts[i] == 0:
        i -= 1  # today not counted yet
    while i >= 0 and counts[i] > 0:
        cur += 1
        i -= 1
    return cur, longest

def build(u):
    cc = u["contributionsCollection"]
    cal = cc["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    cur, longest = streaks(days)
    repos = u["repositories"]["nodes"]
    stars = sum(r["stargazerCount"] for r in repos)

    # stats card
    rows = [("Contributions (12 mo)", cal["totalContributions"], C), ("Commits (12 mo)", cc["totalCommitContributions"], M),
            ("Pull requests", u["pullRequests"]["totalCount"], G), ("Issues", u["issues"]["totalCount"], "#B388FF"),
            ("Stars earned", stars, "#FFD60A"), ("Public repos", u["repositories"]["totalCount"], C), ("Followers", u["followers"]["totalCount"], M)]
    inner = ""
    for i, (lab, val, col) in enumerate(rows):
        y = 74 + i * 24
        inner += (f'<g opacity="0">{fade(i)}<circle cx="32" cy="{y-5}" r="3.5" fill="{col}" filter="url(#g)"/>'
                  f'<text x="46" y="{y}" font-family="{MONO}" font-size="14" fill="#C8D6E5">{escape(lab)}</text>'
                  f'<text x="471" y="{y}" text-anchor="end" font-family="{MONO}" font-size="15" font-weight="bold" fill="{col}">{num(val)}</text></g>')
    open(f"{OUT}/stats.svg", "w").write(frame(495, 240, "// SYSTEM STATS", inner))

    # languages card
    tot = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            tot[e["node"]["name"]] = tot.get(e["node"]["name"], 0) + e["size"]
    top = sorted(tot.items(), key=lambda kv: -kv[1])[:6]
    s = sum(v for _, v in top) or 1
    inner = ""
    for i, (name, v) in enumerate(top):
        y = 76 + i * 27
        pct = v / s * 100
        bw = max(4, 230 * pct / 100)
        col = NEON[i % len(NEON)]
        inner += (f'<g>'
                  f'<text x="28" y="{y}" font-family="{MONO}" font-size="13" fill="#C8D6E5">{escape(name[:14])}</text>'
                  f'<rect x="150" y="{y-11}" width="230" height="10" rx="5" fill="#0d1226"/>'
                  f'<rect x="150" y="{y-11}" width="0" height="10" rx="5" fill="{col}" filter="url(#g)"><animate attributeName="width" from="0" to="{bw:.1f}" dur="1.2s" begin="{i*0.15:.2f}s" fill="freeze"/></rect>'
                  f'<text x="471" y="{y}" text-anchor="end" font-family="{MONO}" font-size="13" font-weight="bold" fill="{col}">{pct:.1f}%</text></g>')
    open(f"{OUT}/languages.svg", "w").write(frame(495, 240, "// TOP LANGUAGES", inner))

    # streak card
    W = 1000
    cols = [(167, "TOTAL CONTRIBUTIONS", cal["totalContributions"], "last 12 months", C),
            (500, "CURRENT STREAK", cur, "days", M),
            (833, "LONGEST STREAK", longest, "days", G)]
    inner = ""
    for x, lab, val, sub, col in cols:
        inner += (f'<text x="{x}" y="112" text-anchor="middle" font-family="{MONO}" font-size="46" font-weight="bold" fill="#FFFFFF" filter="url(#g)">{num(val)}</text>'
                  f'<text x="{x}" y="138" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{col}" letter-spacing="2">{lab}</text>'
                  f'<text x="{x}" y="158" text-anchor="middle" font-family="{MONO}" font-size="11" fill="#7F8FA9">{sub}</text>')
    inner += (f'<circle cx="500" cy="100" r="58" fill="none" stroke="{M}" stroke-width="3" stroke-opacity=".9" stroke-dasharray="364" stroke-dashoffset="364" transform="rotate(-90 500 100)" filter="url(#g)">'
              f'<animate attributeName="stroke-dashoffset" values="364;0;0;364" keyTimes="0;.4;.8;1" dur="6s" repeatCount="indefinite"/></circle>')
    inner += f'<line x1="333" y1="70" x2="333" y2="150" stroke="{C}" stroke-opacity=".2"/><line x1="667" y1="70" x2="667" y2="150" stroke="{C}" stroke-opacity=".2"/>'
    open(f"{OUT}/streak.svg", "w").write(frame(W, 180, "// STREAK TRACKER", inner))

    # contribution heatmap
    weeks = cal["weeks"]
    mx = max([d["contributionCount"] for d in days] + [1])
    def color(c):
        if c == 0: return "#0d1226"
        r = c / mx
        return "#0b4f5c" if r < .25 else "#0097a7" if r < .5 else C if r < .75 else M
    pitch, cell = 17, 14
    W = 26 * 2 + len(weeks) * pitch
    inner = ""
    for wi, wk in enumerate(weeks):
        for d in wk["contributionDays"]:
            dt = datetime.date.fromisoformat(d["date"])
            row = (dt.weekday() + 1) % 7
            c = d["contributionCount"]
            inner += (f'<rect x="{26+wi*pitch}" y="{62+row*pitch}" width="{cell}" height="{cell}" rx="3" fill="{color(c)}" opacity="0">'
                      f'<animate attributeName="opacity" from="0" to="1" dur=".4s" begin="{wi*0.04:.2f}s" fill="freeze"/>'
                      f'<title>{d["date"]}: {c}</title></rect>')
    ly = 62 + 7 * pitch + 14
    inner += f'<text x="26" y="{ly+10}" font-family="{MONO}" font-size="11" fill="#7F8FA9">less</text>'
    for k, col in enumerate(["#0d1226", "#0b4f5c", "#0097a7", C, M]):
        inner += f'<rect x="{62+k*18}" y="{ly}" width="12" height="12" rx="3" fill="{col}"/>'
    inner += f'<text x="{62+5*18+4}" y="{ly+10}" font-family="{MONO}" font-size="11" fill="#7F8FA9">more</text>'
    open(f"{OUT}/heatmap.svg", "w").write(frame(W, ly + 34, "// CONTRIBUTION MATRIX", inner))

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    build(fetch())
    print("cards written to", OUT)
