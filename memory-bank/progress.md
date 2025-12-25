# Progress

What works:

- All 66 book pages exist and follow the same section structure.
- All pages are kept to 500 words or fewer.
- `SUMMARY.md` provides grouped navigation by section/genre.
- A glossary page exists for recurring terms; terms are linked inline to their glossary entries, and footnote annotations provide hover definitions.

Known issues:

- Ongoing spot-checking is still needed for any wording that sounds too certain about beliefs (keep using “the text says…” / “Christians believe…” where appropriate).
- Some pages use many bold mini-headings or lists; this is readable, but could be further simplified if desired.
- GitBook YAML front matter must keep correct indentation (recent parsing errors were caused by broken nesting under `layout:`).
- Pages may exceed 500 words if you count glossary footnote definition lines; the main body text (excluding the appended `[^gl-...]` definitions) stays under 500.

Next steps:

- Do a final read-through for tone consistency and age-appropriate vocabulary across all pages.
- Optionally add a short “How to use this guide” section to `README.md` (teacher/student tips).
