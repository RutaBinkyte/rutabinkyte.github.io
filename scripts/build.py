"""Build a static academic website. Run from any directory with Python 3.10+."""

import argparse
import base64
import hashlib
import html
import json
import mimetypes
import re
import shutil
import unicodedata
from datetime import date
from pathlib import Path
from cv import compile_pdf, cv_sections, date_label, make_tex

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist"
DATA = ROOT / "data"
ASSETS = ROOT / "assets"
NAV = {
    "home": "Home",
    "papers": "Papers",
    "projects": "Projects",
    "talks": "Talks & Media",
    "awards": "Grants & Awards",
    "service": "Service",
    "teaching": "Teaching",
    "cv": "CV",
    "contact": "Contact",
}
DESCRIPTION = {
    "home": "Rūta Binkytė studies bias and safety in interactions among AI agents and between people and AI at DFKI. Explore her research, publications, news, talks, and collaboration interests.",
    "papers": "Research papers by Rūta Binkytė on trustworthy AI, causality, privacy, and multi-agent systems. Browse the publication archive by year or search by author and title.",
    "projects": "Rūta Binkytė’s research projects on deception, contribution attribution in human–AI co-creation, disinformation, multilingual compliance assistance, and synthetic health data.",
    "talks": "Invited talks, panels, and media interviews with Rūta Binkytė on fairness, causality, and AI ethics.",
    "awards": "Research grants, scholarships, and awards received by Rūta Binkytė.",
    "service": "Conference leadership, programme committees, reviewing and community service by Rūta Binkytė.",
    "teaching": "Courses, summer schools, and educational outreach by Rūta Binkytė.",
    "cv": "Academic CV of Rūta Binkytė, Senior Researcher at DFKI and Deputy Lead of its Efficient and Explainable AI group. Research appointments, education, funding, service, and selected publications, with a downloadable PDF.",
    "contact": "Contact Rūta Binkytė at DFKI about research collaborations, paid internship enquiries, partnerships, or speaking invitations.",
}
P = json.loads((DATA / "profile.json").read_text())
CURATED = json.loads((DATA / "selected-papers.json").read_text())
CACHE = json.loads((DATA / "scholar-cache.json").read_text())
CONFERENCE_VENUES = json.loads((DATA / "conference-venues.json").read_text())
BASE = P["base"].rstrip("/")
EMAIL = P["email"]
NAME = P["name"]
FEATURED = [next(p for p in CURATED if p["id"] == key) for key in P["featuredPapers"]]
E = lambda v: html.escape(str(v), quote=True)


def normalize(title):
    return "".join(
        c for c in unicodedata.normalize("NFKD", title).casefold() if c.isalnum()
    )


def archive():
    rows = CACHE["articles"]
    if not rows:
        return sorted(CURATED, key=lambda p: -(p.get("year") or 0))

    known = {
        normalize(title): p
        for p in CURATED
        for title in [p["title"], *p.get("aliases", [])]
    }
    by_id = {p["id"]: p for p in CURATED}
    works = {}
    for raw in rows:
        key = normalize(raw["title"])
        curated = by_id.get(raw.get("work_id")) or known.get(key)
        if curated:
            works[curated["id"]] = curated
        else:
            work_id = raw.get("work_id") or key
            if work_id not in works:
                anchor = raw.get("work_id") or "scholar-" + raw["citation_id"].split(":")[-1]
                works[work_id] = {**raw, "id": anchor, "summary": ""}
    return sorted(works.values(), key=lambda p: -(p.get("year") or 0))


PAPERS = archive()


def filename(page):
    return "index.html" if page == "home" else page + ".html"


def canonical(page):
    return BASE + ("/" if page == "home" else "/" + filename(page))


def link(url, label, cls="", extra=""):
    return f'<a href="{E(url)}" class="{E(cls)}" {extra}>{E(label)}</a>'


def asset_uri(path):
    mime = (
        {".woff2": "font/woff2", ".tex": "application/x-tex"}.get(path.suffix)
        or mimetypes.guess_type(path.name)[0]
        or "application/octet-stream"
    )
    return (
        "data:"
        + mime
        + ";base64,"
        + base64.b64encode(path.read_bytes()).decode("ascii")
    )


