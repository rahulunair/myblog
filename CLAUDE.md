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

- `theme-base.scss` — typography and shape shared by both modes. Sora headings,
  Fira Code, 17px root, 46rem measure, square corners. **No colors here.**
- `theme-light.scss` / `theme-dark.scss` — the same variable roles, inverted.
  Add a color to one, add it to the other.
- **Dark is the default.** Listing `dark:` first in `_quarto.yml` sets Quarto's
  `darkModeDefault` flag. It does *not* change which stylesheet is tagged
  `quarto-color-alternate` (dark always is), so check `authorPrefersDark` in the
  rendered HTML, not the `<link>` tags. Quarto ignores `prefers-color-scheme`
  unless you set `respect-user-color-scheme: true`.

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

### Figures

Run every SVG through `npx svgo@3 --multipass` before committing; matplotlib
output is typically 3x larger than it needs to be.

`image:` must be a **PNG**. Quarto will happily pick an SVG for `og:image` and
X, LinkedIn and Slack all silently refuse to render it, so the post unfurls with
no picture. Generate one with
`rsvg-convert -w 1200 -b white <figure>.svg -o card.png`. A PNG also upgrades
the card to `summary_large_image` automatically.

Figures are xkcd-style with a cream `#fdfcf8` background, which sits bright
against the dark default. Known, accepted.

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
