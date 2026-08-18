# Agent instructions

See **[CLAUDE.md](CLAUDE.md)** for everything: how the site deploys, the two
machines it is written from, theme layout, post conventions, figure handling,
and the writing style rules.

Two things worth knowing before you touch anything:

- Publishing and pushing are **separate**. `quarto publish netlify` deploys;
  `git push` does not. Do both.
- `_site/` is not tracked, and `_publish.yml` must not be regenerated.