def publication_venue(venue, *, markup=False):
    parts = []
    for entry in CONFERENCE_VENUES.get(venue, [venue]):
        if isinstance(entry, str):
            parts.append(E(entry) if markup else entry)
        else:
            abbreviation, full_name = entry
            if markup:
                parts.append(f"{E(full_name)} (<strong>{E(abbreviation)}</strong>)")
            else:
                parts.append(f"{full_name} ({abbreviation})")
    return " · ".join(parts)


def authorline(paper):
    names = paper.get("authors", [])
    if isinstance(names, str):
        return E(names)
    return ", ".join(
        f"<strong>{E(n)}</strong>" if "binkyt" in n.lower() else E(n) for n in names
    )


def icon(name):
    paths = {
        "Google Scholar": '<path d="m2 9 10-5 10 5-10 5z M6 12v4c4 3 8 3 12 0v-4 M21 10v6"/>',
        "GitHub": '<path d="M9 20c-5 1-5-3-7-3m14 5v-4c0-1-.3-1.8-1-2 3.2-.4 6-1.6 6-6 0-1.3-.5-2.4-1.3-3.3.2-1 .1-2.1-.4-3.2-1.3-.2-2.6.4-3.8 1.2a13.4 13.4 0 0 0-7 0c-1.2-.8-2.5-1.4-3.8-1.2-.5 1.1-.6 2.2-.4 3.2C3.5 7.6 3 8.7 3 10c0 4.4 2.8 5.6 6 6-.6.3-1 1.2-1 2v4"/>',
        "ORCID": '<circle cx="12" cy="12" r="9.2"/><path d="M8 10v6m0-9v.1m3 2v7h2a3.5 3.5 0 0 0 0-7z"/>',
        "LinkedIn": '<rect x="2.5" y="2.5" width="19" height="19" rx="2"/><path d="M7 10v7m0-10v.1m4 10v-7m0 3c0-4 6-4 6 0v4"/>',
        "email": '<rect x="2.5" y="4.5" width="19" height="15" rx="2"/><path d="m3.5 6 8.5 7 8.5-7"/>',
        "location": '<path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 0 1 14 0z"/><circle cx="12" cy="10" r="2"/>',
    }
    return (
        '<svg class="mini-icon" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'
        + paths.get(name, "")
        + "</svg>"
    )


