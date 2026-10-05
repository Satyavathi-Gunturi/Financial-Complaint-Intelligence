"""Generate editable draw.io pages and matching SVG architecture views.

Symbols are embedded filled SVG icons, one editable object per icon. Cards,
labels, boundaries and routed connectors are native draw.io objects. No external
image dependencies are needed. The generator uses Python's standard library.
"""

import html
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote

OUT = Path(__file__).resolve().parents[2] / "assets" / "diagrams"
NAVY = "#122B45"
TEAL = "#087F8C"
BLUE = "#3466AC"
GOLD = "#B47A13"
PURPLE = "#7555A1"
RED = "#B84C48"
GRAY = "#63758A"
ICONS = {
    "cloud": '<path d="M8 30h26a9 9 0 0 0 1-18 13 13 0 0 0-24-1A10 10 0 0 0 8 30z"/>',
    "clock": '<circle cx="22" cy="22" r="17"/><path d="M22 10v13l9 5" fill="none" stroke="white" stroke-width="3"/>',
    "database": '<ellipse cx="22" cy="10" rx="16" ry="6"/><path d="M6 10v23c0 8 32 8 32 0V10c-8 7-24 7-32 0z"/><path d="M7 21c8 6 22 6 30 0" fill="none" stroke="white" stroke-width="2"/>',
    "process": '<path d="M11 7h22l10 15-10 15H11L1 22z"/><path d="M14 22h15m-5-6 6 6-6 6" fill="none" stroke="white" stroke-width="3"/>',
    "shield": '<path d="M22 3 39 9v12c0 11-8 17-17 21C13 38 5 32 5 21V9z"/><path d="m12 22 7 7 13-15" fill="none" stroke="white" stroke-width="3"/>',
    "files": '<path d="M5 8h25v31H5z"/><path d="M13 3h22l6 7v24h-8V15H13z"/><path d="M11 19h12m-12 7h12m-12 6h9" fill="none" stroke="white" stroke-width="2"/>',
    "branch": '<path d="M11 10v24m0-12h15c6 0 7-5 7-10" fill="none" stroke="currentColor" stroke-width="6"/><circle cx="11" cy="7" r="6"/><circle cx="11" cy="36" r="6"/><circle cx="33" cy="7" r="6"/>',
    "dashboard": '<rect x="3" y="5" width="38" height="32" rx="4"/><path d="M7 12h30M14 33V23m8 10V17m8 16V21" fill="none" stroke="white" stroke-width="3"/>',
    "person": '<circle cx="22" cy="12" r="8"/><path d="M6 40v-7c0-16 32-16 32 0v7z"/>',
    "code": '<rect x="2" y="5" width="40" height="34" rx="4"/><path d="m15 15-8 7 8 7m14-14 8 7-8 7m-5-17-4 22" fill="none" stroke="white" stroke-width="2.5"/>',
    "search": '<circle cx="18" cy="18" r="13"/><path d="m27 27 13 13" fill="none" stroke="currentColor" stroke-width="7"/><circle cx="18" cy="18" r="8" fill="white"/>',
    "stop": '<path d="M13 3h18l12 12v17L31 43H13L1 31V15z"/><path d="m14 14 16 16m0-16L14 30" fill="none" stroke="white" stroke-width="3"/>',
    "manifest": '<path d="M8 3h21l9 10v28H8z"/><path d="M28 3v12h10M14 22h18m-18 7h18m-18 7h12" fill="none" stroke="white" stroke-width="2"/>',
}


def esc(s):
    return html.escape(str(s), quote=True)


def icon_svg(name, color):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="44" height="44" viewBox="0 0 44 44"><g fill="{color}" color="{color}">{ICONS[name]}</g></svg>'


