#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


GLOSSARY_PATH = Path("glossary.md")
MD_GLOB = "*.md"
SKIP_FILES = {GLOSSARY_PATH.name, "AGENTS.md"}


ANCHOR_HEADING_RE = re.compile(r'^##\s+<a id="(?P<id>[^"]+)"></a>(?P<title>.*)$')
FOOTNOTE_DEF_RE = re.compile(r"^\[\^(?P<id>[^\]]+)\]:\s*(?P<text>.*)\s*$")

# `[Bible[^gl_bible]](glossary.md#bible)` -> `<a href="glossary.md#bible" title="...">Bible</a>`
GLOSSARY_LINK_WITH_INNER_FOOTNOTE_RE = re.compile(
    r"\[(?P<label>[^\]]+?)\[\^(?P<fnid>[^\]]+?)\]\]\(glossary\.md#(?P<anchor>[^)]+)\)"
)

# Normal glossary links (used for conversion)
GLOSSARY_LINK_RE = re.compile(r"\[(?P<label>[^\]]+?)\]\(glossary\.md#(?P<anchor>[^)]+)\)")
GLOSSARY_HTML_LINK_RE = re.compile(
    r'<a\s+href="glossary\.md#(?P<anchor>[^"]+)"(?P<attrs>[^>]*)>(?P<label>.*?)</a>'
)


def parse_glossary_definitions(glossary_text: str) -> dict[str, str]:
    definitions: dict[str, str] = {}
    lines = glossary_text.splitlines()
    i = 0
    while i < len(lines):
        m = ANCHOR_HEADING_RE.match(lines[i])
        if not m:
            i += 1
            continue
        anchor_id = m.group("id").strip()
        i += 1

        while i < len(lines) and not lines[i].strip():
            i += 1
        if i >= len(lines):
            break

        # Definitions in this repo are single-paragraph, single-line.
        definition_line = lines[i].strip()
        definitions[anchor_id] = definition_line
        i += 1
    return definitions


def split_trailing_footnote_block(lines: list[str]) -> tuple[list[str], list[str]]:
    """
    Split `lines` into (body_lines, trailing_footnote_block_lines).

    The trailing block is defined as the maximal suffix consisting only of:
    - blank lines
    - footnote definition lines
    """
    i = len(lines)
    while i > 0:
        line = lines[i - 1]
        if not line.strip():
            i -= 1
            continue
        if FOOTNOTE_DEF_RE.match(line):
            i -= 1
            continue
        break
    return lines[:i], lines[i:]


def extract_footnote_defs(block_lines: list[str]) -> tuple[dict[str, str], list[str]]:
    defs: dict[str, str] = {}
    other_lines: list[str] = []
    for line in block_lines:
        m = FOOTNOTE_DEF_RE.match(line)
        if m:
            footnote_id = m.group("id")
            defs[footnote_id] = m.group("text").strip()
        else:
            other_lines.append(line)
    return defs, other_lines


def find_footnote_refs_outside_defs(lines: list[str]) -> set[str]:
    refs: set[str] = set()
    for line in lines:
        if FOOTNOTE_DEF_RE.match(line):
            continue
        for m in re.finditer(r"\[\^(?P<id>[^\]]+)\]", line):
            refs.add(m.group("id"))
    return refs


