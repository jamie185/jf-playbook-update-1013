#!/usr/bin/env python3
"""Build the Gabrielle Playbook update page from data.json."""

import html
import json
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data.json"
OUTPUT_FILE = ROOT / "index.html"


def esc(value):
    return html.escape(str(value or ""), quote=True)


def lesson_href(data, lesson_id):
    base = data["playbook_url"].rstrip("#")
    return f"{base}#/l/{quote(lesson_id, safe='')}/0"


def route_href(data, route):
    base = data["playbook_url"].rstrip("#")
    return f"{base}#/{quote(route.strip('/'), safe='/')}"


def playbook_link(data, lesson_id, label=None):
    title = data["lesson_titles"].get(lesson_id)
    if not title:
        raise ValueError(f"No lesson title for link: {lesson_id}")
    label = label or title
    return (
        f'<a class="text-link" href="{esc(lesson_href(data, lesson_id))}" '
        f'aria-label="Open {esc(title)} in the Playbook">{esc(label)}</a>'
    )


def answer_row(data, row):
    return f"""<article class="answer-row">
  <div class="answer-copy">
    <h3>{esc(row['title'])}</h3>
    <div class="answer-pair">
      <div>
        <p class="field-label">You said</p>
        <p class="said">{esc(row['said'])}</p>
      </div>
      <div>
        <p class="field-label">Course wording</p>
        <blockquote>{esc(row['quote'])}</blockquote>
      </div>
    </div>
    <p class="change-summary">{esc(row['changed'])}</p>
    <p class="lesson-link">Find it in the lesson: {playbook_link(data, row['lesson'])}</p>
  </div>
</article>"""


def answer_groups(data):
    sections = []
    for group in data["answer_groups"]:
        rows = "\n".join(answer_row(data, row) for row in group["rows"])
        tone = esc(group.get("tone", "blue"))
        sections.append(f"""<section class="answer-group tone-{tone}" aria-labelledby="group-{esc(tone)}">
  <h3 class="group-title" id="group-{esc(tone)}">{esc(group['title'])}</h3>
  <div class="answer-grid">{rows}</div>
</section>""")
    return "\n".join(sections)


def tool_card(data, tool):
    if tool.get("route"):
        href = route_href(data, tool["route"])
        aria = tool.get("aria_label", f"Open {tool['title']} in the Playbook")
    elif tool.get("lesson"):
        href = lesson_href(data, tool["lesson"])
        aria = f"Open {data['lesson_titles'][tool['lesson']]} in the Playbook"
    else:
        href = data["playbook_url"]
        aria = "Open the Playbook"
    steps = ""
    if tool.get("steps"):
        steps = "<ol class=\"tool-steps\">" + "".join(
            f"<li>{esc(step)}</li>" for step in tool["steps"]
        ) + "</ol>"
    extra = f'<p class="tool-extra">{esc(tool["extra"])}</p>' if tool.get("extra") else ""
    return f"""<article class="tool-card">
  <h3>{esc(tool['title'])}</h3>
  <p>{esc(tool['text'])}</p>
  {steps}
  {extra}
  <a class="text-link" href="{esc(href)}" aria-label="{esc(aria)}">{esc(tool.get('link_label', 'Open in the Playbook'))}</a>
</article>"""


def fix_card(data, item):
    links = [playbook_link(data, item["lesson"])] if item.get("lesson") else []
    if item.get("second_lesson"):
        links.append(playbook_link(data, item["second_lesson"]))
    link_markup = "<p class=\"lesson-link\">Find it in: " + " and ".join(links) + "</p>" if links else ""
    quote = f'<blockquote class="template-quote">{esc(item["quote"])}</blockquote>' if item.get("quote") else ""
    return f"""<article class="fix-card">
  <h3>{esc(item['title'])}</h3>
  <p>{esc(item['text'])}</p>
  {quote}
  {link_markup}
</article>"""


def list_cards(items, class_name):
    return "\n".join(
        f'<article class="{class_name}"><h3>{esc(item["title"])}</h3><p>{esc(item["text"])}</p></article>'
        for item in items
    )


def open_cards(items):
    return "\n".join(
        f'<article class="open-item"><h3>{esc(item["title"])}</h3><p>{esc(item["text"])}</p></article>'
        for item in items
    )