class Page:
    def __init__(self, stem, title, subtitle, scope, width=1700, height=1160):
        self.stem, self.title, self.width, self.height = stem, title, width, height
        self.svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img"><title>{esc(title)}</title><desc>{esc(subtitle)}</desc>',
            '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto-start-reverse"><path d="M0 0 8 4 0 8z" fill="#63758A"/></marker></defs>',
            f'<rect width="{width}" height="{height}" fill="#F4F7FB"/>',
        ]
        self.model = ET.Element(
            "mxGraphModel",
            grid="1",
            gridSize="10",
            page="1",
            pageWidth=str(width),
            pageHeight=str(height),
            shadow="0",
        )
        self.root = ET.SubElement(self.model, "root")
        ET.SubElement(self.root, "mxCell", id="0")
        ET.SubElement(self.root, "mxCell", id="1", parent="0")
        self.count = 0
        self.box("header", 0, 0, width, 160, NAVY, NAVY, 0)
        self.text(
            54,
            30,
            "FINANCIAL COMPLAINT INTELLIGENCE  /  ENGINEERING DESIGN",
            14,
            "#72D5D0",
            True,
        )
        self.text(54, 68, title, 32, "#FFFFFF", True)
        self.text(54, 113, subtitle, 16, "#D9E5F0")
        self.text(width - 410, 30, "DESIGN BASELINE  ·  05 OCT 2026", 12, "#D9E5F0")
        self.text(54, 181, scope, 14, GRAY)

    def cell(self, ident, x, y, w, h, value, style, parent="1"):
        c = ET.SubElement(
            self.root,
            "mxCell",
            id=ident,
            value=value,
            style=style,
            vertex="1",
            parent=parent,
        )
        ET.SubElement(
            c,
            "mxGeometry",
            x=str(x),
            y=str(y),
            width=str(w),
            height=str(h),
            **{"as": "geometry"},
        )
        return c

    def box(self, ident, x, y, w, h, fill, stroke, radius=14, dashed=False):
        dash = ' stroke-dasharray="7 5"' if dashed else ""
        self.svg.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"{dash}/>'
        )
        self.cell(
            ident,
            x,
            y,
            w,
            h,
            "",
            f"rounded={int(radius > 0)};arcSize=8;fillColor={fill};strokeColor={stroke};dashed={int(dashed)};",
        )

    def text(self, x, y, s, size=14, color=NAVY, bold=False, width=1500):
        self.count += 1
        self.svg.append(
            f'<text x="{x}" y="{y + size}" font-family="Arial, sans-serif" font-size="{size}" fill="{color}" font-weight="{700 if bold else 400}">{esc(s)}</text>'
        )
        self.cell(
            f"text{self.count}",
            x,
            y,
            width,
            size + 8,
            s,
            f"text;html=0;align=left;verticalAlign=top;spacing=0;whiteSpace=wrap;overflow=hidden;fontFamily=Arial;fontSize={size};fontColor={color};fontStyle={int(bold)};strokeColor=none;fillColor=none;",
        )

    def lane(self, ident, x, y, w, h, label, sub, color=TEAL, dashed=False):
        self.box(ident, x, y, w, h, "#EAF0F6", "#BBCAD8", 16, dashed)
        self.text(x + 18, y + 14, label, 15, color, True, w - 36)
        self.text(x + 18, y + 39, sub, 12, GRAY, False, w - 36)

    def card(
        self,
        ident,
        x,
        y,
        w,
        h,
        title,
        typ,
        lines,
        icon="process",
        color=TEAL,
        planned=False,
    ):
        before = set(c.attrib["id"] for c in self.root)
        self.box(ident, x, y, w, h, "#FFFFFF", "#C1CFDD", 12, planned)
        self.svg.append(
            f'<rect x="{x}" y="{y + 14}" width="5" height="{h - 28}" rx="2" fill="{color}"/>'
        )
        self.cell(
            ident + "accent",
            x,
            y + 14,
            5,
            h - 28,
            "",
            f"rounded=1;fillColor={color};strokeColor=none;",
        )
        self.box(ident + "tile", x + 16, y + 18, 54, 54, "#EEF3F8", "#EEF3F8", 10)
        symbol = icon_svg(icon, color)
        self.svg.append(
            f'<g transform="translate({x + 21},{y + 23})">{symbol.replace("<svg", "<svg", 1)}</g>'
        )
        data = quote(symbol, safe="")
        self.cell(
            ident + "icon",
            x + 21,
            y + 23,
            44,
            44,
            "",
            f"shape=image;imageAspect=1;aspect=fixed;image=data:image/svg+xml,{data};",
        )
        self.text(x + 82, y + 18, title, 17, NAVY, True, w - 96)
        self.text(x + 82, y + 44, typ, 11, color, True, w - 96)
        for i, line in enumerate(lines):
            self.text(x + 20, y + 87 + i * 23, line, 13, "#40566C", False, w - 40)

        for child in self.root:
            if child.attrib["id"] not in before and child.attrib["id"] != ident:
                child.set("parent", ident)
                geo = child.find("mxGeometry")
                geo.set("x", str(float(geo.get("x")) - x))
                geo.set("y", str(float(geo.get("y")) - y))

    def edge(self, ident, source, target, pts, label, lx, ly, dashed=False, color=GRAY):
        path = "M" + " L".join(f"{x} {y}" for x, y in pts)
        self.svg.append(
            f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2" marker-end="url(#arrow)"'
            + (' stroke-dasharray="6 5"' if dashed else "")
            + "/>"
        )
        c = ET.SubElement(
            self.root,
            "mxCell",
            id=ident,
            value="",
            edge="1",
            parent="1",
            source=source,
            target=target,
            style=f"edgeStyle=none;rounded=0;endArrow=block;endFill=1;strokeWidth=2;strokeColor={color};dashed={int(dashed)};",
        )
        g = ET.SubElement(c, "mxGeometry", relative="1", **{"as": "geometry"})
        ET.SubElement(
            g, "mxPoint", x=str(pts[0][0]), y=str(pts[0][1]), **{"as": "sourcePoint"}
        )
        ET.SubElement(
            g, "mxPoint", x=str(pts[-1][0]), y=str(pts[-1][1]), **{"as": "targetPoint"}
        )
        a = ET.SubElement(g, "Array", **{"as": "points"})
        for x, y in pts[1:-1]:
            ET.SubElement(a, "mxPoint", x=str(x), y=str(y))
        self.text(lx, ly, label, 11, color, False, 400)

    def note(self, ident, x, y, w, h, title, lines, color=TEAL, planned=False):
        self.box(ident, x, y, w, h, "#FFFFFF", "#C1CFDD", dashed=planned)
        self.text(x + 18, y + 14, title, 14, color, True, w - 36)
        for i, line in enumerate(lines):
            self.text(x + 18, y + 42 + i * 21, line, 12, GRAY, False, w - 36)

    def finish(self, extra=""):
        y = self.height - 65
        self.text(
            54,
            y,
            "LEGEND  ·  Filled icons = component type  |  Solid cards = implemented  |  Dashed cards = planned",
            12,
            GRAY,
        )
        self.text(
            54,
            y + 23,
            "Solid arrows = data / publication flow  |  Dashed arrows = control / development flow  |  "
            + extra,
            12,
            GRAY,
        )
        self.svg.append("</svg>")
        (OUT / (self.stem + ".svg")).write_text("".join(self.svg))
        return self


def bundle(stem, pages):
    mx = ET.Element("mxfile", host="app.diagrams.net", version="24.7.17")
    for p in pages:
        d = ET.SubElement(mx, "diagram", id=p.stem, name=p.title)
        d.append(p.model)
    ET.ElementTree(mx).write(
        OUT / (stem + ".drawio"), encoding="utf-8", xml_declaration=True
    )


# HLSD: deployment boundaries and container responsibilities, not SQL internals.
p = Page(
    "system-architecture",
    "HLSD 01  /  Platform architecture",
    "Container and data-flow view · Public archives to validated analytics · Future AI is explicitly separated",
    "SCOPE: External source, temporary processing boundary, release repository and live consumption",
)
p.lane(
    "external",
    45,
    225,
    325,
    590,
    "01  PUBLIC SOURCE",
    "External ownership · HTTPS",
    BLUE,
)
p.lane(
    "runner",
    410,
    225,
    800,
    590,
    "02  SCHEDULED DATA PLATFORM",
    "GitHub-hosted runner · temporary compute and storage",
)
p.lane(
    "delivery",
    1250,
    225,
    405,
    770,
    "03  RELEASE & CONSUMPTION",
    "GitHub + Streamlit Community Cloud",
    BLUE,
)
p.card(
    "source",
    65,
    445,
    285,
    150,
    "CFPB archives",
    "EXTERNAL SYSTEM / ZIP + CSV",
    ["Narrative-bearing complaint exports", "Release timing controlled by CFPB"],
    "cloud",
    BLUE,
)
p.card(
    "schedule",
    435,
    295,
    350,
    130,
    "Refresh orchestration",
    "WORKFLOW / GITHUB ACTIONS",
    ["Daily 11:23 UTC + manual force run"],
    "clock",
)
p.card(
    "cache",
    835,
    295,
    350,
    130,
    "Source identity & cache",
    "DATA STORE / ZIP + SHA-256",
    ["HTTP validators; disposable cache"],
    "files",
    BLUE,
)
p.card(
    "ingest",
    435,
    465,
    350,
    145,
    "Retention & ingestion",
    "COMPONENT / PYTHON + PANDAS",
    ["36 months by received date", "Chunking, provenance, ID precedence"],
    "process",
)
p.card(
    "warehouse",
    835,
    465,
    350,
    145,
    "Medallion warehouse",
    "DATA STORE / DUCKDB + DBT",
    ["Staging → silver → wide gold + star", "Complaint-level models; temporary DB"],
    "database",
    GOLD,
)
p.card(
    "quality",
    435,
    655,
    350,
    145,
    "Quality & export gate",
    "COMPONENT / DBT + PYTHON",
    [
        "126 tests; 18 additive totals reconcile",
        "Failures retain the published release",
    ],
    "shield",
)
p.card(
    "exports",
    835,
    655,
    350,
    145,
    "Serving data product",
    "FILES / PARQUET + JSON",
    ["Four independent aggregate grains", "One revision + validation manifest"],
    "files",
    GOLD,
)
p.card(
    "repo",
    1280,
    655,
    345,
    145,
    "Release repository",
    "SYSTEM / GITHUB BRANCH + PR",
    ["Merge commit respects branch rules", "All serving files published together"],
    "branch",
    BLUE,
)
p.card(
    "dashboard",
    1280,
    850,
    345,
    130,
    "Executive dashboard",
    "APPLICATION / STREAMLIT + DUCKDB",
    ["Six tabs; filters, comparisons, CSV"],
    "dashboard",
    TEAL,
)
p.edge("a", "source", "ingest", [(350, 520), (435, 520)], "HTTPS / ZIP", 352, 494)
p.edge(
    "b",
    "schedule",
    "ingest",
    [(610, 425), (610, 465)],
    "Triggers rebuild",
    620,
    437,
    True,
)
p.edge("c", "schedule", "cache", [(785, 355), (835, 355)], "Check", 789, 334, True)
p.edge(
    "cacheflow",
    "cache",
    "ingest",
    [(1010, 425), (1010, 445), (760, 445), (760, 465)],
    "Verified ZIP bytes",
    815,
    428,
)
p.edge("d", "ingest", "warehouse", [(785, 535), (835, 535)], "Rows", 790, 513)
p.edge(
    "e",
    "warehouse",
    "quality",
    [(1010, 610), (1010, 632), (610, 632), (610, 655)],
    "dbt build + reconciliation",
    690,
    613,
)
p.edge("f", "quality", "exports", [(785, 725), (835, 725)], "Pass", 790, 702)
p.edge("g", "exports", "repo", [(1185, 725), (1280, 725)], "Git / PR", 1190, 701)
p.edge(
    "h",
    "repo",
    "dashboard",
    [(1450, 800), (1450, 850)],
    "Merged files / redeploy",
    1462,
    816,
)
p.note(
    "recovery",
    45,
    850,
    555,
    130,
    "DEVELOPMENT / RECOVERY  ·  COLAB + DRIVE",
    [
        "Interactive notebook and manually saved complete checkpoint",
        "Separate from the runner; no Drive credentials in scheduled jobs",
        "Full DB backups remain outside the release repository",
    ],
    PURPLE,
)
p.note(
    "future",
    630,
    850,
    580,
    130,
    "PLANNED AI  ·  DETAIL HOSTING → SQL + RETRIEVAL + LLM",
    [
        "Persistent detailed-data service and model provider are undecided",
        "Aggregate Parquet contains metrics, not narrative text",
        "No deployed AI agent or semantic narrative index",
    ],
    PURPLE,
    planned=True,
)
p.note(
    "blocker",
    45,
    1008,
    1610,
    67,
    "CURRENT STATUS",
    [
        "Live dashboard uses the historical Nov 2022–Aug 2026 snapshot. First hosted ZIP download returned HTTP 403; rolling publication is blocked."
    ],
    RED,
)
p.finish("Icons are generic symbols, not vendor logos")

q = Page(
    "deployment-operations",
    "HLSD 02  /  Deployment & operations",
    "Execution environments · Ownership, permissions, storage lifetime and recovery",
    "SCOPE: Runtime boundaries and operational controls; no invented production cloud services",
)
q.lane(
    "buildenv",
    45,
    230,
    755,
    670,
    "BUILD ENVIRONMENT  /  GITHUB-HOSTED UBUNTU",
    "Execution owner: repository workflow",
)
q.lane(
    "serveenv",
    850,
    230,
    805,
    670,
    "SERVING ENVIRONMENT  /  STREAMLIT COMMUNITY CLOUD",
    "Deployment source: main branch",
    BLUE,
)
q.card(
    "runtime",
    75,
    315,
    335,
    185,
    "Python + dbt runtime",
    "COMPUTE / EPHEMERAL RUNNER",
    [
        "1 dbt thread; 2 GB memory limit",
        "Temporary spill directory",
        "12 GiB free-disk preflight",
        "120-minute workflow timeout",
    ],
    "process",
)
q.card(
    "working",
    445,
    315,
    325,
    185,
    "Working data",
    "STORAGE / RUNNER FILESYSTEM",
    [
        "data/source_cache: disposable ZIPs",
        "data/refresh_work: bronze + DB",
        "data/release: staged outputs",
        "No permanent detailed-data API",
    ],
    "database",
    GOLD,
)
q.card(
    "token",
    75,
    565,
    335,
    160,
    "Publication identity",
    "CONTROL / GITHUB_TOKEN",
    [
        "contents + pull-requests: write",
        "Repository rules remain authoritative",
        "Bot PR may await required review",
    ],
    "shield",
    BLUE,
)
q.card(
    "evidence",
    445,
    565,
    325,
    160,
    "Execution evidence",
    "ARTIFACT / ACTIONS LOGS",
    [
        "dbt results, manifest and build log",
        "14-day artifact retention",
        "Source failure stops publication",
    ],
    "manifest",
    PURPLE,
)
q.card(
    "main",
    890,
    315,
    335,
    185,
    "Main release revision",
    "FILES / GITHUB REPOSITORY",
    [
        "Four aggregate Parquet files",
        "reports/refresh_manifest.json",
        "Merge commit retains release history",
        "Large databases are not committed",
    ],
    "branch",
    BLUE,
)
q.card(
    "app",
    1260,
    315,
    355,
    185,
    "Streamlit app process",
    "APPLICATION / PYTHON",
    [
        "dashboard/app.py",
        "Read aggregate files with DuckDB",
        "Parameterized filters and queries",
        "No narrative text / LLM integration",
    ],
    "dashboard",
)
q.card(
    "cacheapp",
    890,
    565,
    335,
    160,
    "Serving query cache",
    "MEMORY / STREAMLIT CACHE",
    [
        "Key includes file mtime + size",
        "Independent queries per grain",
        "Rates computed from summed flags",
    ],
    "database",
    TEAL,
)
q.card(
    "leadership",
    1260,
    565,
    355,
    160,
    "Leadership & analysts",
    "PERSON / WEB BROWSER",
    [
        "Six-tab exploration",
        "K/M/B counts and hover labels",
        "Exact-value CSV downloads",
    ],
    "person",
    BLUE,
)
q.edge("localio", "runtime", "working", [(410, 405), (445, 405)], "I/O", 414, 383)
q.edge(
    "logs",
    "runtime",
    "evidence",
    [(245, 500), (245, 530), (608, 530), (608, 565)],
    "Build results + log files",
    355,
    509,
)
q.edge("deploy", "main", "app", [(1225, 405), (1260, 405)], "Checkout", 1228, 381)
q.edge(
    "query",
    "app",
    "cacheapp",
    [(1438, 500), (1438, 537), (1058, 537), (1058, 565)],
    "DuckDB read / cache identity",
    1110,
    516,
)
q.edge(
    "view",
    "app",
    "leadership",
    [(1438, 500), (1575, 500), (1575, 565)],
    "HTTPS UI",
    1490,
    530,
)
q.note(
    "limit",
    75,
    770,
    695,
    105,
    "FAILURE / RECOVERY",
    [
        "Any download, schema, dbt or export failure retains last good data.",
        "Main-branch runs supersede older runs; inspect Actions failures.",
        "Colab + Drive complete checkpoint is a separate manual recovery path.",
    ],
    RED,
)
q.note(
    "operating",
    890,
    770,
    725,
    105,
    "SERVICE LIMITS",
    [
        "Daily checks do not guarantee monthly CFPB releases or live coverage.",
        "GITHUB_TOKEN bot PRs do not trigger independent PR Actions checks.",
        "No freshness SLA, automated alerting or DR target is claimed.",
    ],
    PURPLE,
)
q.note(
    "decisions",
    45,
    945,
    1610,
    120,
    "ARCHITECTURE DECISIONS / TRADE-OFFS",
    [
        "Full retained-window rebuild favors reproducibility over incremental cost; full-scale runner acceptance remains open.",
        "Separate aggregate serving keeps large complaint/narrative databases out of the dashboard deployment.",
        "Current source download is blocked by HTTP 403. Durable source versions and hosted AI detail access remain future work.",
    ],
    GOLD,
)
q.finish("Processing is batch-based; no streaming or live-backlog service")
bundle("system-architecture", [p, q])

# LLD: actual implementation contracts, model grain and fail-closed publication.
model_page = Page(
    "low-level-contracts",
    "LLD 01  /  Source-to-model contracts",
    "Implementation and transformation view · Exact identities, schemas and validation gates",
    "SCOPE: scripts/refresh_pipeline.py → maintained dbt models → staged serving release",
    height=1220,
)
model_page.lane(
    "sourcezone",
    45,
    230,
    1610,
    270,
    "01  ACQUISITION & REPLAY IDENTITY",
    "Official catalogue → verified source bytes → revision comparison",
    BLUE,
)
model_page.card(
    "discover",
    70,
    310,
    350,
    165,
    "discover / archive_period",
    "PYTHON / SOURCE CATALOGUE",
    [
        "Official HTTPS host allowlist",
        "Numbered archive month intervals",
        "Reject unknown labels / missing months",
    ],
    "search",
    BLUE,
)
model_page.card(
    "download",
    465,
    310,
    350,
    165,
    "Verified archive cache",
    "PYTHON / STREAMING DOWNLOAD",
    [
        "ETag / Last-Modified when available",
        "SHA-256 cache verification",
        "Incomplete download never promoted",
    ],
    "files",
    BLUE,
)
model_page.card(
    "revision",
    860,
    310,
    350,
    165,
    "Revision identity",
    "CONTRACT / SHA-256",
    [
        "Source bytes + code + window",
        "Latest labelled month; [start, end)",
        "Unchanged revision skips rebuild",
    ],
    "manifest",
    PURPLE,
)
model_page.note(
    "entry",
    1255,
    310,
    375,
    165,
    "TRIGGER / PRECONDITIONS",
    [
        "Daily scheduler or manual force",
        "Validate catalogue coverage",
        "Check available runner disk",
        "HTTP 403 currently blocks ZIP fetch",
    ],
    RED,
)
model_page.edge(
    "dl", "discover", "download", [(420, 392), (465, 392)], "URLs", 423, 370
)
model_page.edge(
    "hash", "download", "revision", [(815, 392), (860, 392)], "Hashes", 819, 370
)
model_page.lane(
    "dbzone",
    45,
    545,
    1610,
    490,
    "02  DATA / REFRESH_WORK  ·  FRESH DUCKDB BUILD",
    "Runner-local source processing and dbt materialization",
)
model_page.card(
    "bronze",
    70,
    625,
    350,
    165,
    "Retained bronze",
    "TABLE / MAIN.BRONZE_COMPLAINTS",
    [
        "50,000-row chunks; 16 raw fields",
        "Received-date window; provenance",
        "Trimmed ID: latest release wins",
    ],
    "database",
    BLUE,
)
model_page.card(
    "staging",
    465,
    625,
    350,
    165,
    "Typed staging",
    "VIEWS / MAIN_STAGING",
    [
        "Parse dates; Yes/No → boolean",
        "Optional blank categories → NULL",
        "IDs and ZIP remain text",
    ],
    "code",
    TEAL,
)
model_page.card(
    "silver",
    860,
    625,
    350,
    165,
    "Normalized silver",
    "8 TABLES / MAIN_SILVER",
    [
        "Complaint + dimensions + narratives",
        "Tags + complaint/tag bridge",
        "JSON → MD5 category keys",
    ],
    "database",
    TEAL,
)
model_page.card(
    "gold",
    1255,
    625,
    375,
    165,
    "Complaint metrics",
    "TABLE / MAIN_GOLD",
    [
        "One row per complaint",
        "18 additive 0/1 count flags",
        "Narrative search view, not vectors",
    ],
    "database",
    GOLD,
)
model_page.card(
    "gate",
    465,
    845,
    350,
    165,
    "Build / invariant gate",
    "DBT BUILD / 126 DATA TESTS",
    [
        "Unique keys + relationships",
        "Row and narrative preservation",
        "Flags + star/wide reconciliation",
    ],
    "shield",
    TEAL,
)
model_page.card(
    "star",
    1255,
    845,
    375,
    165,
    "Dimensional gold",
    "TABLES / MAIN_STAR",
    [
        "fact_complaints + 7 dimensions",
        "Two date roles; YYYYMMDD keys",
        "Flags derive from the wide model",
    ],
    "database",
    GOLD,
)
model_page.note(
    "keyrules",
    70,
    845,
    350,
    165,
    "KEY / OVERLAP RULES",
    [
        "Source IDs are strings, not integers",
        "Archive ordinal DESC, record DESC",
        "Logical record number precedes filter",
        "No inferred company entity merging",
    ],
    PURPLE,
)
model_page.note(
    "stageout",
    860,
    845,
    350,
    165,
    "NEXT BOUNDARY: DATA / RELEASE",
    [
        "Four exports, each sum reconciled",
        "Manifest holds hashes + validation",
        "90 MiB per-file serving guard",
        "See LLD 02 and LLD 03",
    ],
    GOLD,
)
model_page.edge(
    "load",
    "revision",
    "bronze",
    [(1035, 475), (1035, 520), (245, 520), (245, 625)],
    "Changed revision → ingest retained source records",
    420,
    502,
)
model_page.edge("type", "bronze", "staging", [(420, 708), (465, 708)], "Rows", 424, 686)
model_page.edge(
    "normalize", "staging", "silver", [(815, 708), (860, 708)], "Keys", 819, 686
)
model_page.edge(
    "metric", "silver", "gold", [(1210, 708), (1255, 708)], "Joins", 1214, 686
)
model_page.edge(
    "dim", "gold", "star", [(1442, 790), (1442, 845)], "Reuse metric flags", 1455, 809
)
model_page.edge(
    "validate",
    "star",
    "gate",
    [(1442, 1010), (1442, 1024), (640, 1024), (640, 1010)],
    "Validate all layers before publication",
    710,
    1007,
    True,
)
model_page.note(
    "error",
    45,
    1070,
    1610,
    75,
    "FAIL CLOSED",
    [
        "Missing fields, invalid received dates, missing IDs, catalogue gaps, download errors or failed assertions abort the release; no silent row quarantine."
    ],
    RED,
)
model_page.finish(
    "Bronze here is retention-filtered; durable raw source preservation is not implemented"
)

s = Page(
    "serving-contracts",
    "LLD 02  /  Gold-to-dashboard contracts",
    "Data-product interface view · Aggregate grain, lineage, metric algebra and cache identity",
    "SCOPE: main_gold.complaint_metrics → four Parquet contracts → independent dashboard queries",
)
s.lane(
    "producer", 45, 230, 385, 665, "PRODUCER", "Complaint-grain numerical source", GOLD
)
s.lane(
    "interface",
    470,
    230,
    740,
    665,
    "VERSIONED SERVING INTERFACES",
    "All datasets preserve NULL groups and reconcile all 18 sums",
)
s.lane("consumer", 1250, 230, 405, 665, "CONSUMER", "dashboard/app.py", BLUE)
s.card(
    "wide",
    70,
    325,
    335,
    195,
    "complaint_metrics",
    "TABLE / ONE COMPLAINT PER ROW",
    [
        "Complaint ID: unique, non-NULL",
        "Date + company + product context",
        "18 additive count flags",
        "No resolution duration / loss amounts",
    ],
    "database",
    GOLD,
)
s.card(
    "overview",
    495,
    325,
    335,
    160,
    "Company / product",
    "PARQUET / BASE DAILY GRAIN",
    [
        "date_received + company ID/name",
        "product ID / product / sub-product",
        "Overview, Trends, Companies, Outcomes",
    ],
    "files",
    TEAL,
)
s.card(
    "issues",
    850,
    325,
    335,
    160,
    "Issues",
    "PARQUET / BASE + ISSUE DETAIL",
    [
        "Extra grain: issue + sub_issue",
        "Product and issue drilldown",
        "Issue selection is local to its charts",
    ],
    "files",
    TEAL,
)
s.card(
    "geo",
    495,
    555,
    335,
    160,
    "Geography",
    "PARQUET / BASE + STATE",
    [
        "Extra grain: reported state",
        "Map + unmappable-state table",
        "Not geocoded customer locations",
    ],
    "files",
    BLUE,
)
s.card(
    "channels",
    850,
    555,
    335,
    160,
    "Channels",
    "PARQUET / BASE + CHANNEL",
    [
        "Extra grain: submission_channel",
        "Channel comparison",
        "Same global filters and metrics",
    ],
    "files",
    BLUE,
)
s.card(
    "query",
    1280,
    325,
    345,
    195,
    "Independent queries",
    "DUCKDB / PARAMETERIZED SQL",
    [
        "Date / company / product filters",
        "Never join the four serving grains",
        "SUM numerator / SUM denominator",
        "No average of subgroup rates",
    ],
    "code",
    BLUE,
)
s.card(
    "ui",
    1280,
    555,
    345,
    160,
    "Presentation contract",
    "STREAMLIT / SIX TABS",
    [
        "K / M / B on labels and hover",
        "Percentages use explicit denominators",
        "CSV preserves exact count values",
    ],
    "dashboard",
    TEAL,
)
s.card(
    "manifest",
    70,
    595,
    335,
    245,
    "refresh_manifest.json",
    "METADATA / SUCCESSFUL REVISION",
    [
        "Revision SHA-256; source URLs / hashes",
        "HTTP validators; retention boundaries",
        "Observed min / max received dates",
        "Flag totals; export hashes / sizes",
        "Overlap count; validation timestamp",
        "Historical fallback if manifest absent",
    ],
    "manifest",
    PURPLE,
)
s.edge("ag1", "wide", "overview", [(405, 385), (495, 385)], "GROUP BY / SUM", 407, 363)
s.edge(
    "ag2real",
    "wide",
    "issues",
    [(405, 445), (447, 445), (447, 302), (1018, 302), (1018, 325)],
    "Independent aggregation from wide gold",
    590,
    282,
)
s.edge(
    "ag3",
    "wide",
    "geo",
    [(405, 475), (447, 475), (447, 635), (495, 635)],
    "SUM",
    451,
    603,
)
s.edge(
    "ag4",
    "wide",
    "channels",
    [(405, 500), (442, 500), (442, 745), (1018, 745), (1018, 715)],
    "Independent aggregation from wide gold",
    600,
    752,
)
s.edge(
    "read1",
    "overview",
    "query",
    [(830, 455), (840, 455), (840, 530), (1230, 530), (1230, 460), (1280, 460)],
    "Independent file reads",
    1000,
    507,
)
s.edge("read2", "issues", "query", [(1185, 405), (1280, 405)], "Read", 1210, 382)
s.edge(
    "read3",
    "geo",
    "query",
    [(830, 620), (840, 620), (840, 530), (1230, 530), (1230, 460), (1280, 460)],
    "",
    1235,
    475,
)
s.edge(
    "read4",
    "channels",
    "query",
    [(1185, 620), (1230, 620), (1230, 460), (1280, 460)],
    "",
    1235,
    495,
)
s.edge("render", "query", "ui", [(1452, 520), (1452, 555)], "Results", 1463, 531)
s.note(
    "cache",
    495,
    790,
    690,
    85,
    "CACHE / FILE IDENTITY",
    [
        "Each cached query receives (mtime_ns, file_size) as explicit arguments.",
        "Checkout updates change cache identity; retained previous-period coverage is checked.",
    ],
    PURPLE,
)
s.note(
    "release",
    45,
    945,
    1610,
    120,
    "RELEASE CONTRACT",
    [
        "Files: dashboard_daily_company_product.parquet · dashboard_issues.parquet · dashboard_geography.parquet · dashboard_channels.parquet",
        "One staged revision → one release commit with reports/refresh_manifest.json. No partially validated release is promoted.",
        "This is an analytics interface, not a complaint-text retrieval API. Future AI requires a persistent detailed-data service.",
    ],
    GOLD,
)
s.finish("Arrows from gold represent independent aggregations; no inter-export joins")

f = Page(
    "release-lifecycle",
    "LLD 03  /  Release lifecycle & failure handling",
    "State and control-flow view · Source revision to merge-gated publication",
    "SCOPE: .github/workflows/data-refresh.yml and scripts/refresh_pipeline.py",
    height=1180,
)
f.lane(
    "process",
    45,
    230,
    1610,
    600,
    "PROCESSING AND PUBLICATION STATES",
    "A release becomes current only through a successful PR merge",
)
f.card(
    "discoverstate",
    75,
    315,
    320,
    150,
    "Discover & compare",
    "STATE / OFFICIAL SOURCES",
    ["Validate URLs, hashes and window", "Compute deterministic revision"],
    "search",
    BLUE,
)
f.card(
    "buildstate",
    470,
    315,
    320,
    150,
    "Build retained window",
    "STATE / FRESH DATABASE",
    ["Parse / retain / deduplicate", "dbt build + data tests"],
    "process",
)
f.card(
    "gatestate",
    865,
    315,
    320,
    150,
    "Validate & stage",
    "STATE / EXPORT GATE",
    ["18 sums match all four exports", "Manifest + per-file size guard"],
    "shield",
)
f.card(
    "prstate",
    1260,
    315,
    320,
    150,
    "Open release PR",
    "STATE / GITHUB BRANCH",
    ["Commit four files + manifest", "No direct push to main"],
    "branch",
    BLUE,
)
f.card(
    "unchanged",
    75,
    630,
    320,
    150,
    "No changed revision",
    "TERMINAL / SKIP",
    ["No rebuild or publication", "Current serving files retained"],
    "clock",
    GRAY,
)
f.card(
    "abort",
    470,
    630,
    320,
    150,
    "Processing failed",
    "TERMINAL / ABORT",
    ["Download, parse, dbt or export error", "Preserve last published release"],
    "stop",
    RED,
)
f.card(
    "pending",
    865,
    630,
    320,
    150,
    "Merge blocked",
    "STATE / PENDING PR",
    ["Required rules remain authoritative", "Current serving data stays in place"],
    "shield",
    GOLD,
)
f.card(
    "published",
    1260,
    630,
    320,
    150,
    "Merged release",
    "TERMINAL / MAIN + DEPLOY",
    ["Merge commit records history", "Streamlit picks up merged files"],
    "dashboard",
    TEAL,
)
f.edge(
    "r1", "discoverstate", "buildstate", [(395, 390), (470, 390)], "Changed", 402, 366
)
f.edge(
    "r2", "buildstate", "gatestate", [(790, 390), (865, 390)], "Tests pass", 795, 366
)
f.edge(
    "r3",
    "gatestate",
    "prstate",
    [(1185, 390), (1260, 390)],
    "All gates pass",
    1188,
    365,
)
f.edge(
    "r4",
    "discoverstate",
    "unchanged",
    [(235, 465), (235, 630)],
    "Unchanged",
    248,
    535,
    True,
)
f.edge(
    "r5",
    "buildstate",
    "abort",
    [(630, 465), (630, 630)],
    "Failure",
    643,
    535,
    True,
    RED,
)
f.edge(
    "r6",
    "prstate",
    "pending",
    [(1420, 465), (1420, 550), (1025, 550), (1025, 630)],
    "Permission / policy prevents merge",
    1065,
    525,
    True,
    GOLD,
)
f.edge(
    "r7",
    "prstate",
    "published",
    [(1525, 465), (1525, 630)],
    "Merge succeeds",
    1380,
    585,
)
f.edge(
    "r8",
    "pending",
    "published",
    [(1185, 705), (1260, 705)],
    "Rules met",
    1190,
    678,
    True,
)
f.note(
    "failnote",
    45,
    875,
    785,
    175,
    "FAILURE / EVIDENCE CONTRACT",
    [
        "Discovery, download and validation failures can abort from any processing state.",
        "Build logs, run_results and manifest are uploaded with if: always().",
        "Evidence artifacts last 14 days; ZIP cache is not durable source-version storage.",
        "Current observed failure: HTTP 403 at the first hosted archive download.",
    ],
    RED,
)
f.note(
    "botnote",
    870,
    875,
    785,
    175,
    "CONCURRENCY / REPOSITORY RULES",
    [
        "New main refresh runs cancel older runs in the same concurrency group.",
        "GITHUB_TOKEN-created PRs do not trigger independent PR Actions CI.",
        "Full validation runs before PR creation; no protected-branch bypass.",
        "Source-download resolution and first full rolling publication remain open.",
    ],
    PURPLE,
)
f.finish("Source failures never imply a successful data refresh")
bundle("low-level-contracts", [model_page, s, f])
print("Generated 2 HLSD pages, 3 LLD pages and matching SVG previews.")
