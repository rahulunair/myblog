# Technical ramblings — blog repo

Quarto website published to Netlify, live at <https://blog.rahul.onl>.
Author writes as `unrahul`. Repo: `rahulunair/myblog`, branch `master`.

## How it deploys

`quarto publish netlify` renders and uploads the build directly from whichever
machine you run it on. **Nothing builds from the repo** — there is no Netlify
git integration, no CI, no GitHub Pages. Pushing to GitHub does not deploy, and
deploying does not require a push. Do both.

`_publish.yml` holds the Netlify site id (`505e87e4-...`, site
`dashing-malabi-d62add`). Never regenerate that file; without it, publish offers
to create a *new* site instead of updating the live one.

`_site/` is deliberately **not tracked**. macOS and Linux builds differ in
mtime-derived listing attributes and the bootstrap CSS bundle hash, so tracking
it meant ~30 phantom modified files whenever the other machine rendered.

## Machines

Both have Quarto 1.10.18 installed userland (no sudo) at `~/.local/quarto`,
symlinked into `~/.local/bin`.

| | path | notes |
|---|---|---|
| Mac | `~/Coding/blog` | |
| xe-benchy (`rahul@100.109.207.120`, CachyOS, fish) | `~/Coding/blog` | GPU box; blog source tarballs land in `~/Downloads` |

Netlify credential lives at `~/Library/Application Support/quarto/publish/accounts/netlify/`
on macOS and `~/.local/share/quarto/publish/accounts/netlify/` on Linux. Same
token on both, so revoking it revokes both.

## The loop

```bash
cd ~/Coding/blog
quarto preview                       # optional, local check
quarto render
quarto publish netlify --no-prompt --no-browser
git add -A && git commit && git push origin master
```

Pull before starting on the other machine. Verify with
`curl -sS "https://blog.rahul.onl/...?v=N"` — Netlify's edge caches, so a plain
re-fetch can return the previous copy and make a good deploy look broken.

## Theme

- `theme-base.scss` — typography and shape shared by both modes. Space Grotesk
  headings, IBM Plex Sans prose, IBM Plex Mono code, 17px root, 46rem measure,
  square corners. **No mode-specific colors here.**
- `theme-light.scss` / `theme-dark.scss` — the same variable roles, inverted.
  Add a color to one, add it to the other.
- **Dark is the default.** Listing `dark:` first in `_quarto.yml` sets Quarto's
  `darkModeDefault` flag. It does *not* change which stylesheet is tagged
  `quarto-color-alternate` (dark always is), so check `authorPrefersDark` in the
  rendered HTML, not the `<link>` tags. Quarto ignores `prefers-color-scheme`
  unless you set `respect-user-color-scheme: true`.

### Visual system: an annotated systems lab notebook

The site should feel like a fun engineering notebook, not a product landing
page and not an academic PDF. Keep the reading surface calm, then concentrate
color where it helps the reader orient: a marked title, a part heading, a link,
or evidence in a figure.

- Space Grotesk is for headings, IBM Plex Sans is for prose, and IBM Plex Mono
  is for code. They are self-hosted in `assets/fonts/`; do not add a runtime
  Google Fonts import or make the whole site monospace.
- The title banner may use the faint 32px graph-paper grid. Do not put a global
  grid behind long-form prose.
- Post titles are unmarked, high-contrast type preceded by the irregular
  multicolor signal in `assets/theme/signal-strokes.svg`. Level-2 part headings
  use a mint rail. Never run a marker or thick underline through heading text.
  Prose links keep a quiet cyan underline; text selection is yellow and keyboard
  focus is pink.
- Keep corners square. Avoid generic rounded cards, gradients, glass effects,
  animated benchmark charts, ornamental emoji, and novelty interface copy.
- Code, figures, and other evidence may extend 1.5rem beyond the prose measure
  on wide screens. They return to the content width on narrow screens.
- Inline code must remain legible inside marked headings and links in both
  modes. Never globally restyle syntax-token spans or add a client-side
  highlighter merely for decoration; Quarto's static highlighting is the
  baseline.
