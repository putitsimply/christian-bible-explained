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

# `[Bible[^gl_bible]](glossary.md#bible)` -> `[Bible](glossary.md#bible)[^gl_bible]`
GLOSSARY_LINK_WITH_INNER_FOOTNOTE_RE = re.compile(
    r"\[(?P<label>[^\]]+?)\[\^(?P<fnid>[^\]]+?)\]\]\(glossary\.md#(?P<anchor>[^)]+)\)"
)

# Normal glossary links (used later for inserting footnote refs)
GLOSSARY_LINK_RE = re.compile(r"\[(?P<label>[^\]]+?)\]\(glossary\.md#(?P<anchor>[^)]+)\)")


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


def anchor_to_glossary_fn_id(anchor: str) -> str:
    return "gl_" + anchor.strip().replace("-", "_")


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


def sync_file(path: Path, glossary_defs: dict[str, str]) -> tuple[bool, str]:
    original = path.read_text(encoding="utf-8")

    # 1) Fix the common broken pattern where the footnote marker is inside the link label.
    def move_inner_fn(m: re.Match[str]) -> str:
        label = m.group("label")
        fnid = m.group("fnid")
        anchor = m.group("anchor")
        return f"[{label}](glossary.md#{anchor})[^{fnid}]"

    text = GLOSSARY_LINK_WITH_INNER_FOOTNOTE_RE.sub(move_inner_fn, original)

    lines = text.splitlines()
    body_lines, trailing_block = split_trailing_footnote_block(lines)
    existing_defs, trailing_other = extract_footnote_defs(trailing_block)

    body_text = "\n".join(body_lines)

    # 2) Ensure each glossary link has (at least one) tooltip footnote per term per page.
    anchors_in_order: list[str] = [m.group("anchor") for m in GLOSSARY_LINK_RE.finditer(body_text)]
    anchors_in_order = ordered_unique([a.strip() for a in anchors_in_order])

    for anchor in anchors_in_order:
        fn_id = anchor_to_glossary_fn_id(anchor)
        if fn_id in find_footnote_refs_outside_defs(body_lines):
            continue

        # Attach the marker to the first occurrence of a glossary link to this anchor.
        link_pat = re.compile(
            rf"(\[[^\]]+?\]\(glossary\.md#{re.escape(anchor)}\))(?!\[\^[^\]]+\])"
        )
        body_text, count = link_pat.subn(rf"\1[^{fn_id}]", body_text, count=1)
        if count == 0:
            # Should not happen, but avoid silently failing.
            continue

    # 3) Recompute used glossary footnotes after insertions and sync their definitions from glossary.md.
    new_body_lines = body_text.splitlines()
    refs = find_footnote_refs_outside_defs(new_body_lines)
    used_glossary_ids_in_order: list[str] = []
    for anchor in anchors_in_order:
        fn_id = anchor_to_glossary_fn_id(anchor)
        if fn_id in refs:
            used_glossary_ids_in_order.append(fn_id)

    used_glossary_ids_in_order = ordered_unique(used_glossary_ids_in_order)

    new_defs: dict[str, str] = dict(existing_defs)
    for fn_id in used_glossary_ids_in_order:
        anchor = fn_id.removeprefix("gl_").replace("_", "-")
        glossary_def = glossary_defs.get(anchor)
        if glossary_def:
            new_defs[fn_id] = glossary_def

    # Prune unused glossary defs
    for fn_id in list(new_defs.keys()):
        if fn_id.startswith("gl_") and fn_id not in refs:
            del new_defs[fn_id]

    # 4) Rebuild trailing footnote block (keep any non-glossary defs from the original file too).
    rebuilt_block: list[str] = []

    if used_glossary_ids_in_order:
        rebuilt_block.append("")
        for fn_id in used_glossary_ids_in_order:
            text_def = new_defs.get(fn_id)
            if not text_def:
                continue
            rebuilt_block.append(f"[^{fn_id}]: {text_def}")
            rebuilt_block.append("")

    # Add any non-glossary definitions that were present.
    other_def_ids = [k for k in new_defs.keys() if not k.startswith("gl_")]
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
