# Agent instructions

See **[CLAUDE.md](CLAUDE.md)** for everything: how the site deploys, the two
machines it is written from, theme layout, post conventions, figure handling,
and the writing style rules.

Two things worth knowing before you touch anything:

- Publishing and pushing are **separate**. `quarto publish netlify` deploys;
  `git push` does not. Do both.
- `_site/` is not tracked, and `_publish.yml` must not be regenerated.

For deep dives, follow the concrete-first teaching ladder in `CLAUDE.md`: begin
with a real runnable operation, explain every dimension, add one abstraction at
a time, and only then compress it into formal math. Preserve the investigation
as a narrative, including useful failed paths.

Visual work must use the documented annotated-systems-notebook system. Reuse
the canonical pink, yellow, cyan, mint, orange, violet, ink, and paper roles; do not
invent a post-specific palette. SVGs need accessible title/description text,
figures need useful alt text and finding-led captions, and color must be backed
by labels, markers, or line styles. Check dark, light, desktop, and mobile before
calling a theme or figure finished.

For every post, verify the SEO contract in `CLAUDE.md`: concise `pagetitle` and
description, a PNG social card with alt text, lowercase categories, canonical
URL, correct `og:url`, and valid server-rendered `BlogPosting` JSON-LD. Drafts
stay out of the production sitemap, RSS feed, listings, and publish command.
