# SciProof website

The documentation and landing page, built with [Astro](https://astro.build) and
[Starlight](https://starlight.astro.build), deployed to GitHub Pages at
<https://hayagrivai-labs.github.io/sciproof/>.

Nothing in `website/` is part of the Python package (it is excluded from the sdist) and the
package keeps zero runtime dependencies.

## Where the content comes from

**Do not edit generated pages.** The site reads the repository at build time
(`scripts/sync.mjs`); every docs page has an "Edit this page" link that points to the original
file.

| Page / section | Source in the repository |
| --- | --- |
| Getting started | `README.md` (sections Install, Quick start, Commands) |
| Concepts | `docs/CONCEPTS.md` |
| Tutorial: NumPy & pandas | `docs/TUTORIAL_NUMPY_PANDAS.md` |
| CLI reference | generated from `sciproof --help`, `capture --help`, `verify --help`, `inspect --help` |
| Manifest format | `docs/MANIFEST.md` (also feeds the manifest explorer on the landing page) |
| Exit codes, CI, FAQ | `docs/EXIT_CODES.md`, `docs/CI.md`, `docs/FAQ.md` |
| Security & threat model | `SECURITY.md` |
| Signing, RO-Crate | `docs/DESIGN_SIGNING.md`, `docs/DESIGN_RO_CRATE.md` |
| Comparison | `docs/COMPETITIVE_ANALYSIS.md` |
| Roadmap | `README.md` (section Roadmap) |
| Contributing | `CONTRIBUTING.md` |
| Changelog | GitHub Releases (fetched at build time) |
| Landing page: demo, levels table, limitations, related tools | `README.md` (Quick start, "What it does and does not prove", "Threat model and limitations", "Related tools") |
| Landing page: sample manifest | produced by running the README's `sciproof capture` command during the build |
| Landing page: tolerance rule | `src/sciproof/numeric.py` (`_numbers_close`); the build fails if that rule changes |
| Version in the header | `pyproject.toml` |
| Contributors, stars, forks, issues, latest release | GitHub API at build time (with `GITHUB_TOKEN` in CI), refreshed in the browser |
| Maintainers | `MAINTAINERS.md` (and `.github/CODEOWNERS` if it exists) |
| PyPI version / install command | `https://pypi.org/pypi/sciproof/json` at build time; the page shows the git install until the package is published |

If a README section that the site needs is renamed, the build stops with a message saying which.
Relative links in the sources (for example `docs/CONCEPTS.md`) are rewritten to site routes, or to
GitHub for files that are not pages.

## Local development

You need Node.js 22 or newer and the SciProof package installed in your Python environment (the
CLI reference is generated from the real CLI):

```bash
python -m pip install -e .        # from the repository root
cd website
npm ci
npm run dev                       # http://localhost:4321/sciproof/
```

```bash
npm run build                     # sync + astro build + internal link check, output in dist/
npm run preview                   # serve dist/
npm run check-links               # only the internal link check
```

Set `GITHUB_TOKEN` to avoid the unauthenticated GitHub API rate limit during the sync. Without
network access the site still builds; the community and changelog sections then say that the data
could not be loaded. `SCIPROOF_BIN` can point at a specific `sciproof` executable.

## Deployment

1. Enable Pages: repository **Settings → Pages → Build and deployment → Source: GitHub Actions**.
2. `.github/workflows/website.yml` builds and deploys on pushes to `main` that touch the sources,
   on every published release, daily (to refresh contributors and stars) and on demand.
3. Create the label used by the website issue form and the broken-link report (once):

   ```bash
   gh label create website --color 0E8A16 \
     --description "Problems with the website or documentation pages" \
     --repo hayagrivai-labs/sciproof
   ```

   (The daily workflow also creates it if it is missing.)

If the repository is renamed or the site moves, update `website/site.config.mjs`.

## Checks on pull requests

`.github/workflows/website-check.yml` builds the site (a broken internal link or anchor fails the
build), checks external links with lychee (reported, not blocking) and runs Lighthouse CI
(`lighthouserc.json`): performance, accessibility, best practices and SEO must each be at least 90.

## Fixing website issues

* **A user reports a problem** through the "Report a problem with this page" link, which opens the
  `website.yml` issue form with the page URL filled in.
* **Wrong or outdated text on a docs page:** edit the source file listed above, not the page.
* **A "Website: broken links detected" issue appears:** the daily run found dead links on the live
  site. The issue lists them and is updated on every run; it is closed automatically when they are fixed.
* **The build fails after a README change:** the message names the section the site expected.

## Privacy and accessibility

No analytics, no cookies, no third-party requests for fonts or avatars (both are copied onto the
site during the build). The only request to another site is the browser asking `api.github.com`
for fresh repository numbers; if it fails, the build-time numbers stay. Animations stop when the
visitor prefers reduced motion, and the pages work without JavaScript.