def render(data):
    if not data.get("playbook_url"):
        raise ValueError("playbook_url is required")

    referenced = set()
    for group in data.get("answer_groups", []):
        referenced.update(row["lesson"] for row in group["rows"])
    for item in data.get("new_tools", []) + data.get("fixes", []):
        if item.get("lesson"):
            referenced.add(item["lesson"])
        if item.get("second_lesson"):
            referenced.add(item["second_lesson"])
    missing = referenced - set(data.get("lesson_titles", {}))
    if missing:
        raise ValueError("Missing lesson titles: " + ", ".join(sorted(missing)))

    css = r"""
@font-face{font-family:Inter;src:url('assets/inter.woff2') format('woff2');font-style:normal;font-weight:100 900;font-display:swap}
:root{--ink:#222326;--secondary:rgba(31,32,37,.66);--muted:#687080;--canvas:#f5f7fb;--white:#fff;--card:#ebf0f8;--navy:#141742;--dark:#1f2025;--blue:#4da3ff;--blue-wash:#dcebfb;--orange:#f5a524;--orange-wash:#fdebd3;--green:#7ed321;--green-wash:#e4f3d6;--hairline:#eceef2;--radius:24px;--ease:cubic-bezier(.2,.7,.2,1)}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:20px}
body{margin:0;background:var(--canvas);color:var(--ink);font-family:Inter,-apple-system,BlinkMacSystemFont,'SF Pro Text',system-ui,sans-serif;font-size:17px;font-weight:500;line-height:1.48;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
a{color:inherit;text-decoration-thickness:1px;text-underline-offset:4px}
a:hover{text-decoration-thickness:2px}
a:focus-visible{outline:3px solid color-mix(in srgb,var(--blue) 65%,white);outline-offset:4px;border-radius:6px}
.page{max-width:1200px;width:calc(100% - 32px);margin:0 auto;padding:16px 0 64px}
.site-header{display:flex;align-items:center;gap:11px;padding:3px 3px 18px}
.brand-mark{width:40px;height:34px;display:grid;place-items:center;background:var(--navy);border-radius:11px;flex:none}
.brand-mark img{width:28px;height:17px;object-fit:contain}
.brand-name{font-size:16px;font-weight:700;letter-spacing:-.02em}
.hero{padding:32px 24px 28px;border-radius:var(--radius);background:linear-gradient(145deg,#dceafb 0%,#edf3fa 58%,#f7f8fb 100%);box-shadow:0 1px 0 rgba(0,0,0,.03);overflow:hidden}
.hero h1{max-width:920px;font-size:clamp(42px,7.5vw,76px);font-weight:700;line-height:.99;letter-spacing:-.045em;margin:0}
.hero-intro{max-width:740px;margin:20px 0 0;color:var(--secondary);font-size:clamp(18px,2.5vw,22px);line-height:1.38;letter-spacing:-.012em}
.draft-line{margin:17px 0 0;color:var(--muted);font-size:14px;font-weight:600}
.section-nav{display:flex;gap:20px;flex-wrap:wrap;padding:22px 3px 0;font-size:15px;font-weight:600}
.section-nav a{color:var(--secondary)}
.section-nav a:hover{color:var(--ink)}
.link-note{margin:10px 3px 0;color:var(--muted);font-size:14px;line-height:1.4}
.live{margin-top:28px;padding:23px 24px 25px;border-radius:20px;background:var(--dark);color:#fff}
.live h2{font-size:23px;line-height:1.15;letter-spacing:-.025em;margin:0 0 8px;font-weight:700}
.live p{max-width:900px;color:rgba(255,255,255,.76);margin:0;font-size:16px;line-height:1.5}
.section{padding-top:70px;scroll-margin-top:20px}
.section-heading{max-width:780px;margin:0 0 24px}
.section-heading h2{font-size:clamp(32px,5vw,52px);font-weight:700;line-height:1;letter-spacing:-.04em;margin:0}
.section-heading p{font-size:18px;line-height:1.4;color:var(--secondary);max-width:690px;margin:12px 0 0}
.answer-group+.answer-group{margin-top:34px}
.group-title{font-size:26px;line-height:1.12;letter-spacing:-.025em;margin:0 0 14px;font-weight:700}
.tone-orange{--tone:var(--orange);--tone-wash:var(--orange-wash)}
.tone-green{--tone:var(--green);--tone-wash:var(--green-wash)}
.tone-blue{--tone:var(--blue);--tone-wash:var(--blue-wash)}
.answer-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.answer-row{min-width:0;background:var(--white);border-radius:20px;padding:20px 19px;box-shadow:0 1px 0 rgba(0,0,0,.035)}
.answer-row h3,.tool-card h3,.fix-card h3,.right-item h3,.open-item h3{margin:0;font-size:19px;line-height:1.2;letter-spacing:-.018em;font-weight:700}
.answer-pair{display:grid;grid-template-columns:1fr 1fr;gap:13px;margin-top:16px}
.field-label{font-size:13px;font-weight:650;color:var(--muted);margin:0 0 5px}
.said{font-size:15px;line-height:1.4;color:var(--secondary);margin:0}
blockquote{margin:0;border-radius:14px;background:var(--tone-wash,var(--card));padding:11px 12px;font-size:15px;font-weight:600;line-height:1.42;letter-spacing:-.008em}
.change-summary{margin:14px 0 0;font-size:15px;line-height:1.48;color:var(--secondary)}
.lesson-link{margin:13px 0 0;color:var(--muted);font-size:14px;line-height:1.4}
.text-link{display:inline;font-size:inherit;font-weight:650;color:#185ca6;overflow-wrap:anywhere}
.tool-grid,.fix-grid,.right-grid,.open-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.tool-card{background:var(--white);border-radius:20px;padding:22px;box-shadow:0 1px 0 rgba(0,0,0,.035)}
.tool-card:nth-child(1){background:linear-gradient(145deg,var(--blue-wash),#fff 72%)}
.tool-card:nth-child(2){background:linear-gradient(145deg,#e7eefb,#fff 72%)}
.tool-card p,.fix-card p,.right-item p,.open-item p{margin:10px 0 0;color:var(--secondary);font-size:15px;line-height:1.48}
.tool-steps{padding-left:22px;margin:15px 0 0;color:var(--secondary);font-size:14px;line-height:1.45}
.tool-steps li+li{margin-top:7px}
.tool-extra{padding-top:12px;border-top:1px solid rgba(34,35,38,.08);font-size:14px!important}
.tool-card>.text-link{display:inline-block;margin-top:14px}
.fix-card{background:var(--white);border-radius:18px;padding:19px 20px;box-shadow:0 1px 0 rgba(0,0,0,.035)}
.template-quote{margin-top:12px;font-size:14px;font-weight:550;background:#f5f7fb}
.fix-card .lesson-link{margin-top:12px}
.link-separator{color:#9ba2ad;padding:0 4px}
.right-section{padding:28px;border-radius:var(--radius);background:#fff;box-shadow:0 1px 0 rgba(0,0,0,.035)}
.right-section .section-heading{margin-bottom:20px}
.right-grid{gap:0 28px}
.right-item{padding:16px 0;border-top:1px solid var(--hairline)}
.right-item h3{font-size:17px}
.right-item p{margin-top:5px}
.open-grid{grid-template-columns:1fr 1fr}
.open-item{padding:18px 19px;background:#eaf0f7;border-radius:18px}
.open-item:nth-child(even){background:#eef1f5}
.open-item h3{font-size:17px}
.open-item p{font-size:14px;margin-top:7px}
.topic-details{margin-top:18px;background:#fff;border-radius:18px;padding:17px 20px;box-shadow:0 1px 0 rgba(0,0,0,.035)}
.topic-details summary{font-size:15px;font-weight:650;cursor:pointer}
.topic-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px 26px;padding:16px 0 0 20px;margin:0;color:var(--secondary);font-size:14px}
.footer{padding:42px 3px 0;color:var(--muted);font-size:13px}
.footer p{margin:0}
.footer a{color:var(--secondary)}
@media(min-width:900px){.page{width:calc(100% - 60px);padding-top:22px}.hero{padding:58px 54px 46px}.live{padding:27px 30px}.section{padding-top:92px}.answer-row{padding:23px}.group-title{font-size:30px}.right-section{padding:36px}}
@media(max-width:720px){body{font-size:16px}.page{width:calc(100% - 24px);padding-top:10px}.site-header{padding-bottom:12px}.hero{padding:28px 20px 25px;border-radius:21px}.hero h1{font-size:clamp(40px,12vw,53px);max-width:560px}.hero-intro{font-size:18px;margin-top:15px}.draft-line{font-size:13px}.section-nav{gap:9px 17px;padding-top:18px;font-size:14px;flex-wrap:wrap;white-space:normal}.live{margin-top:21px;padding:20px;border-radius:18px}.live h2{font-size:21px}.live p{font-size:15px}.section{padding-top:55px}.section-heading{margin-bottom:19px}.section-heading h2{font-size:36px}.section-heading p{font-size:16px}.group-title{font-size:23px}.answer-grid,.tool-grid,.fix-grid,.right-grid,.open-grid{grid-template-columns:1fr;gap:9px}.answer-group+.answer-group{margin-top:28px}.answer-row{padding:18px 16px;border-radius:17px}.answer-row h3,.tool-card h3,.fix-card h3{font-size:18px}.answer-pair{gap:10px;margin-top:13px}.said,blockquote{font-size:14px}.change-summary{font-size:14px}.lesson-link{font-size:13px}.tool-card{padding:19px;border-radius:17px}.fix-card{padding:17px;border-radius:16px}.right-section{padding:21px 18px;border-radius:20px}.right-item{padding:13px 0}.open-item{padding:16px;border-radius:16px}.topic-list{grid-template-columns:1fr;gap:6px}.footer{padding-top:34px}}
@media(max-width:390px){.answer-pair{grid-template-columns:1fr}.answer-pair>div+div{padding-top:1px}.hero h1{font-size:40px}.section-heading h2{font-size:33px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*,*::before,*::after{animation-duration:.01ms!important;transition-duration:.01ms!important}}
"""

    groups = answer_groups(data)
    tools = "\n".join(tool_card(data, item) for item in data["new_tools"])
    fixes = "\n".join(fix_card(data, item) for item in data["fixes"])
    right = list_cards(data["already_right"], "right-item")
    opens = open_cards(data["open"])
    topics = "".join(f"<li>{esc(topic)}</li>" for topic in data.get("shift_topics", []))
    topic_section = ""
    if topics:
        topic_section = f"""<details class="topic-details">
  <summary>See the 23 topics kept for your shifts</summary>
  <ul class="topic-list">{topics}</ul>
</details>"""

    return f"""<!doctype html>
<html lang="en-AU">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="robots" content="noindex, nofollow, noarchive">
  <meta name="googlebot" content="noindex, nofollow, noarchive">
  <meta name="description" content="What changed in the JF Playbook from Gabrielle’s sign-off.">
  <title>{esc(data['title'])} | Jamie Fitness</title>
  <link rel="icon" href="assets/jf-mark.svg" type="image/svg+xml">
  <style>{css}</style>
</head>
<body>
  <main class="page">
    <header class="site-header">
      <span class="brand-mark"><img src="assets/jf-mark.svg" alt="JF" width="28" height="17"></span>
      <span class="brand-name">Jamie Fitness</span>
    </header>

    <section class="hero" aria-labelledby="page-title">
      <h1 id="page-title">{esc(data['title'])}</h1>
      <p class="hero-intro">{esc(data['intro'])}</p>
      <p class="draft-line">{esc(data.get('release_note',''))} Updated {esc(data['date'])}.</p>
    </section>

    <nav class="section-nav" aria-label="On this page">
      <a href="#changes">Your sign-off</a>
      <a href="#new-for-you">New for you</a>
      <a href="#other-fixes">Other fixes</a>
      <a href="#already-right">Already right</a>
      <a href="#open">Still to finish</a>
    </nav>

    <section class="live" aria-labelledby="live-title">
      <h2 id="live-title">{esc(data['live']['title'])}</h2>
      <p>{esc(data['live']['text'])}</p>
    </section>
    <p class="link-note">{esc(data['link_note'])}</p>

    <section class="section" id="changes" aria-labelledby="changes-title">
      <div class="section-heading">
        <h2 id="changes-title">From your sign-off</h2>
        <p>The wording below is now live in the course. Each lesson link opens the Playbook after sign-in.</p>
      </div>
      {groups}
    </section>

    <section class="section" id="new-for-you" aria-labelledby="tools-title">
      <div class="section-heading">
        <h2 id="tools-title">New for you</h2>
        <p>These guide and video tools are part of the update and will be available after final checks.</p>
      </div>
      <div class="tool-grid">{tools}</div>
    </section>

    <section class="section" id="other-fixes" aria-labelledby="fixes-title">
      <div class="section-heading">
        <h2 id="fixes-title">Other fixes from your feedback</h2>
        <p>{esc(data.get('other_fixes_intro', ''))}</p>
      </div>
      <div class="fix-grid">{fixes}</div>
    </section>

    <section class="section right-section" id="already-right" aria-labelledby="right-title">
      <div class="section-heading">
        <h2 id="right-title">Things you said were already right</h2>
      </div>
      <div class="right-grid">{right}</div>
    </section>

    <section class="section" id="open" aria-labelledby="open-title">
      <div class="section-heading">
        <h2 id="open-title">Still to finish</h2>
        <p>A few things are deliberately left as they are, and why.</p>
      </div>
      <div class="open-grid">{opens}</div>
      {topic_section}
    </section>

    <footer class="footer">
      <p>{esc(data['closing'])}</p>
      
    </footer>
  </main>
</body>
</html>
"""


def main():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    page = render(data)
    page = "\n".join(line.rstrip() for line in page.splitlines()) + "\n"
    OUTPUT_FILE.write_text(page, encoding="utf-8")
    print(f"Built {OUTPUT_FILE.name} from {DATA_FILE.name}")


if __name__ == "__main__":
    main()