class Render:
    def __init__(self, standalone=False):
        self.standalone = standalone

    def url(self, route):
        if route.startswith(("https://", "mailto:")):
            return route
        page, _, anchor = route.partition("#")
        if self.standalone:
            return "#" + page + ("--" + anchor if anchor else "")
        return filename(page) + ("#" + page + "--" + anchor if anchor else "")

    def image(self, name, alt="", extra=""):
        path = asset_uri(ASSETS / name) if self.standalone else "assets/" + name
        return f'<img src="{E(path)}" alt="{E(alt)}" {extra}>'

    def event_photos(self, photos, event):
        first = Path(photos[0][0])
        thumb = first.with_stem(first.stem + "-thumb")
        lazy = 'loading="lazy"'
        preview = self.image(str(thumb) if (ASSETS / thumb).is_file() else str(first), "", lazy)
        label = "View photo" if len(photos) == 1 else f"View {len(photos)} photos"
        figures = "".join(
            f'<figure>{self.image(filename, "", lazy)}<figcaption>{E(caption)}</figcaption></figure>'
            for filename, caption in photos
        )
        return (
            f'<details class="event-photos"><summary>{preview}<span class="when-closed">{label}</span>'
            f'<span class="when-open">Close photos</span><span class="visually-hidden"> · {E(event)}</span></summary>'
            f'<div class="photo-grid">{figures}</div></details>'
        )

    def file_link(self, name, label, cls):
        path = asset_uri(OUT / name) if self.standalone else name
        return link(path, label, cls, f'download="{name}"')

    def bar(self, page):
        items = "".join(
            link(
                self.url(k),
                v,
                "contact-nav" if k == "contact" else "",
                'data-nav="' + k + '"' + (' aria-current="page"' if k == page else ""),
            )
            for k, v in NAV.items()
        )
        mark = self.image("ruby-pixels.png", "", 'width="360" height="88"')
        return f'<a class="skip" href="#main">Skip to content</a><header class="sitehead"><div class="wrap headrow"><a href="{self.url("home")}" class="brand"><span class="mark" aria-hidden="true">{mark}</span>{E(NAME)}</a><nav class="nav" aria-label="Main navigation">{items}</nav></div></header>'

    def foot(self):
        machine = link(
            asset_uri(OUT / "research.json") if self.standalone else "research.json",
            "Research data",
            extra='download="research.json"' if self.standalone else "",
        )
        return f'<footer class="foot"><div class="wrap footrow"><p>© {date.today().year} {E(NAME)}</p><div>{link(P["profiles"]["ORCID"], "ORCID")}{link(self.url("contact"), "Contact")}{machine}</div></div></footer>'

    def intro(self, kicker, title, description):
        return f'<header class="pageintro"><p class="kicker">{E(kicker)}</p><h1>{E(title)}</h1><p>{E(description)}</p></header>'

    def news(self, items):
        return (
            '<ul class="newslist">'
            + "".join(
                f'<li><time class="date" datetime="{dt}">{date_label(dt)}</time><div><span class="category">{E(kind)}</span><p>{E(body)}</p>{link(self.url(url), label)}</div></li>'
                for dt, kind, body, label, url in items
            )
            + "</ul>"
        )

    def bio_inline(self, part):
        if isinstance(part, str):
            return E(part)
        if isinstance(part, list):
            label, route = part
            return link(self.url(route), label)
        label = part["strong"]
        content = link(self.url(part["url"]), label) if "url" in part else E(label)
        return f"<strong>{content}</strong>"

    def home(self):
        profiles = "".join(
            f'<a href="{E(P["profiles"][name])}">{icon(name)}{name}</a>'
            for name in ["Google Scholar", "GitHub", "ORCID", "LinkedIn"]
        )
        profiles += f'<a href="mailto:{E(EMAIL)}">{icon("email")}{E(EMAIL)}</a>'
        selected = "".join(
            f'<article class="featured-item"><span class="micro">{E(p["venue"])} · {p["year"]}</span><h3>{link(p["url"], p["title"])}</h3><p>{E(p["summary"])}</p></article>'
            for p in FEATURED
        )
        bio = []
        for section in P["bioSections"]:
            sentences = ["".join(self.bio_inline(part) for part in para) for para in section["paragraphs"]]
            bio.append(f'<p>{" ".join(sentences)}</p>')
        return f"""<div class="hero"><div><p class="kicker">AI bias &amp; safety</p><h1>{E(NAME)}</h1><p class="role">{E(P["role"])} of DFKI’s {E(P["group"])}</p><p class="intro">{E(P["intro"])}</p><div class="profiles">{profiles}</div></div>
<figure class="portrait">{self.image("ruta-binkyte-headshot.png", "Rūta Binkytė", 'width="238" height="238" fetchpriority="high"')}<figcaption><span class="geo">{icon("location")}{E(P["location"])}</span><span>DFKI · E&amp;E</span></figcaption></figure></div>
<div class="biography">{"".join(bio)}</div>
<section class="home-news" aria-labelledby="news-title"><div class="sectionhead"><h2 id="news-title">Recent news</h2></div>{self.news(P["news"][:4])}<details class="more-news"><summary>Earlier news</summary>{self.news(P["news"][4:])}</details></section>
<section class="featured"><div class="sectionhead"><h2>Selected papers</h2>{link(self.url("papers"), "All papers", "text-link")}</div><div class="featured-grid">{selected}</div></section>"""

    def papers(self):
        result = f'<header class="pageintro"><h1>Papers</h1><p>{link(P["profiles"]["Google Scholar"], "View Scholar profile")}</p></header>'
        groups = sorted({p.get("year") or 0 for p in PAPERS}, reverse=True)
        options = "".join(
            f'<option value="{y}">{y or "Undated"}</option>' for y in groups
        )
        result += f'<div class="filters js-only" hidden><label>Search papers<input id="paper-search" type="search" placeholder="Title, author, or venue"></label><label>Year<select id="paper-year"><option value="">All years</option>{options}</select></label><span id="matches" class="matches" aria-live="polite"></span></div>'
        for y in groups:
            result += f'<section class="yeargroup" data-year="{y}"><h2>{y or "Undated"}</h2><div>'
            for p in (p for p in PAPERS if (p.get("year") or 0) == y):
                alternate_titles = " ".join(p.get("aliases", []))
                result += f'<article class="paper" data-aliases="{E(alternate_titles)}" id="papers--{E(p["id"])}"><span class="venue">{publication_venue(p["venue"], markup=True)}</span><h3>{link(p["url"], p["title"])}</h3>'
                if isinstance(p["authors"], list) and len(p["authors"]) > 12:
                    first = ", ".join(p["authors"][:3])
                    result += f'<details><summary>{E(first)} et al. · All {len(p["authors"])} authors</summary><p>{authorline(p)}</p></details>'
                else:
                    result += f"<p>{authorline(p)}</p>"
                if p.get("versions"):
                    result += '<p class="links">' + " · ".join(
                        link(url, label) for label, url in p["versions"]
                    ) + "</p>"
                if p["summary"]:
                    result += f"<p>{E(p['summary'])}</p>"
                result += "</article>"
            result += "</div></section>"
        return (
            result
            + '<p id="no-papers" hidden>No papers match this search. Try another title, author, venue, or year.</p>'
        )

    def projects(self):
        result = self.intro(
            "Research",
            "Projects",
            "I lead collaborations on deception in AI teams and on how to trace contributions when people and AI create something together.",
        )
        roles = {}
        for project in P["projects"]:
            roles.setdefault(project["role"], []).append(project)
        for role, projects in roles.items():
            result += f'<section class="cv-group"><div class="sectionhead"><h2>{E(role)}</h2></div>'
            for p in projects:
                project_link = ""
                if p.get("link"):
                    project_link = '<div class="links">' + link(p["link"], p["linkLabel"], "text-link") + '</div>'
                result += f'''<article class="project" id="projects--{E(p["id"])}">
<div><p class="micro">{E(p["topic"])}</p><p class="meta">{E(p["meta"])}</p></div>
<div><h3>{E(p["name"])}</h3><p class="question">{E(p["question"])}</p><p>{E(p["description"])}</p>{project_link}</div></article>'''
            result += "</section>"
        return result

    def talks(self):
        groups = [
            ("invited", "Invited talks"),
            ("media", "Media and interviews"),
        ]
        lines = [
            self.intro("Speaking", "Invited talks & media",
                       "Talks, panels and interviews on fairness, causality and AI safety."),
            '<nav class="appearance-nav" aria-label="Talks and media sections">',
        ]
        for section, title in groups:
            lines.append(link(self.url("talks#" + section), title))
        lines.append("</nav>")
        for section, title in groups:
            entries = P["media"] if section == "media" else [
                talk for talk in P["talks"] if talk["section"] == section
            ]
            lines.append(f'<section class="appearances" id="talks--{section}"><h2>{E(title)}</h2>')
            for t in entries:
                when = t["date"]
                display_date = t.get("displayDate") or date_label(when)
                lines.append(f'<article class="appearance" id="talks--{E(t["id"])}">')
                date_html = f'<time class="date" datetime="{E(when)}">{E(display_date)}</time>' if when else '<span></span>'
                lines.append(date_html + '<div class="appearance-copy">')
                title = t["title"] + (": " + t["subtitle"] if t.get("subtitle") else "")
                lines.append(f'<h3>{E(title)}</h3><p class="appearance-host">{E(t["host"])}</p>')
                lines.append(f'<p class="appearance-kind">{E(t["kind"])}</p>')
                if t.get("description"):
                    lines.append(f'<p class="appearance-detail">{E(t["description"])}</p>')
                actions = [(t["action"], t["url"])] if t.get("url") else []
                actions.extend(t.get("links", []))
                if actions:
                    lines.append('<div class="appearance-links">' + "".join(link(url, label) for label, url in actions) + '</div>')
                lines.append("</div>")
                if t.get("photos"):
                    lines.append(self.event_photos(t["photos"], t["title"]))
                elif t.get("image"):
                    photo = self.image(t["image"], "", 'loading="lazy"')
                    image_link = t.get("imageUrl", t["url"])
                    label = t.get("imageLabel", t["action"] + " — " + t["title"])
                    lines.append(f'<a href="{E(image_link)}" class="appearance-photo" aria-label="{E(label)}">{photo}</a>')
                lines.append("</article>")
            lines.append("</section>")
        return "".join(lines)

    def cv_groups(self, titles=None, event_media=None, headings=None):
        sections = []
        for title, rows in cv_sections(P):
            if titles and title not in titles:
                continue
            entries = []
            for when, name, description, *source in rows:
                heading = link(self.url(source[0]), name) if source else E(name)
                if title in ("Research grants", "Awards and honours"):
                    heading = f"<strong>{heading}</strong>"
                media = (event_media or {}).get(name, {})
                photo_links = "".join(link(self.url(url), label) for label, url in media.get("links", []))
                if photo_links:
                    photo_links = '<div class="appearance-links">' + photo_links + '</div>'
                photos = self.event_photos(media["photos"], name) if media.get("photos") else ""
                event_anchor = f' id="service--{E(media["id"])}"' if "id" in media else ""
                row_class = "appearance" if photos else "cvrow"
                entries.append(
                    f'<article class="{row_class}"{event_anchor}><span class="date">{E(when)}</span>'
                    f'<div><h3>{heading}</h3><p>{E(description)}</p>{photo_links}</div>{photos}</article>'
                )
            section_anchor = ' id="service--event-organization"' if titles and title == "Event Organization" else ""
            heading = (headings or {}).get(title, title)
            sections.append(
                f'<section class="cv-group"{section_anchor}><h2>{E(heading)}</h2>'
                f'<div class="cvrows">{"".join(entries)}</div></section>'
            )
        return "".join(sections)

    def awards(self):
        return '<header class="pageintro"><h1>Grants &amp; Awards</h1></header>' + self.cv_groups(
            ["Research grants", "Awards and honours"]
        )

    def service(self):
        return '<header class="pageintro"><h1>Service</h1></header>' + self.cv_groups(
            ["Academic and community service", "Event Organization", "Peer review and programme committees"],
            P.get("serviceMedia"),
        )

    def teaching(self):
        return '<header class="pageintro"><h1>Teaching</h1></header>' + self.cv_groups(
            ["Teaching", "School outreach"], P.get("teachingResources"), {"Teaching": "Courses and summer schools"}
        )

    def cv(self):
        result = self.intro(
            NAME,
            "Curriculum vitae",
            P["role"] + " of DFKI’s " + P["group"] + ", Saarbrücken.",
        )
        result += f'<p class="print-heading">{E(NAME)} · {E(EMAIL)}</p><div class="links noprint">{self.file_link("ruta-binkyte-cv.pdf", "Download PDF", "button")}{self.file_link("ruta-binkyte-cv.tex", "Download LaTeX source", "button secondary")}</div>'
        result += self.cv_groups(event_media=P.get("teachingResources"))
        result += '<section class="cv-group"><h2>Selected publications</h2><div class="cvrows">'
        for p in FEATURED:
            result += f'<article class="cvrow"><span class="date">{p["year"]}</span><div><h3>{link(p["url"], p["title"])}</h3><p>{authorline(p)} · {E(p["venue"])}</p></div></article>'
        return result + "</div></section>"

    def contact(self):
        result = self.intro(
            "Get in touch",
            "Contact",
            "Tell me what you’d like to work on together. I’ll reach out if there’s a fit.",
        )
        options = lambda items: "".join(f"<option>{E(x)}</option>" for x in items)
        return (
            result
            + f"""<div class="contact-layout"><aside class="contact-info"><h2>Write to me</h2><p>{link("mailto:" + EMAIL, EMAIL)}</p><p>{E(P["group"])}<br>{E(P["affiliation"])}<br>{E(P["location"])}</p><p>{link(P["profiles"]["LinkedIn"], "LinkedIn")}</p></aside>
<section class="formpanel"><h2>Collaboration enquiry</h2><p class="small">A few details help me understand your proposal. You can review the formatted message before sending it from your email app.</p>
<form id="enquiry" data-recipient="{E(EMAIL)}" hidden><div class="twocol"><label>Your name<input name="name" autocomplete="name" required maxlength="100"></label><label>Your email<input type="email" name="email" autocomplete="email" required maxlength="200"></label></div>
<div class="twocol"><label>How would you like to collaborate?<select name="kind" required><option value="">Choose a format</option>{options(P["types"])}</select></label><label>Research interest<select name="topic" required><option value="">Choose an interest</option>{options(P["topics"])}</select></label></div>
<label>What would you like to explore together?<textarea name="idea" required maxlength="1200" placeholder="A question, what you could contribute, and any timing or funding details."></textarea></label>
<button class="button" type="submit">Prepare email draft</button></form><noscript><p>To enquire, email {link("mailto:" + EMAIL, EMAIL)} with your name, preferred collaboration format, research interest, and a short proposal.</p></noscript>
<div class="draft" id="draft" hidden><h3 tabindex="-1" id="draft-heading">Your email draft</h3><pre id="draft-text"></pre><div class="form-actions"><a class="button" id="open-mail">Open email app</a><button class="button secondary" id="copy-mail" type="button">Copy message</button></div><p class="small">Send the message in your email app to complete your enquiry.</p><p class="small" id="copy-status" aria-live="polite"></p></div></section></div>"""
        )

    def section(self, page):
        body = getattr(self, page)()
        return f'<div class="wrap {"inside" if page != "home" else ""}" id="{page}" data-page="{page}">{body}</div>'


