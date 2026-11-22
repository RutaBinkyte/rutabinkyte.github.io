# Rūta Binkytė’s academic website

Open `dist/index.html` in a browser to review the complete site. The separate single-file HTML preview contains the same nine sections, images, fonts and CV downloads. It also works offline. Following a link to a publisher or a recording requires an internet connection.

## Edit and rebuild

Use Python 3.10 or newer. The standard library is sufficient for a normal build. The archive includes a compiled CV. Whenever its content changes, the builder recompiles it using XeLaTeX with DejaVu Serif and DejaVu Sans installed.

```sh
python3 scripts/build.py
python3 scripts/build.py --standalone website-preview.html
```

The first command writes ordinary static files to `dist/`. The second also writes the self-contained review version. Open either directly. To serve `dist/` locally, run `python3 -m http.server 8000 --directory dist` and visit `http://localhost:8000/`.

| Edit | File |
| --- | --- |
| Profile, email, homepage news, invited talks, media, projects, grants and awards, teaching, service, collaboration formats, CV entries | `data/profile.json` |
| Curated paper metadata, summaries, publisher URLs and alternative titles for matching Scholar | `data/selected-papers.json` |
| Full venue names and abbreviations shown in Papers | `data/conference-venues.json` |
| Highlighted papers shown on the homepage and CV | `featuredPapers` in `data/profile.json` |
| Page design and interactions | `assets/site.css` and `assets/site.js` |
| PDF typography and layout | `scripts/cv.py` |
| Section layout, canonical pages and structured exports | `scripts/build.py` |
| Known incoming links from the Owlstown site | `data/redirects.json` |

Put news entries in newest-first order. Dates in the news section label the month of the update. The ECAF update is filed in November 2026 for the August 2027 event. Keep uploads you want to serve in the repository. A talk can link to a recording or programme and include a gallery. Its `photos` list contains pairs of local filenames and captions. Store images in `assets/`. A smaller copy of the first photo with `-thumb` before its extension can be used for the gallery cover.

The standalone preview includes a **Design options** control for comparing the pixel ruby or round monogram and the heading fonts. For the public site, set `appearance.mark` (`diamond` or `round`) and `appearance.headings` (`sans`, `serif` or `mono`) in `data/profile.json` and rebuild.

### Compile the CV

The web CV and its LaTeX source share the same CV entries and selected publication IDs. The CV page provides a downloadable PDF and a standalone `.tex` file. To force a fresh PDF after adjusting layout, run the following command in the project root.

```sh
python3 scripts/build.py --pdf
```

To compile a downloaded source by itself, run `xelatex ruta-binkyte-cv.tex` twice in its directory with DejaVu fonts installed. The browser’s Print command also uses a print stylesheet on the CV page.

## Publish on GitHub Pages when ready

1. On the [RutaBinkyte GitHub account](https://github.com/RutaBinkyte), use a repository named `RutaBinkyte.github.io`. The extracted folder has that name. Commit its contents, including `.github/workflows/website.yml`, at the root of the `main` branch.
2. In repository **Settings → Pages**, select **GitHub Actions** as the build source. The workflow builds `dist/` and uploads that directory. Run **Build and publish academic site** manually for a preview on the GitHub Pages hostname.
3. To enable publication updates, add a repository Actions secret named `SERPAPI_KEY` with a key for the [SerpApi Google Scholar Author API](https://serpapi.com/google-scholar-author-api). Run the workflow once with **Refresh Google Scholar before publishing** selected. Weekly refreshes are scheduled for Monday at 06:27 UTC.
4. After the site opens at `https://rutabinkyte.github.io`, set `rutabinkyte.com` in the repository’s **Settings → Pages → Custom domain**. If Namecheap hosts the DNS, open **Advanced DNS → Host Records**. Set the `www` CNAME to `rutabinkyte.github.io` and use GitHub’s four A records for `@`. Enable HTTPS when the certificate is ready. Check both hostnames and a bookmarked paper link before retiring Owlstown. Keep the domain registration active at Namecheap.

[GitHub’s custom-domain setup](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site) · [Domain verification](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/verifying-your-custom-domain-for-github-pages)

### How updates work

The November 21, 2026 snapshot contains all 30 listings supplied from the author’s Scholar profile. The Papers page groups these into 27 distinct works and links to alternate versions. It uses the publisher’s year and venue for published papers. The homepage features a separate selection of works.

The refresh script reads the public bibliography for Scholar author ID `ujrfUKIAAAAJ`, follows pagination, and saves the complete snapshot in `data/scholar-cache.json`. The archive follows the latest snapshot. Metadata in `data/selected-papers.json` supplies publisher links, full author lists and summaries. Add a preprint’s alternate title to the corresponding work’s `aliases` list when Scholar indexes both versions under different titles.

The workflow commits the snapshot so later builds reuse it. It needs permission to write the cache to the publishing branch. A branch rule requiring pull requests for these updates calls for a pull-request-based cache update workflow. A failed fetch stops the scheduled job before deployment and preserves the last published site. The weekly schedule starts after the workflow is installed on the repository’s default branch and Actions is enabled. SerpApi account quotas and terms apply. Keys stay in the Actions environment. A build of the included draft needs no key.

### Collaboration enquiries

The short survey validates name, reply address, collaboration format, research interest, and proposal. Visitors can review the message, open their email app, or copy it into webmail. The actual send takes place in the visitor’s email client. A request for a paid internship is an enquiry about fit and funding.

### Search and agent access

Each section has its own readable HTML URL, descriptive title, canonical link and page description. Paper entries and talks are visible in the HTML even with JavaScript disabled. The site exports JSON-LD, social-sharing metadata, `sitemap.xml`, `robots.txt`, `research.json`, and a short `llms.txt` index. The one-file review version is marked noindex. The production base URL is set in `data/profile.json`. Static forwarding pages cover the main archived routes and selected paper permalinks. Check outstanding Owlstown permalinks when preparing the final migration.

## Content and assets

Rūta supplied the square homepage portrait. The standing portrait and ECML PKDD galleries come from her previous website. ELSA published the [May 2026 workshop group photo](https://elsa-ai.eu/and-last-but-not-least/). Rūta supplied additional event photographs and the still from her Mokslo sriuba interview. Video thumbnails identify the original recordings. Instrument Serif and DM Sans are distributed with their open font licenses in `assets/fonts/`.

- [Previous homepage](https://www.rutabinkyte.com/) and [previous academic biography](https://www.rutabinkyte.com/pages/about)
- [Author’s professional profile](https://www.linkedin.com/in/ruta-binkyte/)
- [ECAF 2027 organising committee](https://2027.ecafconference.org/organization) and [conference dates](https://2027.ecafconference.org/)
- [DFG International Collaboration funding record at CISPA](https://cispa.de/en/research/funded-projects-and-collaborations)
- [PriSyn at CISPA](https://cispa.de/en/prisyn-project)
- [Probabilistic AI School lecture](https://www.youtube.com/watch?v=yazyhBDT0Lg) and [Interdisciplinary Institute for Societal Computing lecture](https://www.youtube.com/watch?v=PgzE9ds30Eg)

Individual paper records link to their proceedings, DOI, or preprint.
