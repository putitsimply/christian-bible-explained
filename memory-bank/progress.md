# Progress

What works:

- All 66 book pages exist and follow the same section structure.
- Content pages are kept to 500 words or fewer in the main body (the appended footnote definition block is excluded from the count).
- `SUMMARY.md` provides grouped navigation by section/genre.
- A glossary page exists for recurring terms; content pages use footnote markers (e.g. `God[^gl_god]`) and the footnote definition includes a link back to the glossary.

Known issues:

- Ongoing spot-checking is still needed for any wording that sounds too certain about beliefs (keep using “the text says…” / “Christians believe…” where appropriate).
- Some pages use many bold mini-headings or lists; this is readable, but could be further simplified if desired.
- GitBook YAML front matter must keep correct indentation (recent parsing errors were caused by broken nesting under `layout:`).
- Reference/navigation pages (like `glossary.md`) are exceptions to the 500-word limit.

Next steps:

- Do a final read-through for tone consistency and age-appropriate vocabulary across all pages.
- Optionally add a short “How to use this guide” section to `README.md` (teacher/student tips).
