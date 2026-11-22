"""Generate a short academic CV from the same records used on the web."""

import re
import shutil
import subprocess
import tempfile
from datetime import date
from pathlib import Path


def tex(value):
    escapes = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return re.sub(r"[\\&%$#_{}~^]", lambda m: escapes[m.group()], str(value))


def date_label(iso):
    if len(iso) == 7:
        return date.fromisoformat(iso + "-01").strftime("%b %Y")
    return iso


def cv_sections(profile):
    yield from profile["cv"]
    talks = []
    for talk in profile["talks"]:
        if talk["section"] != "invited":
            continue  # These events already appear under event organisation.
        when = talk.get("displayDate") or date_label(talk["date"])
        title = talk["title"]
        if talk.get("subtitle"):
            title += ": " + talk["subtitle"]
        details = talk["host"] + " · " + talk["kind"]
        talks.append([when, title, details, talk.get("url") or "talks#" + talk["id"]])
    yield "Invited talks and panels", talks


def make_tex(profile, selected):
    lines = [
        r"""\documentclass[10pt,a4paper]{article}
\usepackage[hmargin=21mm,vmargin=17mm,footskip=10mm]{geometry}
\usepackage{fontspec}
\setmainfont{DejaVu Serif}
\setsansfont{DejaVu Sans}
\usepackage{xcolor,hyperref}
\definecolor{forest}{HTML}{174E40}
\hypersetup{colorlinks=true,urlcolor=forest,pdftitle={Curriculum vitae — Rūta Binkytė},pdfauthor={Rūta Binkytė}}
\setlength{\parindent}{0pt}
\newcommand{\cvsection}[1]{\section*{\normalfont\Large\color{forest}#1}}
\newcommand{\entry}[3]{\noindent\begin{minipage}[t]{.18\linewidth}\small\sffamily #1\end{minipage}\hfill\begin{minipage}[t]{.79\linewidth}\textbf{#2}\par #3\end{minipage}\par\vspace{4pt}}
\begin{document}""",
        r"{\Huge " + tex(profile["name"]) + r"}\hfill{\sffamily Curriculum vitae}\par",
        r"\vspace{5pt}{\large " + tex(profile["role"]) + r"}\par",
        tex(profile["group"] + " · DFKI · " + profile["location"]) + r"\par",
        r"\href{mailto:"
        + profile["email"]
        + "}{"
        + tex(profile["email"])
        + r"} \quad \href{"
        + profile["base"]
        + r"}{rutabinkyte.com} \quad \href{"
        + profile["profiles"]["LinkedIn"]
        + r"}{LinkedIn}\par",
        r"\vspace{9pt}" + tex(profile["background"]) + r"\par",
    ]
    for name, rows in cv_sections(profile):
        lines.append(r"\cvsection{" + tex(name) + "}")
        for when, title, desc, *source in rows:
            heading = tex(title)
            if source:
                url = source[0]
                if not url.startswith("https://"):
                    page, _, anchor = url.partition("#")
                    url = f"{profile['base']}/{page}.html"
                    if anchor:
                        url += f"#{page}--{anchor}"
                url = url.replace("%", r"\%").replace("#", r"\#")
                heading = r"\href{" + url + "}{" + heading + "}"
            lines.append(
                r"\entry{" + tex(when) + "}{" + heading + "}{" + tex(desc) + "}"
            )
    lines.append(r"\cvsection{Selected publications}")
    for p in selected:
        lines.append(
            r"\noindent\begin{minipage}{\linewidth}\textbf{\href{"
            + p["url"]
            + "}{"
            + tex(p["title"])
            + r"}}\par "
            + tex(
                ", ".join(p["authors"])
                + ". "
                + p["venue"]
                + ", "
                + str(p["year"])
                + "."
            )
            + r"\end{minipage}\par\vspace{6pt}"
        )
    lines.extend(
        [
            r"\vspace{4pt}\href{"
            + profile["base"]
            + r"/papers.html}{Publication archive and research links}",
            r"\end{document}",
        ]
    )
    return "\n".join(lines) + "\n"


def compile_pdf(source, target):
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "ruta-binkyte-cv.tex"
        path.write_text(source, encoding="utf-8")
        for _ in range(2):
            subprocess.run(
                ["xelatex", "-interaction=nonstopmode", "-halt-on-error", path.name],
                cwd=folder,
                check=True,
                stdout=subprocess.DEVNULL,
            )
        shutil.copyfile(path.with_suffix(".pdf"), target)
