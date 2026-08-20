# Blog authoring templates

Copy a template into `posts/`, rename it to the dated post slug, and replace the
placeholders.

```bash
cp templates/flashcard.qmd.template posts/YYYY-MM-DD-topic-card.qmd
cp templates/deep-dive.qmd.template posts/YYYY-MM-DD-deep-dive.qmd
```

`flashcard.qmd.template` owns the bright question card, answer reveal, memory
blocks, and related-card navigation.

`deep-dive.qmd.template` is a flexible annotated-notebook scaffold. Choose the
post archetype first, then retain only the sections that belong to that
investigation.
