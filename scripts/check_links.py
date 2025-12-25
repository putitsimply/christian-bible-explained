#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path


MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
LIST_ITEM_RE = re.compile(r"^(?P<indent>\s*)[*-]\s+(?P<body>.+?)\s*$")
HEADING_RE = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<title>.+?)\s*$")


def collect_glossary_anchors() -> set[str]:
    anchors: set[str] = set()
    glossary = Path("glossary.md").read_text(encoding="utf-8")
    for match in re.finditer(r'<a id="([^"]+)"></a>', glossary):
        anchors.add(match.group(1))
    return anchors


def must_have_link_in_line(*, src_file: str, label_substring: str, target_path: str, errors: list[tuple[str, str, str]]):
    for line in Path(src_file).read_text(encoding="utf-8").splitlines():
        if target_path in line and "](" in line and label_substring in line:
            return
    errors.append((src_file, f"{label_substring} -> {target_path}", "expected navigation link not found"))


def check_list_block_links(
    *,
    file_path: Path,
    heading_title: str,
    require_link_for_item,
    errors: list[tuple[str, str, str]],
):
    """
    Find a `## <heading_title>` section and validate list items immediately under it.

    `require_link_for_item(line, indent, body) -> bool` decides whether that list line must contain a markdown link.
    """
    lines = file_path.read_text(encoding="utf-8").splitlines()
    in_section = False
    in_list = False
    for i, line in enumerate(lines, start=1):
        heading = HEADING_RE.match(line)
        if heading:
            title = heading.group("title")
            if in_section and title != heading_title:
                break
            in_section = title == heading_title
            in_list = False
            continue

        if not in_section:
            continue

        if not line.strip():
            if in_list:
                break
            continue

        list_item = LIST_ITEM_RE.match(line)
        if not list_item:
            if in_list:
                break
            continue

        in_list = True
        indent = len(list_item.group("indent").replace("\t", "    "))
        body = list_item.group("body")

        if require_link_for_item(line, indent, body) and not MD_LINK_RE.search(line):
            errors.append(
                (
                    file_path.name,
                    f"{heading_title} (line {i})",
                    f"list item expected to link but did not: {line.strip()}",
                )
            )


def check_summary_list_items_link(*, summary_path: Path, errors: list[tuple[str, str, str]]):
    for i, line in enumerate(summary_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.lstrip().startswith("* "):
            continue
        if not re.search(r"^\s*\*\s+\[[^\]]+\]\([^)]+\)\s*$", line):
            errors.append((summary_path.name, f"line {i}", f"SUMMARY list item is not a link: {line.strip()}"))


def main() -> int:
    md_files = sorted([p for p in Path(".").glob("*.md") if p.name not in {"AGENTS.md"}])
    glossary_anchors = collect_glossary_anchors()

    errors: list[tuple[str, str, str]] = []
    checked_links = 0

    for md in md_files:
        text = md.read_text(encoding="utf-8")
        for match in MD_LINK_RE.finditer(text):
            url = match.group(1).strip()
            if not url or url.startswith(("http://", "https://", "mailto:")):
                continue
            if url.startswith("#"):
                continue

            target = url.split()[0]
            if not target.endswith(".md") and ".md#" not in target:
                continue

            checked_links += 1

            if ".md#" in target:
                path, frag = target.split(".md#", 1)
                path = path + ".md"
                frag = frag.strip()
            else:
                path, frag = target, None

            file_path = Path(path)
            if not file_path.exists():
                errors.append((md.name, target, "missing file"))
                continue

            if frag and file_path.name == "glossary.md" and frag not in glossary_anchors:
                errors.append((md.name, target, f"missing glossary anchor #{frag}"))

    # Navigation spot-checks (labels may contain footnote refs like [^gl_...]).
    must_have_link_in_line(
        src_file="old-testament.md",
        label_substring="The Law (Torah",
        target_path="ot-law.md",
        errors=errors,
    )
    must_have_link_in_line(
        src_file="old-testament.md",
        label_substring="History (Old Testament",
        target_path="ot-history.md",
        errors=errors,
    )
    must_have_link_in_line(
        src_file="old-testament.md",
        label_substring="Poetry and wisdom",
        target_path="ot-wisdom.md",
        errors=errors,
    )
    must_have_link_in_line(
        src_file="old-testament.md",
        label_substring="Major prophets",
        target_path="ot-major-prophets.md",
        errors=errors,
    )
    must_have_link_in_line(
        src_file="old-testament.md",
        label_substring="Minor prophets",
        target_path="ot-minor-prophets.md",
        errors=errors,
    )

    must_have_link_in_line(
        src_file="new-testament.md",
        label_substring="Gospels",
        target_path="nt-gospels.md",
        errors=errors,
    )
    must_have_link_in_line(
        src_file="new-testament.md",
        label_substring="History (New Testament",
        target_path="nt-history.md",
        errors=errors,
    )
    must_have_link_in_line(
        src_file="new-testament.md",
        label_substring="Letters (Paul",
        target_path="nt-paul-letters.md",
        errors=errors,
    )
    must_have_link_in_line(
        src_file="new-testament.md",
        label_substring="Other letters",
        target_path="nt-other-letters.md",
        errors=errors,
    )
    must_have_link_in_line(
        src_file="new-testament.md",
        label_substring="Apocalyptic",
        target_path="nt-apocalyptic.md",
        errors=errors,
    )

    must_have_link_in_line(
        src_file="README.md",
        label_substring="Find a book",
        target_path="find-a-book.md",
        errors=errors,
    )

    # Navigation list checks: ensure navigation lists are links where expected.
    check_summary_list_items_link(summary_path=Path("SUMMARY.md"), errors=errors)

    check_list_block_links(
        file_path=Path("README.md"),
        heading_title="Quick links",
        require_link_for_item=lambda _line, _indent, _body: True,
        errors=errors,
    )

    check_list_block_links(
        file_path=Path("old-testament.md"),
        heading_title="Explore in this guide",
        require_link_for_item=lambda _line, _indent, _body: True,
        errors=errors,
    )
    check_list_block_links(
        file_path=Path("new-testament.md"),
        heading_title="Explore in this guide",
        require_link_for_item=lambda _line, _indent, _body: True,
        errors=errors,
    )

    check_list_block_links(
        file_path=Path("find-a-book.md"),
        heading_title="Browse by section",
        require_link_for_item=lambda _line, indent, body: not (
            indent == 0 and body.strip() in {"Old Testament", "New Testament"}
        ),
        errors=errors,
    )
    check_list_block_links(
        file_path=Path("find-a-book.md"),
        heading_title="A–Z list",
        require_link_for_item=lambda _line, _indent, _body: True,
        errors=errors,
    )

    for nav in sorted(Path(".").glob("ot-*.md")) + sorted(Path(".").glob("nt-*.md")):
        check_list_block_links(
            file_path=nav,
            heading_title="Books in this section",
            require_link_for_item=lambda _line, _indent, _body: True,
            errors=errors,
        )

    if errors:
        print(f"FAIL: {len(errors)} issues found (checked {checked_links} local markdown links)")
        for src, link, why in errors:
            print(f"- {src}: {link} -> {why}")
        return 1

    print(f"OK: checked {checked_links} local markdown links; no missing files/anchors; navigation spot-checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
