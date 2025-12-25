#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


GLOSSARY_PATH = Path("glossary.md")
MD_GLOB = "*.md"
SKIP_FILES = {GLOSSARY_PATH.name, "AGENTS.md"}
SKIP_FILES.add("SUMMARY.md")


ANCHOR_HEADING_RE = re.compile(r'^##\s+<a id="(?P<id>[^"]+)"></a>(?P<title>.*)$')
FOOTNOTE_DEF_RE = re.compile(r"^\[\^(?P<id>[^\]]+)\]:\s*(?P<text>.*)\s*$")

# Normal glossary links (used for conversion) - supports optional Markdown link title.
GLOSSARY_MD_LINK_RE = re.compile(
    r'\[(?P<label>[^\]]+?)\]\(glossary\.md#(?P<anchor>[^\)\s]+)(?:\s+"[^"]*")?\)'
)

# Links created by the (now reverted) per-term-pages approach.
TERM_PAGE_LINK_RE = re.compile(r"\[(?P<label>[^\]]+?)\]\(glossary/(?P<anchor>[^)]+?)\.md\)")

GLOSSARY_HTML_LINK_RE = re.compile(
    r'<a\s+href="glossary\.md#(?P<anchor>[^"]+)"[^>]*>(?P<label>.*?)</a>',
    re.DOTALL,
)

GLOSSARY_FOOTNOTE_REF_RE = re.compile(r"[ \t]*\[\^gl_[^\]]+\]")
GLOSSARY_FOOTNOTE_DEF_RE = re.compile(r"^\[\^gl_[^\]]+\]:.*\n?", re.M)


def parse_glossary_entries(glossary_text: str) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    lines = glossary_text.splitlines()
    i = 0
    while i < len(lines):
        m = ANCHOR_HEADING_RE.match(lines[i])
        if not m:
            i += 1
            continue
        anchor_id = m.group("id").strip()
        title = m.group("title").strip()
        i += 1

        while i < len(lines) and not lines[i].strip():
            i += 1
        if i >= len(lines):
            break

        # Definitions in this repo are single-paragraph, single-line.
        definition_line = lines[i].strip()
        entries[anchor_id] = {"title": title, "definition": definition_line}
        i += 1
    return entries


def build_term_variants(glossary_entries: dict[str, dict[str, str]]) -> dict[str, list[str]]:
    """
    Build a list of term variants to match for each glossary anchor.

    Variants are derived from the glossary heading title (e.g. "Israel / Israelites" -> ["Israel", "Israelites"]).
    """
    variants: dict[str, list[str]] = {}
    for anchor, entry in glossary_entries.items():
        raw_title = entry["title"].strip()
        if not raw_title:
            continue
        parts = [p.strip() for p in re.split(r"\s*/\s*", raw_title) if p.strip()]
        out: list[str] = []
        for part in parts:
            out.append(part)
            lower = part.lower()
            if lower != part and part not in {"God", "Bible", "Israel", "LORD"}:
                out.append(lower)
            # Add a simple plural form for single-word terms (e.g. Priest -> Priests).
            if part.isalpha() and not part.endswith("s"):
                out.append(part + "s")
                if lower != part and part not in {"God", "Bible", "Israel", "LORD"}:
                    out.append(lower + "s")
        variants[anchor] = ordered_unique(out)
    return variants


def phrase_regex(phrase: str) -> re.Pattern[str]:
    escaped = re.escape(phrase)
    if re.match(r"^[A-Za-z0-9][A-Za-z0-9\s-]*[A-Za-z0-9]$", phrase):
        return re.compile(rf"\b{escaped}\b")
    return re.compile(escaped)


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


def anchor_to_glossary_fn_id(anchor: str) -> str:
    return "gl_" + anchor.strip().replace("-", "_")


def strip_glossary_link_titles(text: str) -> str:
    # Remove optional Markdown link titles from glossary links.
    return re.sub(r'\(glossary\.md#([^\)\s]+)\s+"[^"]*"\)', r"(glossary.md#\1)", text)