def json_text(data):
    return json.dumps(data, ensure_ascii=False, indent=2)


def person():
    return {
        "@type": "Person",
        "@id": BASE + "/#person",
        "name": NAME,
        "alternateName": [
            "Ruta Binkyte",
            "Ruta Binkyte-Sadauskiene",
            "Rūta Binkytė-Sadauskienė",
        ],
        "url": BASE + "/",
        "image": BASE + "/assets/ruta-binkyte-headshot.png",
        "jobTitle": P["role"] + " of the " + P["group"],
        "worksFor": {"@type": "Organization", "name": P["affiliation"]},
        "sameAs": list(P["profiles"].values()),
        "email": "mailto:" + EMAIL,
        "knowsAbout": [
            "AI ethics",
            "AI safety",
            "Algorithmic fairness",
            "Causal inference",
            "Multi-agent systems",
            "Mechanistic interpretability",
        ],
    }


def paper_record(p):
    authors = p["authors"]
    data = {
        "@type": "ScholarlyArticle",
        "name": p["title"],
        "url": p["url"],
        "isPartOf": {"@type": "CreativeWork", "name": publication_venue(p["venue"])},
    }
    if p.get("year"):
        data["datePublished"] = str(p["year"])
    if isinstance(authors, list):
        data["author"] = [
            {
                "@type": "Person",
                "name": name,
                **({"@id": BASE + "/#person"} if "binkyt" in name.lower() else {}),
            }
            for name in authors
        ]
    else:
        data["creditText"] = authors
    if p["summary"]:
        data["description"] = p["summary"]
    return data


