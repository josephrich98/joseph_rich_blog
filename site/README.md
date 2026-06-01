# joseph-rich.com — website (`site/`)

The public blog at [joseph-rich.com](https://joseph-rich.com). It's a Jekyll site
built on the [academicpages](https://github.com/academicpages/academicpages.github.io)
theme (a Minimal Mistakes fork), trimmed to a blog with **About**, **Blog (with
tags)**, **Publications**, and **CV**. Comments are powered by
[giscus](https://giscus.app) (GitHub Discussions). It deploys on **Vercel**.

> The rest of this repo (`../posts/`, `../tests/`, each post's `environment.yml`, …) is the
> notebook/PDF authoring toolchain and is unrelated to this website.

## Local development

Requires Ruby 3.x (see `.ruby-version`) and Bundler.

```bash
cd site
bundle install
bundle exec jekyll serve      # http://localhost:4000
```

> **Note for older Linux (e.g. RHEL/CentOS 8, glibc < 2.29):** the precompiled
> `nokogiri`/`sass-embedded` gems in `Gemfile.lock` need a newer glibc than the
> one on the box. Compile the native gems from source locally with:
> `bundle config set --local force_ruby_platform true && bundle install`.
> This writes `.bundle/config` (git-ignored) and does **not** affect Vercel,
> which uses the precompiled Linux gems.

## Content workflow

### Blog posts
Create `_posts/YYYY-MM-DD-title.md`:

```yaml
---
title: "My post title"
date: 2026-05-31
excerpt: "One-line summary shown in the blog list."
tags:
  - machine learning
  - bioinformatics
comments: true
---
Body in Markdown…
```

`tags:` are per-post labels (think categories) shown at the bottom of each post.
They aren't a top-level nav section, but clicking a tag opens a filtered list of
posts with that tag (the `/tags/` page). See `_posts/2026-05-31-welcome.md`.

### Publications
Each paper is a file in `_publications/` (`title`, `category`
[`manuscripts` / `conferences` / `preprints`], `excerpt` = abstract, `paperurl`,
`citation`). To bulk-generate from a **Google Scholar** export:

1. On your Scholar profile, select papers → **Export → BibTeX**, save as
   `markdown_generator/pubs.bib`.
2. `cd markdown_generator && python pubsFromBib.py` (needs `pip install pybtex`).
3. Commit the generated `_publications/*.md`.

(There's no reliable *live* Scholar API — Scholar blocks scrapers — so this is a
periodic manual export rather than an automatic sync.)

### CV
Replace `files/CV.pdf`; it's linked from the `/cv/` page. Edit the prose in
`_pages/cv.md`.

### About / sidebar / nav
- `_pages/about.md` — the home page bio.
- `_config.yml` `author:` block — sidebar name, email, GitHub, LinkedIn, avatar
  (`images/profile.png`).
- `_data/navigation.yml` — the header menu.

## One-time setup

### 1. giscus comments
Discussions are already enabled on `josephrich98/joseph_rich_blog`. Then:

1. Create a Discussions **category** named **`Comments`** (type: *Announcements*).
2. Go to <https://giscus.app>, enter the repo `josephrich98/joseph_rich_blog`,
   choose mapping **pathname** and category **Comments**.
3. Copy the generated **`data-repo-id`** and **`data-category-id`** into
   `_config.yml` under `giscus:` (`repo_id` and `category_id`).

Until those two IDs are set, posts show a "giscus is not configured yet" notice
instead of the comment box.

### 2. Vercel
1. In Vercel, **Add New → Project** and import `josephrich98/joseph_rich_blog`.
2. Set **Root Directory** to **`site`** (Settings → General). Vercel auto-detects
   the Jekyll framework; `vercel.json` here pins the build command
   (`bundle exec jekyll build`) and output (`_site`).
3. Deploy, then add the **`joseph-rich.com`** custom domain (Settings → Domains)
   and point your DNS at Vercel.

`Gemfile.lock` is committed (with the `x86_64-linux` platform) so Vercel's build
is reproducible — don't delete it.
