---
title: "How This Blog Is Built: A Reproducible Pipeline for Scientific Writing"
author: "Joseph Rich"
date: "2026-06-01"
# Blog metadata (ignored by pandoc/Eisvogel; consumed by scripts/sync_posts.py)
excerpt: "A tour of the stack behind joseph-rich.com — Vercel, Jekyll, giscus, Jupyter/Colab, conda + Docker, pytest + GitHub Actions, a pre-commit publish hook, and Markdown-with-LaTeX — and the one principle tying them together: a blog post should be as reproducible as the experiment it describes."
tags:
  - reproducibility
  - tooling
  - open science
  - jekyll
  - continuous integration
titlepage: true
toc: true
toc-own-page: true
colorlinks: true
linkcolor: NavyBlue
urlcolor: NavyBlue
listings: true
---

# Why a blog deserves a build system

Most of what I write here makes a quantitative claim, and a quantitative claim is
only as trustworthy as the analysis behind it. In a paper, the apparatus that
makes a result believable — version control, a pinned environment, a test that
re-runs the analysis end-to-end — lives off to the side, in a supplement nobody
reads. I wanted the blog to put that apparatus *first*. Every figure here should
be regenerable from a notebook, every notebook should run in a known
environment, and every claim that survives to the published page should have
passed a test on the way there.

That goal sounds heavy, but the day-to-day is the opposite. My entire workflow as
an author is three commands:

```bash
# write posts/<slug>/main.md, then:
git add -A
git commit -m "Add post: ..."
git push
```

Everything downstream — rendering the PDF, publishing the web page, running the
analysis, testing that it all still works — is automated. This post is a tour of
that automation: what each piece does, why I chose it, and how they compose into
the pipeline in Figure 1.

![**Figure 1.** One source of truth — `posts/<slug>/main.md` plus its notebook —
fans out to a PDF, a tested analysis, and a live web page. The top lane is
everything I touch by hand; the bottom lane is automatic.](figures/pipeline.png)

# The author's-eye view: one source of truth

Each post is a self-contained directory:

```text
posts/<slug>/
  main.md            # the article: Markdown + YAML front matter + LaTeX math
  notebook.ipynb     # the analysis that generates every figure
  figures/           # generated plots (git-ignored)
  scripts/           # plotting / analysis code, runnable standalone
  data/              # datasets + a README describing each source (git-ignored)
  environment.yml    # the conda environment for *this* post
  Dockerfile         # a container that reproduces *this* post
```

The article itself is a plain Markdown file. Prose is Markdown; math is LaTeX,
delimited by `$…$` for inline symbols and `$$…$$` for display equations. So a
sentence can carry a real claim — for a diagnostic test with sensitivity
$\mathrm{Se}$ and specificity $\mathrm{Sp}$ applied to a population with disease
prevalence $\pi$, the post-test probability of disease given a positive result
is

$$
\Pr(D^{+}\mid T^{+}) \;=\;
\frac{\mathrm{Se}\,\pi}{\mathrm{Se}\,\pi + (1-\mathrm{Sp})(1-\pi)},
$$

— and that same source file renders to a typeset PDF *and* to a web page, with
the math intact in both. Writing in Markdown rather than HTML or a CMS means the
post is diffable, greppable, reviewable in a pull request, and outlives any
particular renderer.

The rest of the directory exists so that the numbers in that prose are
*defensible*. The notebook produces the figures; the scripts hold any analysis
worth reusing; the `environment.yml` and `Dockerfile` pin exactly what it takes
to run them. Nothing in the published page is hand-drawn or hand-typed from a
result I can't reproduce.

# The website: Jekyll, a theme, and Vercel

## Jekyll for the site, academicpages for the theme

