# Tech Context

Stack:

- GitBook-flavoured Markdown content.
- Navigation defined in `SUMMARY.md`.

Repo notes:

- No build tooling in this repo; changes are mostly content edits.
- Keep filenames stable where possible, but navigation can be improved by renaming overview pages and updating `SUMMARY.md`.
- `scripts/sync_glossary_tooltips.py` keeps glossary tooltips consistent across content pages by ensuring each used glossary term has a single `[^gl_...]` marker and a matching one-line footnote definition that links back to `glossary.md#...`.
- Run it after editing content pages (especially after adding/removing glossary terms):
  - Check mode (prints files that would change): `python3 scripts/sync_glossary_tooltips.py`
  - Write mode (applies changes): `python3 scripts/sync_glossary_tooltips.py --write`
  - Limit to files: `python3 scripts/sync_glossary_tooltips.py --write --files genesis.md exodus.md`
- Glossary entries in `glossary.md` are expected to have single-line definitions (the script parses one line after each `## <a id="..."></a>Title` heading).
