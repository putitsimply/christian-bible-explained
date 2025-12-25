# Active Context

Current focus:

- Keep content correct and internally consistent.
- Enforce the 500-word limit across content pages (main body text only; exclude the appended footnote definition block).
- Maintain a consistent page structure for easy scanning.
- Keep navigation clear and student-friendly.

Decisions:

- Prefer descriptive, neutral phrasing (“the book describes…”, “the text says…”, “Christians believe…”) especially for miraculous claims.
- Keep changes minimal and consistent with existing tone.
- For glossary help: don’t link the term inline; use a footnote marker on the word (e.g. `God[^gl_god]`) and put a glossary link inside the footnote definition (e.g. `[^gl_god]: ... ([Glossary](glossary.md#god))`).
- Glossary definitions in `glossary.md` are single-line paragraphs; the tooltip sync script assumes this.
- Use `scripts/sync_glossary_tooltips.py` to keep glossary footnotes consistent after edits.

Recent changes:

- Added a neutral home page (`README.md`) and split testament overviews into `old-testament.md` and `new-testament.md`.
- Reworked `SUMMARY.md` into grouped sections (Law/History/Wisdom/Prophets; Gospels/Letters/etc.).
- Added `glossary.md` and linked it in `README.md` and `SUMMARY.md`.
- Standardised glossary usage across content pages to footnote-only tooltips (no inline links on terms), with per-page `[^gl_...]` definitions including a link back to `glossary.md#...`, kept in sync using `scripts/sync_glossary_tooltips.py`.
- Standardised all book pages to the same section headings: `## What this book is`, `## What it contains`, `## Big ideas`.
- Trimmed over-length pages back under 500 words and removed external link-style citations.
- Fixed YAML front matter indentation in `README.md`, `old-testament.md`, and `new-testament.md` to resolve GitBook parsing errors.