- Test every visual change in dark and light mode, at desktop and roughly
  390px mobile width. Check keyboard focus, text selection, code comments,
  borders, overflow, and `prefers-reduced-motion`.

The canonical accent palette is shared with the figures. Use these by semantic
role rather than grabbing a new color for each post:

| role | color |
|---|---|
| paper / figure ground | `#fffdf7` |
| ink | `#243447` |
| primary result / mint | `#06d6a0` |
| baseline / signal yellow | `#ffc107` |
| comparison / violet | `#8e6cff` |
| warning or regression / pink | `#e91e63` |
| hot path / orange | `#ff5722` |
| technical path / cyan | `#00bcd4` |
| muted annotation | `#6b7785` |
| grid and border | `#d9e2e8` |
| dark yellow annotation text | `#b98900` |

These are not a substitute for labels. Lines also need distinct dashes or
markers, bars need direct labels where practical, and diagrams must remain
understandable without color.

## Posts

`posts/YYYY-MM-DD-slug.qmd`, flat files. The listing globs `posts/*.qmd`, so a
post in a subdirectory will not appear. Per-post assets go in
`posts/<slug-dir>/`. `posts/_metadata.yml` sets author, toc and
`title-block-banner` for every post.

Frontmatter that matters: `title`, `subtitle`, `date`, `description`,
`categories`, `image`, `image-alt`. Drop any authoring-tool keys
(`archetype`, `audience`, `depth`) — Quarto does not understand them.

Categories are lowercase and reuse the existing vocabulary: `intel`, `arc`,
`arc-pro`, `xe2`, `xpu`, `sglang`, `llm-inference`, `quantization`,
`agentic-coding`, `coding`, `rust`, `ml`, `prose`.

### Search and sharing metadata

The site uses native Quarto canonical links plus two small SEO includes:

- `seo/site-schema.html` defines Rahul Nair (`unrahul`, GitHub `rahulunair`),
  the WebSite, and the Blog once through the shared page layout.
- `filters/blogposting.lua` adds the real page `og:url`, `og:type`, and a
  server-rendered `BlogPosting` object to dated files in `posts/`.

Keep these rules when adding or renaming a post:

- Add a concise `pagetitle` for the browser/search title without shortening
  the visible narrative `title`. Aim for roughly 30–60 characters after the
  site suffix, but preserve clarity over a mechanical cutoff.
- Write a unique `description` of roughly 70–160 characters. State the model,
  hardware or system, operation, and the useful result; do not stuff keywords.
- Set `image` to a 1200px-wide PNG and provide `image-alt`. Never let Quarto
  auto-select an SVG for Open Graph or Twitter cards.
- Keep category names lowercase. When introducing a new category, also add its
  static link to the `topic-cloud` in `index.md`; Quarto's generated category
  controls require JavaScript and are not sufficient on their own.
- Keep drafts as `draft: true`. Preview a specific draft with
  `quarto preview <post>.qmd -M draft:false`; never publish with that override.
- A named draft URL may have a forced Netlify `404!` rule in `_redirects` so
  Quarto's existing empty production placeholder cannot shadow the rule and
  return HTTP 200. Remove that rule in the same change that removes
  `draft: true` and publishes the article.
- Do not add ratings, FAQ schema, an Organization, or a WebSite SearchAction
  unless the visible page and real site functionality support them. This is a
  personal blog, so `Person` is the intentional publisher entity.

After rendering, audit the built homepage and changed posts for canonical,
Open Graph, Twitter, H1/alt coverage, and JSON-LD. If the `discoverability`
skill is installed, its `audit-meta.mjs` and `extract-jsonld.mjs` scripts are
the deterministic checks. The sitemap and RSS feed must exclude drafts.

### Figures

Run every SVG through `npx svgo@3 --multipass` before committing; matplotlib
output is typically 3x larger than it needs to be.

`image:` must be a **PNG**. Quarto will happily pick an SVG for `og:image` and
X, LinkedIn and Slack all silently refuse to render it, so the post unfurls with
no picture. Generate one with
`rsvg-convert -w 1200 -b white <figure>.svg -o card.png`. A PNG also upgrades
the card to `summary_large_image` automatically.

