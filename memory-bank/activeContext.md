# Active Context

Current focus:

- Keep content correct and internally consistent.
- Enforce the 500-word limit across all pages.
- Maintain a consistent page structure for easy scanning.
- Keep navigation clear and student-friendly.

Decisions:

- Prefer descriptive, neutral phrasing (“the book describes…”, “the text says…”, “Christians believe…”) especially for miraculous claims.
- Keep changes minimal and consistent with existing tone.
- For glossary help: don’t link the term inline; use a footnote marker on the word (e.g. `priests[^gl_priest]`) and put a glossary link inside the footnote text (e.g. `[^gl_priest]: ... ([Glossary](glossary.md#priest))`).

Recent changes:

- Added a neutral home page (`README.md`) and split testament overviews into `old-testament.md` and `new-testament.md`.
- Reworked `SUMMARY.md` into grouped sections (Law/History/Wisdom/Prophets; Gospels/Letters/etc.).
- Added `glossary.md` and linked it in `README.md` and `SUMMARY.md`, and linked glossary terms inline throughout the book pages (direct links, not footnote annotations).
- Added glossary hover tooltips across all content pages by adding a GitBook footnote annotation for each glossary term used on that page (definitions copied from `glossary.md`). Each occurrence of a glossary term stays linked to the glossary; the footnote marker is included once per term per page to avoid clutter.
- Synced glossary-term occurrences to footnote-only tooltips (no inline links), with per-page `[^gl_...]` definitions including a link back to `glossary.md#...` using `scripts/sync_glossary_tooltips.py`.
- Standardised all book pages to the same section headings: `## What this book is`, `## What it contains`, `## Big ideas`.
- Trimmed over-length pages back under 500 words and removed external link-style citations.
- Fixed YAML front matter indentation in `README.md`, `old-testament.md`, and `new-testament.md` to resolve GitBook parsing errors.