def metadata(page):
    record = {
        "@type": {
            "home": "ProfilePage",
            "papers": "CollectionPage",
            "talks": "CollectionPage",
            "projects": "CollectionPage",
            "contact": "ContactPage",
        }.get(page, "WebPage"),
        "@id": canonical(page),
        "name": NAV[page] + " · " + NAME,
        "description": DESCRIPTION[page],
        "about": {"@id": BASE + "/#person"},
    }
    if page == "home":
        record["mainEntity"] = {"@id": BASE + "/#person"}
    elif page in ("papers", "talks", "projects"):
        if page == "papers":
            items = [paper_record(p) for p in PAPERS]
        elif page == "projects":
            items = [
                {
                    "@type": "ResearchProject",
                    "name": p["name"],
                    "description": p["description"],
                    "url": canonical(page) + "#projects--" + p["id"],
                }
                for p in P["projects"]
            ]
        else:
            items = [
                {
                    "@type": "CreativeWork",
                    "name": t["title"]
                    + (": " + t["subtitle"] if "subtitle" in t else ""),
                    "url": t.get("url") or canonical("talks") + "#talks--" + t["id"],
                    "description": t["description"],
                }
                for t in P["talks"] + P.get("media", [])
            ]
        record["mainEntity"] = {
            "@type": "ItemList",
            "itemListElement": [
                {"@type": "ListItem", "position": i, "item": item}
                for i, item in enumerate(items, 1)
            ],
        }
    return {"@context": "https://schema.org", "@graph": [person(), record]}


