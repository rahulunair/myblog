# Self-hosted fonts

The site ships Latin-subset WOFF2 files for:

- Space Grotesk, weights 500–700
- IBM Plex Sans, weights 400–600
- IBM Plex Mono, weights 400 and 500

The files came from the Google Fonts distribution and are licensed under the
SIL Open Font License. The corresponding license text is stored beside each
family. Keep the system fallbacks in `theme-base.scss`; they cover characters
outside the packaged Latin subset.