Figures are colorful, lightly xkcd-style explanations on the canonical paper
ground `#fffdf7`. The bright paper against the dark theme is deliberate. Keep
the hand-drawn quality in strokes and annotations, while preserving exact
numbers, readable labels, and honest geometry.

- Author at a 1200px-wide baseline unless the subject needs another aspect
  ratio. SVG is the source format for diagrams and charts; retain the source
  script or editable source beside generated output.
- Every SVG needs `role="img"`, a useful `<title>`, and a `<desc>`. Every Quarto
  figure also needs meaningful alt text and a caption that states the finding,
  not merely "benchmark results."
- Say when a drawing is schematic or not to scale. Do not imply area, length,
  or slope encodes a quantity unless it really does.
- Comparison charts keep the same axes and units. Name the statistic (`p50`,
  `p90`, `p99`, mean, or minimum), sample count, warm-up policy, and important
  measurement conditions in the prose or caption.
- Prefer direct annotations and a small number of purposeful series. Use the
  palette roles above, plus markers, dash patterns, and labels so color is
  never the only carrier of meaning.
- Inspect the optimized SVG in both site modes. Also inspect the generated PNG
  card because social platforms will show that file, not the SVG.

## Writing style

Match the existing posts. Concretely, things that have been asked for and
should not be reintroduced:

- **No em dashes.** Rewrite the sentence; do not swap in a comma mechanically.
- **No "that is the honest number"**, "the honest takeaway", or similar
  self-congratulatory framing.
- **No `X is not Y. It is Z.` constructions.** They pile up fast. Keep the ones
  carrying real information ("not from a number in `config.json`").
- **Never refer to earlier versions of a post.** Readers see one document, not a
  revision history. No "in the first version", "now measured", "since
  publishing", "the original claim". When a post corrects itself, write it as
  the author working the problem through in order.
- Do not link the author's GitHub repos. Hugging Face and Docker Hub links are
  fine when a reader needs them to run something.
- Claims must be scoped to what was measured. "14.8x without writing a kernel"
  is true of the FP8 ladder and false of the whole arc, because a Triton retile
  and a custom collective are inside the final number.
- Practical instructions ("Running it") go near the top; the investigation
  follows for readers who want the reasoning.

### Deep-dive teaching order

For kernel, model-internals, and performance deep dives, teach concrete first,
one abstraction at a time. The post can be long; confusion and filler are the
constraints, not word count.

1. Begin with the smallest real operation a reader can run or picture, such as
   `[1, 2048] -> matrix multiply -> [1, 5120]`.
2. Explain every number in ordinary language before compressing it into
   symbols. Start from the actual model config or measured workload, not an
   arbitrary benchmark shape.
3. Use a tiny worked example when it gives the next abstraction something
   physical to attach to.
4. Keep asking, "What physically happens to the tensor next?" Introduce one
   concept at a time: projection, then Q/K/V, then heads, then GQA, then the
   attention math.
5. Map the toy picture back to the real model, then introduce the compact math.
   Clearly label which facts are verified, which values are derived, and which
   details depend on the framework implementation.
6. Let the optimization narrative follow the investigation: readable baseline,
   measurement, hypothesis, change, result, and the next question. Keep failed
   paths when they teach something; do not manufacture a smooth victory lap.

HTML comments in a `.qmd` file are internal drafting notes. The
`filters/blogposting.lua` filter strips source comments from generated page
HTML. Even so, do not put secrets, credentials, or private URLs in them.

## Structure

Long posts group sections under part-level `##` headings with the sections as
`###`. Parts must be contiguous in file order, because file order is reading
order. `toc-depth: 3` is already set.

## Working from source drops

Long technical posts arrive as tarballs in `~/Downloads` on xe-benchy, e.g.
`qwen38-blog-20260817.tar.gz`. They may contain a `BLOG-UPDATE-*.md` keyed to
the published section names; when present, that file is the source of new
material and the **published post is the source of prose**. The `BLOG.md` in
such a drop is usually stale.

Numbers in those drops are transcribed, not re-derived. Do not invent derived
figures (a 35% byte cut and a 9% throughput gain do not make a "missing 26%").