def sync_file(
    path: Path,
    glossary_entries: dict[str, dict[str, str]],
    term_variants: dict[str, list[str]],
) -> tuple[bool, str]:
    original = path.read_text(encoding="utf-8")

    text = original

    # Remove any stray footnote reference lines (never valid on their own).
    text = re.sub(r"^\[\^gl_[^\]]+\]\s*\n?", "", text, flags=re.M)
    text = re.sub(r"^\[\^\d+\]\s*\n?", "", text, flags=re.M)

    # Convert any leftover HTML links to Markdown links.
    text = GLOSSARY_HTML_LINK_RE.sub(lambda m: f"[{m.group('label')}](glossary.md#{m.group('anchor')})", text)

    # Remove any Markdown link titles on glossary links (we don't rely on them).
    text = strip_glossary_link_titles(text)

    lines = text.splitlines()
    # Clean up stray `: <definition>` lines that can be left behind by earlier tooltip conversions.
    def is_stray_definition_line(line: str) -> bool:
        stripped = line.strip()
        if not stripped.startswith(":"):
            return False
        stripped = stripped[1:].strip()
        for definition in (v["definition"] for v in glossary_entries.values()):
            if stripped == definition:
                return True
            if stripped == f"{definition}.":
                return True
            if stripped == f"{definition} (Glossary)":
                return True
            if stripped == f"{definition}. (Glossary)":
                return True
            if stripped.startswith(definition) and "Glossary" in stripped:
                return True
        return False

    lines = [line for line in lines if not is_stray_definition_line(line)]
    body_lines, trailing_block = split_trailing_footnote_block(lines)
    existing_defs, trailing_other = extract_footnote_defs(trailing_block)

    body_text = "\n".join(body_lines)

    # Detect any existing glossary footnote markers in the body (so re-running is idempotent).
    existing_glossary_ids_in_order = ordered_unique(re.findall(r"\[\^(gl_[^\]]+)\]", body_text))
    seen_anchors: set[str] = set(
        fid.removeprefix("gl_").replace("_", "-") for fid in existing_glossary_ids_in_order
    )
    used_glossary_ids: list[str] = list(existing_glossary_ids_in_order)

    # 2) Convert glossary links into footnote-only tooltips.
    # No link on the term in content; the footnote text includes a link back to the glossary.
    def to_footnote(label: str, anchor: str) -> str:
        anchor = anchor.strip()
        if anchor not in glossary_entries:
            return label
        if anchor in seen_anchors:
            return label
        seen_anchors.add(anchor)
        footnote_id = anchor_to_glossary_fn_id(anchor)
        used_glossary_ids.append(footnote_id)
        return f"{label}[^{footnote_id}]"

    # Undo per-term-pages links (if any) back into footnote-only.
    body_text = TERM_PAGE_LINK_RE.sub(lambda m: to_footnote(m.group("label"), m.group("anchor")), body_text)
    body_text = GLOSSARY_MD_LINK_RE.sub(lambda m: to_footnote(m.group("label"), m.group("anchor")), body_text)
    used_glossary_ids = ordered_unique(used_glossary_ids)

    # Also add tooltip footnotes for glossary terms that occur without links.
    for anchor, variants in term_variants.items():
        if anchor in seen_anchors:
            continue
        footnote_id = anchor_to_glossary_fn_id(anchor)
        inserted = False
        for variant in variants:
            pat = phrase_regex(variant)
            m = pat.search(body_text)
            if not m:
                continue
            body_text = body_text[: m.end()] + f"[^{footnote_id}]" + body_text[m.end() :]
            seen_anchors.add(anchor)
            used_glossary_ids.append(footnote_id)
            inserted = True
            break
        if inserted:
            continue

    # Recompute glossary footnote IDs in final appearance order (not insertion order),
    # so re-running this script is idempotent and footnote defs follow reading order.
    used_glossary_ids = ordered_unique(re.findall(r"\[\^(gl_[^\]]+)\]", body_text))

    # 4) Rebuild trailing footnote block (keep any non-glossary defs from the original file too).
    new_body_lines = body_text.splitlines()
    refs = find_footnote_refs_outside_defs(new_body_lines)

    # Keep existing non-glossary defs that are still referenced.
    new_defs: dict[str, str] = {k: v for (k, v) in existing_defs.items() if not k.startswith("gl_") and k in refs}

    # Sync glossary tooltip defs from glossary.md.
    for footnote_id in used_glossary_ids:
        if footnote_id not in refs:
            continue
        anchor = footnote_id.removeprefix("gl_").replace("_", "-")
        definition = glossary_entries.get(anchor, {}).get("definition")
        if definition:
            new_defs[footnote_id] = f"{definition} ([Glossary](glossary.md#{anchor}))"

    rebuilt_block: list[str] = []

    # Glossary defs first, in appearance order.
    glossary_def_ids = [fid for fid in used_glossary_ids if fid in refs and fid in new_defs]
    if glossary_def_ids:
        if not rebuilt_block:
            rebuilt_block.append("")
        for def_id in glossary_def_ids:
            rebuilt_block.append(f"[^{def_id}]: {new_defs[def_id]}")
            rebuilt_block.append("")

    other_def_ids = [k for k in new_defs.keys() if not k.startswith("gl_") and k in refs]
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
    ap = argparse.ArgumentParser(description="Sync glossary tooltips as footnotes (term not linked).")
    ap.add_argument("--write", action="store_true", help="Apply changes to files.")
    ap.add_argument("--files", nargs="*", default=None, help="Specific Markdown files to process.")
    args = ap.parse_args()

    glossary_text = GLOSSARY_PATH.read_text(encoding="utf-8")
    glossary_entries = parse_glossary_entries(glossary_text)
    if not glossary_entries:
        raise SystemExit("No glossary definitions found in glossary.md")
    term_variants = build_term_variants(glossary_entries)

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
        changed, after = sync_file(path, glossary_entries, term_variants)
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