def design_options(appearance):
    groups = [
        ("mark", "Header mark", [("diamond", "Pixel ruby"), ("round", "Round")]),
        ("headings", "Heading font", [("sans", "DM Sans"), ("serif", "Instrument Serif"), ("mono", "Mono")]),
    ]
    fields = []
    for key, legend, options in groups:
        buttons = []
        for value, label in options:
            checked = " checked" if value == appearance[key] else ""
            buttons.append(
                f'<label><input type="radio" name="{key}" value="{value}"{checked}>'
                f'<span class="sample-{value}">{label}</span></label>'
            )
        fields.append(f'<fieldset><legend>{legend}</legend><div>{"".join(buttons)}</div></fieldset>')
    return (
        '<details class="design-options" id="design-options" hidden>'
        '<summary>Design options</summary><div class="design-fields">'
        + "".join(fields) + '</div></details>'
    )


def document(render, page, content, styles, script):
    standalone = render.standalone
    appearance = P["appearance"]
    chooser = design_options(appearance) if standalone else ""
    title = (
        NAME + " · AI Bias & Safety" if page == "home" else NAV[page] + " · " + NAME
    )
    schema = json.dumps(metadata(page), ensure_ascii=False).replace("<", "\\u003c")
    css = (
        "<style>" + styles + "</style>"
        if standalone
        else '<link rel="stylesheet" href="assets/site.css">'
    )
    js = (
        "<script>" + script + "</script>"
        if standalone
        else '<script src="assets/site.js" defer></script>'
    )
    production = (
        ""
        if standalone
        else f'<link rel="canonical" href="{E(canonical(page))}"><link rel="alternate" type="application/json" href="research.json" title="Research profile data"><meta property="og:type" content="website"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(DESCRIPTION[page])}"><meta property="og:url" content="{E(canonical(page))}"><meta property="og:image" content="{E(BASE)}/assets/ruta-binkyte-headshot.png"><meta property="og:image:alt" content="Portrait of Rūta Binkytė"><meta name="twitter:card" content="summary">'
    )
    if standalone:
        production = '<meta name="robots" content="noindex,nofollow">'
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(DESCRIPTION[page])}"><meta name="author" content="{E(NAME)}"><meta name="theme-color" content="#ffffff">{production}
{css}<script type="application/ld+json">{schema}</script></head>
<body data-standalone="{str(standalone).lower()}" data-mark="{E(appearance["mark"])}" data-headings="{E(appearance["headings"])}">{render.bar(page)}<main id="main" tabindex="-1">{content}</main>{render.foot()}{chooser}{js}</body></html>"""


def machine_files():
    href = Render().url
    news = [
        {
            "date": a,
            "category": b,
            "text": c,
            "url": (e if e.startswith("https://") else BASE + "/" + href(e)),
        }
        for a, b, c, _, e in P["news"]
    ]
    data = {
        "profile": person(),
        "navigation": {v: canonical(k) for k, v in NAV.items()},
        "news": news,
        "projects": P["projects"],
        "talks": P["talks"],
        "media": P.get("media", []),
        "cv": P["cv"],
        "serviceMedia": P.get("serviceMedia", {}),
        "publications": [paper_record(p) for p in PAPERS],
        "publicationCoverage": (
            f'{len(PAPERS)} works from {len(CACHE["articles"])} Scholar entries; versions grouped'
            if CACHE["articles"] else "Curated publication records"
        ),
        "scholarLastRefresh": CACHE["updated"],
        "contact": {
            "email": EMAIL,
            "enquiryForm": canonical("contact"),
            "formats": P["types"],
            "topics": P["topics"],
            "response": "I’ll reach out if there’s a fit.",
        },
    }
    (OUT / "research.json").write_text(json_text(data) + "\n")
    llms = [
        f"# {NAME}",
        "> " + DESCRIPTION["home"],
        "",
        P["role"] + " of the " + P["group"] + " at " + P["affiliation"] + ".",
        "Also publishes as Ruta Binkyte and Ruta Binkyte-Sadauskiene.",
        "",
        "## Browse",
        "",
    ]
    llms.extend(f"- [{NAV[k]}]({canonical(k)}): {DESCRIPTION[k]}" for k in NAV)
    llms += [
        "",
        "## Primary sources",
        "",
        f"- [Structured research profile]({BASE}/research.json)",
        f"- [CV PDF]({BASE}/ruta-binkyte-cv.pdf)",
    ]
    llms.extend(f"- [{label}]({url})" for label, url in P["profiles"].items())
    (OUT / "llms.txt").write_text("\n".join(llms) + "\n")
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(f"  <url><loc>{E(canonical(k))}</loc></url>" for k in NAV)
        + "\n</urlset>\n"
    )
    (OUT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n"
    )
    (OUT / ".nojekyll").touch()


def redirects():
    for old, target in json.loads((DATA / "redirects.json").read_text()).items():
        folder = OUT / old.strip("/")
        folder.mkdir(exist_ok=True, parents=True)
        page, _, anchor = target.partition("#")
        destination = canonical(page) + ("#" + page + "--" + anchor if anchor else "")
        relative = "../" * len(Path(old.strip("/")).parts) + Render().url(target)
        (folder / "index.html").write_text(
            f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Page moved · {E(NAME)}</title><meta name="robots" content="noindex"><link rel="canonical" href="{destination}"><meta http-equiv="refresh" content="0;url={E(relative)}"></head><body><a href="{E(relative)}">Continue to {NAV[page]}</a></body></html>'
        )


def build(standalone_path=None, force_pdf=False):
    OUT.mkdir(exist_ok=True)
    shutil.copytree(ASSETS, OUT / "assets", dirs_exist_ok=True)
    raw = make_tex(P, FEATURED)
    (OUT / "ruta-binkyte-cv.tex").write_text(raw)
    cache = ROOT / "cv"
    cache.mkdir(exist_ok=True)
    fingerprint = hashlib.sha256(raw.encode()).hexdigest()
    checksum = cache / "source.sha256"
    saved = cache / "ruta-binkyte-cv.pdf"
    if (
        force_pdf
        or not saved.exists()
        or not checksum.exists()
        or checksum.read_text().strip() != fingerprint
    ):
        if not shutil.which("xelatex"):
            raise SystemExit(
                "CV source changed. Install XeLaTeX and the DejaVu fonts, then rerun the build."
            )
        compile_pdf(raw, saved)
        checksum.write_text(fingerprint + "\n")
    shutil.copyfile(saved, OUT / saved.name)
    css = (
        "\n".join(
            (ASSETS / "fonts" / (name + ".css")).read_text()
            for name in ("instrumentserif", "dmsans")
        )
        + "\n"
        + (ASSETS / "site.css").read_text()
    )
    (OUT / "assets/site.css").write_text(css)
    script = (ASSETS / "site.js").read_text()
    machine_files()
    render = Render()
    for page in NAV:
        (OUT / filename(page)).write_text(
            document(render, page, render.section(page), css, script)
        )
    redirects()
    if standalone_path:
        # Each font binary occurs once per subset even when multiple weights share it.
        unique = {}

        def inline_font(match):
            ref = match.group(1)
            if ref not in unique:
                unique[ref] = asset_uri(ASSETS / ref)
            return "url(" + unique[ref] + ")"

        portable_css = re.sub(r"url\((fonts/[^)]+)\)", inline_font, css)
        licenses = "\n".join(
            x.read_text() for x in sorted((ASSETS / "fonts").glob("*-OFL.txt"))
        )
        portable_css = (
            "/* Bundled font licenses\n"
            + licenses.replace("*/", "* /")
            + "*/\n"
            + portable_css
        )
        portable = Render(standalone=True)
        body = "".join(portable.section(page) for page in NAV)
        Path(standalone_path).write_text(
            document(portable, "home", body, portable_css, script)
        )
    print(f"Built {len(NAV)} pages and {len(PAPERS)} publication records in {OUT}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--standalone",
        metavar="FILE",
        help="Write an additional single-file offline review copy.",
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Recompile the CV PDF even if its source is unchanged.",
    )
    args = parser.parse_args()
    build(args.standalone, args.pdf)