The site is a [Jekyll](https://jekyllrb.com/) static site. Jekyll turns a folder
of Markdown into a fast, dependency-free set of HTML pages, and — the reason I
chose it over a hand-rolled framework — it has a deep ecosystem of ready-made
themes. I use [**academicpages**](https://github.com/academicpages/academicpages.github.io),
a fork of [Minimal Mistakes](https://github.com/mmistakes/minimal-mistakes) built
for academics, trimmed down to the three things I actually need: an **About**
page, a **Blog** with tag filtering, and a **Publications** list. Because the
publications list can be generated from a BibTeX export of my Google Scholar
profile, the academic furniture of the site maintains itself.

A static site is the right tool here for the same reason a simple model often
beats a complex one: there is no server to run, no database to corrupt, no
attack surface to patch. The output is just files.

## Vercel for hosting

Those files are served by [Vercel](https://vercel.com/). I point Vercel at the
GitHub repository, set the root directory to `site/`, and it does the rest: on
every push to `main` it runs `bundle exec jekyll build` and deploys the result
to `joseph-rich.com` behind a global CDN, with HTTPS and the custom domain
handled for me. There is no deploy step in my workflow — "deploy" *is* "merge to
`main`."

The appeal is simplicity. I never think about web servers. A push becomes a live
site in under a minute, every pull request gets its own preview URL so I can see
a draft exactly as it will appear before it goes public, and committing
`Gemfile.lock` keeps Vercel's build byte-for-byte reproducible against my local
one.

## giscus for comments

Comments are powered by [**giscus**](https://giscus.app/), which stores each
discussion thread in this repository's **GitHub Discussions**. I chose it for
three reasons:

- **It's built on GitHub.** The comments live next to the code, in the same
  account that already hosts everything else — no third-party comment database to
  own or migrate.
- **It requires a GitHub login.** Commenting means authenticating with GitHub,
  which by itself filters out essentially all drive-by spam. The barrier is low
  for the technical audience this blog is written for and high for bots.
- **No ads, no tracking, free.** Unlike hosted comment widgets, giscus serves no
  advertising and sells no data. It's an open-source script talking to the GitHub
  API.

Setup is a one-time affair: enable Discussions, install the giscus GitHub app,
and drop the repository and category IDs into the Jekyll config.

# The analysis: notebooks you can actually re-run

## Jupyter for the figures, Colab for zero-install access

Every figure starts life in a [Jupyter notebook](https://jupyter.org/). The
notebook is the interactive workbench — load the data, fit the model, plot it,
see the result inline, iterate — and it doubles as an honest record of how each
figure was made. Crucially, the notebook *writes the figures into* `figures/`,
so the article and the analysis can never silently drift apart: regenerate the
figure and the post updates.

For readers who don't want to install anything, each notebook also opens
directly in [**Google Colab**](https://colab.research.google.com/) from a badge
at the top. A curious reader can re-run my analysis in their browser, change a
parameter, and watch the figure move — no local setup at all. Interactivity is
the point: a static PNG asserts a result; a runnable notebook lets you *check*
it.

## conda and Docker: one environment per post

"It runs on my machine" is not reproducibility. Each post therefore pins its own
environment two ways:

- **conda.** A per-post `environment.yml` lists exact versions of Python and
  every library the notebook imports. The environment is *named after the post*,
  so posts never share a dependency set. A two-year-old post can pin an old
  `numpy` while a new one uses the latest, and neither breaks the other.
- **Docker.** A per-post `Dockerfile` builds that conda environment inside a
  container and registers it as a Jupyter kernel, so the notebook runs
  identically on any machine with Docker — no conda required, nothing touching
  the host.

Isolating environments per post is deliberate. A single shared environment is a
slow-motion dependency crisis: every new library risks an upgrade that quietly
changes an old figure. Per-post environments make each article a sealed unit
that reproduces on its own, indefinitely.

# Quality control: tests, CI, and a publish hook

This is the part most personal sites skip, and it's the part I care about most. A
blog that makes numerical claims should be tested like software that makes
numerical claims.

## pytest discovers and exercises every post

A [pytest](https://docs.pytest.org/) suite walks `posts/`, discovers every post
automatically, and runs three independent checks against each one:

1. **The PDF builds.** `main.md` renders to PDF through pandoc and the Eisvogel
   LaTeX template. If an equation or a figure path is broken, this fails.
2. **The notebook runs (lax).** The notebook executes top to bottom and must
   complete without raising — using [`nbval`](https://github.com/computationalmodelling/nbval)
   in `--nbval-lax` mode, which ignores the *stored* outputs and only checks that
   nothing errors.
3. **The notebook reproduces its outputs (strict).** The notebook re-runs and
   each cell's output must match what's committed, exactly.

Running both a **lax** and a **strict** notebook check is intentional, and it's
the diagnostic trick I'd most recommend stealing. The two failures mean very
different things:

- A **lax** failure means the code is *broken* — an exception, a missing import,
  an API that changed under me.
- A **strict** failure means the code still runs but the *result moved* — a new
  library version nudged a number, or a computation wasn't as deterministic as I
  thought.

Separating "it crashed" from "the answer changed" turns a red checkmark into an
actual diagnosis. Genuinely non-deterministic cells (timestamps, random draws,
plot objects) are marked to be ignored by the strict check, so a strict failure
is always a real signal, never noise.

## GitHub for version control, GitHub Actions for CI

The whole repository lives on [GitHub](https://github.com/), which gives me
version history, pull requests, and Discussions (the same Discussions that back
the comments). On top of that, [**GitHub Actions**](https://github.com/features/actions)
runs the entire pytest suite — PDF builds and both notebook checks, across every
post — automatically on every push and every pull request. It spins up a clean
Ubuntu machine, installs the conda environments and a LaTeX toolchain from
scratch, regenerates the figures, and runs the tests. Because the runner starts
empty, "passes in CI" means "reproduces on a machine that has never seen my
files" — exactly the property I want.

The payoff is that I can't quietly ship a broken post. If a notebook stops
running or a figure stops reproducing, the check goes red before anything reaches
the site.

## Feature branches keep the live site stable

New posts are written on a **feature branch**, never on `main`. Vercel only
deploys `main`, so a half-finished draft can be committed, pushed, and run
through CI as many times as I like without ever touching the public site. When
the branch is green and the writing is done, I merge to `main` — and *that* merge
is what publishes. The branch is the draft; `main` is print.

## A pre-commit hook publishes automatically

The bridge from `posts/<slug>/main.md` to a Jekyll page is a committed
**pre-commit hook**. On every commit it runs a small script
(`sync_posts.py`) that:

- maps the post's front matter into the Jekyll format the theme expects,
- copies the referenced figures into the site's image folder and rewrites the
  paths,
- translates inline `$…$` math into the `$$…$$` form the site's MathJax renders,
  and
- appends a footer linking back to the post's source folder on GitHub, so any
  reader can reproduce the analysis.

Because this runs at commit time, the website copy is *always* in sync with the
authoritative `main.md` — I never edit the published page by hand, and I can
never forget to. Authoring and publishing collapse into a single `git commit`.

# Details that keep the repository honest

A few smaller choices do disproportionate work.

**Citations have to resolve.** Before I reference a paper, I check its DOI
against [doi2bib](https://doi2bib.org/) (`https://doi2bib.org/bib/<DOI>`); if the
DOI doesn't return a valid bib entry, the citation doesn't go in. It's a cheap,
mechanical guard against the broken or imaginary references that creep into
informal writing — and the final notebook cell of a data-driven post re-checks
that every DOI still resolves.

**Data and figures are git-ignored.** The repository tracks *code and prose*, not
the artifacts they produce. Generated figures and downloaded datasets are
excluded from version control, which keeps the repo small and fast to clone and
avoids committing large or redistribution-restricted files. CI regenerates the
figures from the notebooks before testing, so nothing is lost — the recipe is
versioned, the output is disposable. (The `data/README.md` still documents every
source and its license, so the provenance survives even though the bytes don't.)

**Lean for proofs that have to be right.** When a post leans on a piece of
mathematics I want to be *certain* of — not just plausible — I can formalize it
in [Lean](https://leanprover.github.io/), a proof assistant that mechanically
verifies each step. Most posts never need it, but for a subtle inequality or a
correctness argument it's the difference between "I checked it carefully" and
"a theorem prover checked it."

# The whole loop, in one breath

Put together, the system means my job is to *write*. I open `main.md`, write
prose and equations in Markdown and LaTeX, build the figures in a notebook, and
then commit and push. From there:

1. the **pre-commit hook** converts the post into a web page and stages it;
2. **GitHub** stores the history and opens the pull request;
3. **GitHub Actions** rebuilds the PDF and re-runs every notebook, lax and
   strict, on a clean machine;
4. once it's green I merge to **`main`**, and
5. **Vercel** builds the Jekyll site and deploys it to `joseph-rich.com`.

No manual build, no manual deploy, no copy-paste into a CMS, and — most
importantly — no published claim that hasn't survived a test. The blog is held
to the same standard as the research it describes: reproducible, version
controlled, and continuously verified. That's the whole point. If a result is
worth publishing, it's worth being able to run again.

# Recommendations, if you're building something similar

A few things I'd tell a past version of myself:

- **Pick a static site with a theme ecosystem.** The fastest path to a site you
  won't fight is a mature theme on Jekyll, Hugo, or Astro. Don't hand-roll the
  CSS for a blog.
- **Write in Markdown, not in your CMS.** Plain text files are diffable,
  reviewable, and portable across renderers. Your words should outlive your
  tooling.
- **Test the analysis, not just the prose.** The lax/strict split is worth
  adopting wholesale: it tells you *whether your code broke or your answer
  moved*, which are different problems with different fixes.
- **Isolate environments aggressively.** One pinned environment per post (or per
  project) is the cheapest insurance against bit-rot you can buy.
- **Make publishing a side effect of committing.** A commit hook plus a
  push-to-deploy host removes the two steps most likely to go stale: the manual
  build and the manual upload.
- **Use branches as drafts.** Gating deploys on `main` lets you commit freely,
  run CI repeatedly, and publish only when you mean to.

None of these pieces is exotic. The leverage is in composing them so that the
boring, error-prone work — building, deploying, testing, keeping copies in sync —
happens on its own, and the only thing left for me to do is the part that
actually matters: the writing.
