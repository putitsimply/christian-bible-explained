# Active Context

Current focus:

- Keep content correct and internally consistent.
- Enforce the 500-word limit across all pages.
- Maintain a consistent page structure for easy scanning.
- Keep navigation clear and student-friendly.

Decisions:

- Prefer descriptive, neutral phrasing (“the book describes…”, “the text says…”, “Christians believe…”) especially for miraculous claims.
- Keep changes minimal and consistent with existing tone.
- For glossary help: keep the term as a normal link to `glossary.md#...`, and attach the definition as a separate GitBook footnote marker (with a space) so the link remains clickable.

Recent changes:

- Added a neutral home page (`README.md`) and split testament overviews into `old-testament.md` and `new-testament.md`.
- Reworked `SUMMARY.md` into grouped sections (Law/History/Wisdom/Prophets; Gospels/Letters/etc.).
- Added `glossary.md` and linked it in `README.md` and `SUMMARY.md`, and linked glossary terms inline throughout the book pages (direct links, not footnote annotations).
- Added glossary hover tooltips across all content pages by adding a GitBook footnote annotation for each glossary term used on that page (definitions copied from `glossary.md`). Each occurrence of a glossary term stays linked to the glossary; the footnote marker is included once per term per page to avoid clutter.
- Standardised all book pages to the same section headings: `## What this book is`, `## What it contains`, `## Big ideas`.
- Trimmed over-length pages back under 500 words and removed external link-style citations.
- Fixed YAML front matter indentation in `README.md`, `old-testament.md`, and `new-testament.md` to resolve GitBook parsing errors.