def ordered_unique(seq: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in seq:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def html_escape_attr(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def sync_file(path: Path, glossary_defs: dict[str, str]) -> tuple[bool, str]:
    original = path.read_text(encoding="utf-8")

    text = original

    # Remove any old glossary footnote definition lines entirely (we regenerate tooltips on links).
    text = re.sub(r"^\[\^gl_[^\]]+\]:.*\n?", "", text, flags=re.M)

    # Remove any stray numeric/glossary footnote reference lines (these are never valid on their own).
    text = re.sub(r"^\[\^\d+\]\s*\n?", "", text, flags=re.M)
    text = re.sub(r"^\[\^gl_[^\]]+\]\s*\n?", "", text, flags=re.M)

    # 1) Fix the common broken pattern where the footnote marker is inside the link label.
    def move_inner_fn(m: re.Match[str]) -> str:
        label = m.group("label")
        anchor = m.group("anchor")
        return f"[{label}](glossary.md#{anchor})"

    text = GLOSSARY_LINK_WITH_INNER_FOOTNOTE_RE.sub(move_inner_fn, text)

    # Remove any existing glossary/numeric footnote markers that were previously used for tooltips.
    text = re.sub(r"[ \t]*\[\^gl_[^\]]+\]", "", text)
    text = re.sub(r"[ \t]*\[\^\d+\]", "", text)

    lines = text.splitlines()
    body_lines, trailing_block = split_trailing_footnote_block(lines)
    existing_defs, trailing_other = extract_footnote_defs(trailing_block)

    body_text = "\n".join(body_lines)

    # 2) Convert all glossary links into HTML anchors with `title` tooltips (definition from glossary.md).
    # Remove any leftover footnote refs that immediately follow a glossary link.
    body_text = re.sub(
        r"(\]\(glossary\.md#[^)]+\))\s*\[\^[^\]]+\]",
        r"\1",
        body_text,
    )
    body_text = re.sub(
        r'(</a>)\s*\[\^[^\]]+\]',
        r"\1",
        body_text,
    )

    def md_link_to_html(m: re.Match[str]) -> str:
        label = m.group("label")
        anchor = m.group("anchor").strip()
        definition = glossary_defs.get(anchor)
        if not definition:
            return m.group(0)
        title = html_escape_attr(definition)
        return f'<a href="glossary.md#{anchor}" title="{title}">{label}</a>'

    body_text = GLOSSARY_LINK_RE.sub(md_link_to_html, body_text)

    def html_link_update_title(m: re.Match[str]) -> str:
        anchor = m.group("anchor").strip()
        attrs = m.group("attrs") or ""
        label = m.group("label")
        definition = glossary_defs.get(anchor)
        if not definition:
            return m.group(0)
        title = html_escape_attr(definition)
        attrs_wo_title = re.sub(r'\s+title="[^"]*"', "", attrs)
        return f'<a href="glossary.md#{anchor}"{attrs_wo_title} title="{title}">{label}</a>'

    body_text = GLOSSARY_HTML_LINK_RE.sub(html_link_update_title, body_text)

    # 4) Rebuild trailing footnote block (keep any non-glossary defs from the original file too).
    new_body_lines = body_text.splitlines()
    refs = find_footnote_refs_outside_defs(new_body_lines)

    # Drop any glossary footnote definitions (gl_*) always.
    new_defs: dict[str, str] = {k: v for k, v in existing_defs.items() if not k.startswith("gl_")}

    # Also drop numeric defs if they are no longer referenced (these were previously glossary tooltips).
    for def_id in list(new_defs.keys()):
        if def_id.isdigit() and def_id not in refs:
            del new_defs[def_id]

    rebuilt_block: list[str] = []

    # Keep any remaining (non-glossary) footnote definitions that are still referenced.
    other_def_ids = [k for k in new_defs.keys() if k in refs]
    if other_def_ids:
        if not rebuilt_block:
            rebuilt_block.append("")
        for def_id in other_def_ids:
            rebuilt_block.append(f"[^{def_id}]: {new_defs[def_id]}")
            rebuilt_block.append("")

    # Preserve any non-definition lines that were in the old trailing block (rare, but be safe).
    if trailing_other and any(line.strip() for line in trailing_other):
        if not rebuilt_block:
            rebuilt_block.append("")
        rebuilt_block.extend(trailing_other)
        if rebuilt_block and rebuilt_block[-1].strip():
            rebuilt_block.append("")

    new_text = "\n".join(new_body_lines + rebuilt_block).rstrip() + "\n"
    changed = new_text != original
    if changed:
        path.write_text(new_text, encoding="utf-8")
    return changed, new_text


def main() -> int:
    ap = argparse.ArgumentParser(description="Sync glossary links and GitBook tooltip footnotes.")
    ap.add_argument("--write", action="store_true", help="Apply changes to files.")
    ap.add_argument("--files", nargs="*", default=None, help="Specific Markdown files to process.")
    args = ap.parse_args()

    glossary_text = GLOSSARY_PATH.read_text(encoding="utf-8")
    glossary_defs = parse_glossary_definitions(glossary_text)
    if not glossary_defs:
        raise SystemExit("No glossary definitions found in glossary.md")

    if args.files:
        paths = [Path(p) for p in args.files]
    else:
        paths = sorted(Path(".").glob(MD_GLOB))

    paths = [
        p
        for p in paths
        if p.name not in SKIP_FILES and not str(p).startswith("memory-bank/")
    ]

    changed_files: list[str] = []
    for path in paths:
        if not path.is_file():
            continue
        before = path.read_text(encoding="utf-8")
        changed, after = sync_file(path, glossary_defs)
        if changed:
            changed_files.append(str(path))
        if not args.write:
            # Revert any in-place changes when running in "check" mode.
            path.write_text(before, encoding="utf-8")

    if changed_files:
        print("\n".join(changed_files))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
