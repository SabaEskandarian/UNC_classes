#!/usr/bin/env python3
import subprocess
import sys
import os
import tempfile
from bs4 import BeautifulSoup

BASE_URL = "https://reports.unc.edu/class-search/tiled/?subject={subject}&term=2026+Fall"

SUBJECTS = ["COMP"]

#SUBJECTS = [
#    "AAAD", "AMST", "ANTH", "APPL", "ASTR", "BCB", "BIOC", "BIOL", "BIOS",
#    "BMME", "BUSI", "CHEM", "CLAR", "CMPL", "COMM", "COMP", "DATA", "DRAM",
#    "ECON", "EDUC", "EMES", "ENEC", "ENGL", "ENVR", "EPID", "EXSS", "GEOG",
#    "HBEH", "INLS", "LING", "MATH", "MEJO", "NSCI", "PHIL", "PHYS", "PLAN",
#    "PLCY", "POLI", "PSYC", "SOCI", "STOR", "WGST",
#]

CSS = """
body{
    font-family: Arial, Helvetica, sans-serif;
    padding: 30px;
}
#main{
    margin: auto;
}
ul{
    list-style-type:none;
}
table{
    border: none;
}
th{
    font-weight: bold;
    padding-bottom: 1em;
    text-align: left;
    padding-right: 2em;
}
td{
    padding-bottom: 1em;
    padding-right: 2em;
}
h1{
    font-weight: normal;
}
h2{
    font-weight: normal;
}
h3{
    font-weight: normal;
    margin-bottom: 0px;
    margin-top: 0px;
}
a{
    color: #337ab7;
    outline:none;
}
a:hover {
    color: hotpink;
}
tr:nth-child(even) {
    background-color: #F2F7FB;
}
"""


def fetch_page(url):
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
        tmpfile = f.name
    try:
        subprocess.run(["wget", "-q", "-O", tmpfile, url], check=True)
        with open(tmpfile, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    finally:
        os.unlink(tmpfile)


def text(el):
    return el.get_text(" ", strip=True) if el else ""


def parse_courses(html):
    soup = BeautifulSoup(html, "html.parser")
    courses = []

    for card in soup.find_all("div", class_="card"):
        header = card.find("div", class_="card-header")
        body = card.find("div", class_="card-body")
        panel = card.find("div", class_="panel-body")

        if not header:
            continue

        # Header fields
        course_num = text(header.find("h2"))
        title = text(header.find("h3"))
        seats = text(header.find("p", class_="card-available-seats")).replace(" available seats", "")

        # Card body: term, time, credits (each in a <p>)
        body_ps = [text(p) for p in body.find_all("p")] if body else []
        term = body_ps[0] if len(body_ps) > 0 else ""
        time = body_ps[1] if len(body_ps) > 1 else ""
        credits = body_ps[2].replace(" credit hours", "") if len(body_ps) > 2 else ""

        # Expandable panel body: cross-list, dates, delivery, class number
        panel_ps = [text(p) for p in panel.find_all("p")] if panel else []
        cross_list = panel_ps[0] if len(panel_ps) > 0 else ""
        dates = panel_ps[1] if len(panel_ps) > 1 else ""
        delivery = panel_ps[2] if len(panel_ps) > 2 else ""
        class_num = panel_ps[3].replace("Class Number: ", "") if len(panel_ps) > 3 else ""

        courses.append({
            "Course": course_num,
            "Title": title,
            "Available Seats": seats,
            "Time": time,
            "Credits": credits,
            "Dates": dates,
            "Delivery": delivery,
            "Class #": class_num,
            "Cross-listed": cross_list,
        })

    return courses


HEADERS = ["Class #", "Course", "Title", "Time", "Credits", "Available Seats", "Delivery"]


OUTPUT_DIR = "output"
AFS_DIR = "/afs/cs.unc.edu/home/saba/public_html/UNC_classes"


def build_html(subject, courses, all_subjects):
    header_row = "".join(f"<th>{h}</th>" for h in HEADERS)

    rows_html = []
    for course in courses:
        cells = "".join(f"<td>{course.get(h, '')}</td>" for h in HEADERS)
        rows_html.append(f"<tr>{cells}</tr>")

    nav_links = " | ".join(
        f'<a href="{s}.html">{s}</a>' for s in sorted(all_subjects)
    )

    return f"""<html>
<head>
    <title>{subject} Class Information</title>
    <style>{CSS}</style>
</head>
<body>
<div id="main">
<h1>{subject} Classes &mdash; 2026 Fall</h1>
<p>{nav_links}</p>
<table>
<thead><tr>{header_row}</tr></thead>
<tbody>
{''.join(rows_html)}
</tbody>
</table>
</div>
</body>
</html>"""


def process_subject(subject, all_subjects):
    url = BASE_URL.format(subject=subject)
    print(f"Fetching {url} ...", file=sys.stderr)
    raw_html = fetch_page(url)

    print(f"Parsing courses for {subject}...", file=sys.stderr)
    courses = parse_courses(raw_html)
    print(f"Found {len(courses)} course sections.", file=sys.stderr)

    output = build_html(subject, courses, all_subjects)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_file = os.path.join(OUTPUT_DIR, f"{subject}.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"Written to {out_file}", file=sys.stderr)

    try:
        afs_file = os.path.join(AFS_DIR, f"{subject}.html")
        subprocess.run(["cp", out_file, afs_file], check=True)
        print(f"Copied to {afs_file}", file=sys.stderr)
    except Exception as e:
        print(f"Could not copy to AFS ({afs_file}): {e}", file=sys.stderr)


def main():
    for subject in SUBJECTS:
        process_subject(subject, SUBJECTS)


if __name__ == "__main__":
    main()
