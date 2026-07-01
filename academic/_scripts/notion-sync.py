#!/usr/bin/env python3
"""
Bidirectional sync between Notion pages and local Markdown files.

Usage:
    python scripts/notion-sync.py pull  [--dry-run] [--discipline NAME] [--verbose]
    python scripts/notion-sync.py push  [--dry-run] [--discipline NAME] [--verbose]
    python scripts/notion-sync.py sync  [--dry-run] [--discipline NAME] [--verbose]
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
CONFIG_PATH = SCRIPT_DIR / "sync-config.json"
STATE_PATH = REPO_ROOT / ".notion-sync-state.json"

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_state():
    if STATE_PATH.exists():
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def get_notion_token(config):
    token = os.environ.get(config.get("notion_token_env", "NOTION_TOKEN"))
    if token:
        return token
    fallback = config.get("notion_token_fallback")
    if fallback:
        mcp_path = REPO_ROOT / fallback
        if mcp_path.exists():
            with open(mcp_path, "r", encoding="utf-8") as f:
                mcp = json.load(f)
            servers = mcp.get("mcpServers", {})
            for srv in servers.values():
                env = srv.get("env", {})
                if "NOTION_TOKEN" in env:
                    return env["NOTION_TOKEN"]
    print("ERROR: No Notion token found. Set NOTION_TOKEN env var.", file=sys.stderr)
    sys.exit(1)


def file_sha256(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def log(msg, verbose_only=False, verbose=False):
    if verbose_only and not verbose:
        return
    print(msg)


# ---------------------------------------------------------------------------
# Notion API Client
# ---------------------------------------------------------------------------

class NotionClient:
    def __init__(self, token: str):
        self.token = token
        self._last_request = 0.0

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        }

    def _rate_limit(self):
        elapsed = time.time() - self._last_request
        if elapsed < 0.35:
            time.sleep(0.35 - elapsed)
        self._last_request = time.time()

    def _request(self, method, url, data=None):
        self._rate_limit()
        body = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=body, headers=self._headers(), method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            print(f"Notion API error {e.code}: {error_body}", file=sys.stderr)
            if e.code == 429:
                retry_after = float(e.headers.get("Retry-After", "1"))
                print(f"  Rate limited. Waiting {retry_after}s...", file=sys.stderr)
                time.sleep(retry_after)
                return self._request(method, url, data)
            raise

    def get_page(self, page_id: str) -> dict:
        return self._request("GET", f"{NOTION_API}/pages/{page_id}")

    def get_blocks(self, block_id: str) -> list:
        blocks = []
        url = f"{NOTION_API}/blocks/{block_id}/children?page_size=100"
        while url:
            resp = self._request("GET", url)
            blocks.extend(resp.get("results", []))
            url = resp.get("next_cursor")
            if url:
                url = f"{NOTION_API}/blocks/{block_id}/children?page_size=100&start_cursor={url}"
        return blocks

    def delete_block(self, block_id: str):
        self._request("DELETE", f"{NOTION_API}/blocks/{block_id}")

    def append_blocks(self, parent_id: str, children: list):
        for i in range(0, len(children), 100):
            batch = children[i:i + 100]
            self._request("PATCH", f"{NOTION_API}/blocks/{parent_id}/children", {"children": batch})

    def create_page(self, parent_id: str, title: str, children: list = None) -> dict:
        data = {
            "parent": {"page_id": parent_id},
            "properties": {
                "title": [{"text": {"content": title}}]
            },
        }
        if children:
            data["children"] = children[:100]
        page = self._request("POST", f"{NOTION_API}/pages", data)
        if children and len(children) > 100:
            self.append_blocks(page["id"], children[100:])
        return page


# ---------------------------------------------------------------------------
# Notion Blocks -> Markdown
# ---------------------------------------------------------------------------

def rich_text_to_md(rich_texts: list) -> str:
    parts = []
    for rt in rich_texts:
        text = rt.get("plain_text", "")
        annotations = rt.get("annotations", {})
        href = rt.get("href")
        if annotations.get("code"):
            text = f"`{text}`"
        if annotations.get("bold"):
            text = f"**{text}**"
        if annotations.get("italic"):
            text = f"*{text}*"
        if annotations.get("strikethrough"):
            text = f"~~{text}~~"
        if href:
            text = f"[{text}]({href})"
        parts.append(text)
    return "".join(parts)


def download_image(url: str, images_dir: Path, page_id: str, index: int) -> str:
    images_dir.mkdir(parents=True, exist_ok=True)
    ext = ".png"
    if "." in url.split("?")[0].split("/")[-1]:
        ext = "." + url.split("?")[0].split("/")[-1].rsplit(".", 1)[-1]
        if len(ext) > 5:
            ext = ".png"
    filename = f"{page_id[:8]}_{index}{ext}"
    filepath = images_dir / filename
    try:
        urllib.request.urlretrieve(url, str(filepath))
    except Exception as e:
        return f"<!-- image download failed: {e} -->"
    return f"_images/{filename}"


def blocks_to_markdown(blocks: list, client: NotionClient, base_dir: Path,
                       page_id: str, depth: int = 0, image_counter: list = None,
                       options: dict = None) -> str:
    if image_counter is None:
        image_counter = [0]
    if options is None:
        options = {}

    lines = []
    numbered_index = 1

    for block in blocks:
        btype = block.get("type", "")
        bdata = block.get(btype, {})

        if btype == "paragraph":
            text = rich_text_to_md(bdata.get("rich_text", []))
            lines.append(text)
            lines.append("")

        elif btype in ("heading_1", "heading_2", "heading_3"):
            level = int(btype[-1])
            text = rich_text_to_md(bdata.get("rich_text", []))
            lines.append(f"{'#' * level} {text}")
            lines.append("")

        elif btype == "bulleted_list_item":
            text = rich_text_to_md(bdata.get("rich_text", []))
            indent = "  " * depth
            lines.append(f"{indent}- {text}")
            if block.get("has_children"):
                children = client.get_blocks(block["id"])
                child_md = blocks_to_markdown(
                    children, client, base_dir, page_id, depth + 1,
                    image_counter, options
                )
                lines.append(child_md.rstrip())
            numbered_index = 1

        elif btype == "numbered_list_item":
            text = rich_text_to_md(bdata.get("rich_text", []))
            indent = "  " * depth
            lines.append(f"{indent}{numbered_index}. {text}")
            numbered_index += 1
            if block.get("has_children"):
                children = client.get_blocks(block["id"])
                child_md = blocks_to_markdown(
                    children, client, base_dir, page_id, depth + 1,
                    image_counter, options
                )
                lines.append(child_md.rstrip())

        elif btype == "to_do":
            text = rich_text_to_md(bdata.get("rich_text", []))
            checked = "x" if bdata.get("checked") else " "
            lines.append(f"- [{checked}] {text}")

        elif btype == "code":
            text = rich_text_to_md(bdata.get("rich_text", []))
            lang = bdata.get("language", "")
            lines.append(f"```{lang}")
            lines.append(text)
            lines.append("```")
            lines.append("")

        elif btype == "quote":
            text = rich_text_to_md(bdata.get("rich_text", []))
            for line in text.split("\n"):
                lines.append(f"> {line}")
            lines.append("")

        elif btype == "callout":
            icon = ""
            icon_data = bdata.get("icon", {})
            if icon_data.get("type") == "emoji":
                icon = icon_data.get("emoji", "")
            text = rich_text_to_md(bdata.get("rich_text", []))
            prefix = f"**{icon}** " if icon else ""
            lines.append(f"> {prefix}{text}")
            lines.append("")

        elif btype == "divider":
            lines.append("---")
            lines.append("")

        elif btype == "image":
            image_counter[0] += 1
            caption = rich_text_to_md(bdata.get("caption", []))
            img_data = bdata.get(bdata.get("type", ""), {})
            url = img_data.get("url", "")
            if url and options.get("image_download", True):
                images_dir = base_dir / options.get("image_dir", "_images")
                local_path = download_image(url, images_dir, page_id, image_counter[0])
                lines.append(f"![{caption}]({local_path})")
            elif url:
                lines.append(f"![{caption}]({url})")
            else:
                lines.append(f"<!-- image: no url available -->")
            lines.append("")

        elif btype == "table":
            table_width = bdata.get("table_width", 0)
            has_header = bdata.get("has_column_header", False)
            rows = client.get_blocks(block["id"]) if block.get("has_children") else []
            for i, row in enumerate(rows):
                cells = row.get("table_row", {}).get("cells", [])
                row_text = "| " + " | ".join(
                    rich_text_to_md(cell) for cell in cells
                ) + " |"
                lines.append(row_text)
                if i == 0 and has_header:
                    lines.append("| " + " | ".join("---" for _ in cells) + " |")
            lines.append("")

        elif btype == "toggle":
            text = rich_text_to_md(bdata.get("rich_text", []))
            lines.append(f"<details><summary>{text}</summary>")
            lines.append("")
            if block.get("has_children"):
                children = client.get_blocks(block["id"])
                child_md = blocks_to_markdown(
                    children, client, base_dir, page_id, 0,
                    image_counter, options
                )
                lines.append(child_md.rstrip())
            lines.append("")
            lines.append("</details>")
            lines.append("")

        elif btype == "child_page":
            child_title = bdata.get("title", "Untitled")
            child_id = block["id"]
            safe_name = re.sub(r'[^\w\s-]', '', child_title).strip().lower()
            safe_name = re.sub(r'[\s]+', '-', safe_name)
            if not safe_name:
                safe_name = child_id[:8]

            child_dir = base_dir / safe_name
            child_dir.mkdir(parents=True, exist_ok=True)

            child_blocks = client.get_blocks(child_id)
            child_page = client.get_page(child_id)
            child_md = blocks_to_markdown(
                child_blocks, client, child_dir, child_id, 0,
                image_counter, options
            )
            notion_url = child_page.get("url", "")
            last_edited = child_page.get("last_edited_time", "")

            frontmatter = (
                f"---\n"
                f"notion_page_id: \"{child_id}\"\n"
                f"title: \"{child_title}\"\n"
                f"last_synced: \"{datetime.now(timezone.utc).isoformat()}\"\n"
                f"notion_url: \"{notion_url}\"\n"
                f"---\n\n"
            )
            (child_dir / "index.md").write_text(
                frontmatter + f"# {child_title}\n\n" + child_md,
                encoding="utf-8"
            )
            lines.append(f"- [{child_title}]({safe_name}/index.md)")

        elif btype == "bookmark":
            url = bdata.get("url", "")
            caption = rich_text_to_md(bdata.get("caption", []))
            label = caption if caption else url
            lines.append(f"[{label}]({url})")
            lines.append("")

        elif btype == "embed":
            url = bdata.get("url", "")
            lines.append(f"<!-- embed: {url} -->")
            lines.append("")

        elif btype == "equation":
            expr = bdata.get("expression", "")
            lines.append(f"$$\n{expr}\n$$")
            lines.append("")

        elif btype == "column_list":
            if block.get("has_children"):
                cols = client.get_blocks(block["id"])
                for col in cols:
                    if col.get("has_children"):
                        col_blocks = client.get_blocks(col["id"])
                        col_md = blocks_to_markdown(
                            col_blocks, client, base_dir, page_id, depth,
                            image_counter, options
                        )
                        lines.append(col_md.rstrip())
                        lines.append("")

        elif btype in ("synced_block", "link_to_page", "child_database",
                        "table_of_contents", "breadcrumb", "template",
                        "link_preview", "file", "pdf", "video", "audio"):
            lines.append(f"<!-- notion:unsupported type={btype} -->")
            lines.append("")

        else:
            if btype not in ("column",):
                lines.append(f"<!-- notion:unsupported type={btype} -->")
                lines.append("")

        # Reset numbered index for non-numbered blocks
        if btype != "numbered_list_item":
            numbered_index = 1

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Markdown -> Notion Blocks (push)
# ---------------------------------------------------------------------------

def md_rich_text(text: str) -> list:
    """Parse inline markdown to Notion rich_text array."""
    segments = []
    pattern = re.compile(
        r'(?P<bold_italic>\*\*\*(.+?)\*\*\*)'
        r'|(?P<bold>\*\*(.+?)\*\*)'
        r'|(?P<italic>\*(.+?)\*)'
        r'|(?P<strike>~~(.+?)~~)'
        r'|(?P<code>`(.+?)`)'
        r'|(?P<link>\[([^\]]+)\]\(([^)]+)\))'
    )

    pos = 0
    for m in pattern.finditer(text):
        if m.start() > pos:
            segments.append(_text_obj(text[pos:m.start()]))

        if m.group("bold_italic"):
            inner = m.group(2)
            segments.append(_text_obj(inner, bold=True, italic=True))
        elif m.group("bold"):
            inner = m.group(4)
            segments.append(_text_obj(inner, bold=True))
        elif m.group("italic"):
            inner = m.group(6)
            segments.append(_text_obj(inner, italic=True))
        elif m.group("strike"):
            inner = m.group(8)
            segments.append(_text_obj(inner, strikethrough=True))
        elif m.group("code"):
            inner = m.group(10)
            segments.append(_text_obj(inner, code=True))
        elif m.group("link"):
            label = m.group(12)
            url = m.group(13)
            segments.append(_text_obj(label, link=url))

        pos = m.end()

    if pos < len(text):
        segments.append(_text_obj(text[pos:]))

    return segments if segments else [_text_obj("")]


def _text_obj(content, bold=False, italic=False, strikethrough=False,
              code=False, link=None):
    obj = {
        "type": "text",
        "text": {"content": content},
        "annotations": {
            "bold": bold,
            "italic": italic,
            "strikethrough": strikethrough,
            "underline": False,
            "code": code,
            "color": "default",
        },
    }
    if link:
        obj["text"]["link"] = {"url": link}
    return obj


def markdown_to_blocks(md_text: str) -> list:
    """Convert markdown string to list of Notion block objects."""
    lines = md_text.split("\n")
    blocks = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Skip frontmatter
        if i == 0 and line.strip() == "---":
            i += 1
            while i < len(lines) and lines[i].strip() != "---":
                i += 1
            i += 1
            continue

        # Empty line
        if not line.strip():
            i += 1
            continue

        # Headings
        heading_match = re.match(r'^(#{1,3})\s+(.+)$', line)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2)
            btype = f"heading_{level}"
            blocks.append({
                "object": "block",
                "type": btype,
                btype: {"rich_text": md_rich_text(text)},
            })
            i += 1
            continue

        # Fenced code block
        code_match = re.match(r'^```(\w*)$', line)
        if code_match:
            lang = code_match.group(1) or "plain text"
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```
            code_content = "\n".join(code_lines)
            # Notion limits rich_text content to 2000 chars
            if len(code_content) > 2000:
                code_content = code_content[:2000]
            blocks.append({
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [_text_obj(code_content)],
                    "language": lang,
                },
            })
            continue

        # Divider
        if re.match(r'^---+$', line):
            blocks.append({"object": "block", "type": "divider", "divider": {}})
            i += 1
            continue

        # Blockquote
        if line.startswith("> "):
            quote_lines = []
            while i < len(lines) and lines[i].startswith("> "):
                quote_lines.append(lines[i][2:])
                i += 1
            text = "\n".join(quote_lines)
            blocks.append({
                "object": "block",
                "type": "quote",
                "quote": {"rich_text": md_rich_text(text)},
            })
            continue

        # To-do
        todo_match = re.match(r'^- \[([ x])\] (.+)$', line)
        if todo_match:
            checked = todo_match.group(1) == "x"
            text = todo_match.group(2)
            blocks.append({
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": md_rich_text(text),
                    "checked": checked,
                },
            })
            i += 1
            continue

        # Bulleted list
        bullet_match = re.match(r'^(\s*)- (.+)$', line)
        if bullet_match:
            text = bullet_match.group(2)
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": md_rich_text(text)},
            })
            i += 1
            continue

        # Numbered list
        num_match = re.match(r'^(\s*)\d+\.\s+(.+)$', line)
        if num_match:
            text = num_match.group(2)
            blocks.append({
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": md_rich_text(text)},
            })
            i += 1
            continue

        # Image
        img_match = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)$', line)
        if img_match:
            caption = img_match.group(1)
            url = img_match.group(2)
            if url.startswith("http"):
                blocks.append({
                    "object": "block",
                    "type": "image",
                    "image": {
                        "type": "external",
                        "external": {"url": url},
                        "caption": md_rich_text(caption) if caption else [],
                    },
                })
            else:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": md_rich_text(f"[image: {caption}]")},
                })
            i += 1
            continue

        # Table
        if "|" in line and i + 1 < len(lines) and re.match(r'^\|[\s\-|]+\|$', lines[i + 1]):
            table_rows = []
            header_cells = [c.strip() for c in line.strip().strip("|").split("|")]
            table_rows.append(header_cells)
            i += 2  # skip header + separator
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                table_rows.append(cells)
                i += 1
            width = max(len(r) for r in table_rows)
            children = []
            for row in table_rows:
                while len(row) < width:
                    row.append("")
                children.append({
                    "type": "table_row",
                    "table_row": {
                        "cells": [md_rich_text(cell) for cell in row],
                    },
                })
            blocks.append({
                "object": "block",
                "type": "table",
                "table": {
                    "table_width": width,
                    "has_column_header": True,
                    "has_row_header": False,
                    "children": children,
                },
            })
            continue

        # Details/toggle
        details_match = re.match(r'^<details><summary>(.+?)</summary>$', line)
        if details_match:
            summary_text = details_match.group(1)
            i += 1
            toggle_lines = []
            while i < len(lines) and lines[i].strip() != "</details>":
                toggle_lines.append(lines[i])
                i += 1
            i += 1  # skip </details>
            inner_md = "\n".join(toggle_lines)
            inner_blocks = markdown_to_blocks(inner_md)
            blocks.append({
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": md_rich_text(summary_text),
                    "children": inner_blocks[:100] if inner_blocks else [],
                },
            })
            continue

        # HTML comment (unsupported marker) — skip
        if line.strip().startswith("<!--"):
            i += 1
            continue

        # Equation block
        if line.strip() == "$$":
            eq_lines = []
            i += 1
            while i < len(lines) and lines[i].strip() != "$$":
                eq_lines.append(lines[i])
                i += 1
            i += 1
            blocks.append({
                "object": "block",
                "type": "equation",
                "equation": {"expression": "\n".join(eq_lines)},
            })
            continue

        # Default: paragraph
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": md_rich_text(line)},
        })
        i += 1

    return blocks


# ---------------------------------------------------------------------------
# Frontmatter helpers
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> tuple:
    """Return (metadata_dict, body_text)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_block = text[4:end]
    body = text[end + 4:].lstrip("\n")
    meta = {}
    for line in fm_block.split("\n"):
        if ":" in line:
            key, _, val = line.partition(":")
            val = val.strip().strip('"').strip("'")
            meta[key.strip()] = val
    return meta, body


def make_frontmatter(page_id: str, title: str, notion_url: str) -> str:
    now = datetime.now(timezone.utc).isoformat()
    return (
        f"---\n"
        f"notion_page_id: \"{page_id}\"\n"
        f"title: \"{title}\"\n"
        f"last_synced: \"{now}\"\n"
        f"notion_url: \"{notion_url}\"\n"
        f"---\n\n"
    )


# ---------------------------------------------------------------------------
# Pull: Notion -> Markdown
# ---------------------------------------------------------------------------

def pull_page(client: NotionClient, page_id: str, target_dir: Path,
              options: dict, dry_run: bool = False, verbose: bool = False):
    page = client.get_page(page_id)
    title_parts = page.get("properties", {}).get("title", {}).get("title", [])
    title = "".join(t.get("plain_text", "") for t in title_parts)
    notion_url = page.get("url", "")
    last_edited = page.get("last_edited_time", "")

    log(f"  Pulling: {title} ({page_id[:8]}...)", verbose_only=False, verbose=verbose)
    log(f"    Last edited: {last_edited}", verbose_only=True, verbose=verbose)

    blocks = client.get_blocks(page_id)

    if dry_run:
        log(f"    [DRY RUN] Would write to {target_dir}/index.md ({len(blocks)} blocks)")
        return last_edited

    target_dir.mkdir(parents=True, exist_ok=True)
    md_content = blocks_to_markdown(blocks, client, target_dir, page_id, options=options)
    frontmatter = make_frontmatter(page_id, title, notion_url)
    full_content = frontmatter + f"# {title}\n\n" + md_content

    index_path = target_dir / "index.md"
    index_path.write_text(full_content, encoding="utf-8")
    log(f"    Written: {index_path.relative_to(REPO_ROOT)}", verbose_only=True, verbose=verbose)

    return last_edited


# ---------------------------------------------------------------------------
# Push: Markdown -> Notion
# ---------------------------------------------------------------------------

def push_page(client: NotionClient, md_path: Path, parent_page_id: str,
              dry_run: bool = False, verbose: bool = False):
    if not md_path.exists():
        log(f"  Skip (no file): {md_path}")
        return

    text = md_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    page_id = meta.get("notion_page_id", "")
    title = meta.get("title", md_path.parent.name)

    log(f"  Pushing: {md_path.relative_to(REPO_ROOT)}", verbose_only=False, verbose=verbose)

    blocks = markdown_to_blocks(body)

    if dry_run:
        log(f"    [DRY RUN] Would push {len(blocks)} blocks to Notion page {page_id[:8]}...")
        return

    if page_id:
        # Delete existing blocks (except child_page blocks)
        existing_blocks = client.get_blocks(page_id)
        for block in existing_blocks:
            if block.get("type") == "child_page":
                continue
            try:
                client.delete_block(block["id"])
            except Exception as e:
                log(f"    Warning: could not delete block {block['id'][:8]}: {e}",
                    verbose_only=True, verbose=verbose)
        # Append new blocks
        if blocks:
            client.append_blocks(page_id, blocks)
        log(f"    Updated Notion page {page_id[:8]}...", verbose_only=True, verbose=verbose)
    else:
        # Create new page
        page = client.create_page(parent_page_id, title, blocks)
        new_id = page["id"]
        notion_url = page.get("url", "")
        log(f"    Created new Notion page: {new_id[:8]}...")
        # Update frontmatter with new page ID
        new_fm = make_frontmatter(new_id, title, notion_url)
        md_path.write_text(new_fm + body, encoding="utf-8")

    # Recursively push child pages (subfolders with index.md)
    parent_dir = md_path.parent
    target_page_id = page_id if page_id else ""
    if target_page_id:
        for child_dir in sorted(parent_dir.iterdir()):
            if child_dir.is_dir() and child_dir.name != "_images":
                child_index = child_dir / "index.md"
                if child_index.exists():
                    push_page(client, child_index, target_page_id,
                              dry_run=dry_run, verbose=verbose)


# ---------------------------------------------------------------------------
# Sync engine
# ---------------------------------------------------------------------------

def sync_discipline(client: NotionClient, mapping: dict, config: dict,
                    mode: str, state: dict, dry_run: bool = False,
                    verbose: bool = False):
    page_id = mapping["notion_page_id"]
    repo_path = REPO_ROOT / mapping["repo_path"]
    name = mapping["name"]
    options = config.get("options", {})
    index_path = repo_path / "index.md"

    log(f"\n{'='*60}")
    log(f"Discipline: {name}")
    log(f"  Notion: {page_id}")
    log(f"  Repo:   {repo_path.relative_to(REPO_ROOT)}/")

    page_state = state.get(page_id, {})

    if mode == "pull":
        last_edited = pull_page(client, page_id, repo_path, options,
                                dry_run=dry_run, verbose=verbose)
        if not dry_run:
            page_state["notion_last_edited"] = last_edited
            page_state["local_sha256"] = file_sha256(index_path)
            state[page_id] = page_state
        return

    if mode == "push":
        push_page(client, index_path, page_id, dry_run=dry_run, verbose=verbose)
        if not dry_run:
            page_state["local_sha256"] = file_sha256(index_path)
            page = client.get_page(page_id)
            page_state["notion_last_edited"] = page.get("last_edited_time", "")
            state[page_id] = page_state
        return

    # mode == "sync" — bidirectional
    # 1. Check Notion changes
    page = client.get_page(page_id)
    notion_edited = page.get("last_edited_time", "")
    prev_notion_edited = page_state.get("notion_last_edited", "")
    notion_changed = notion_edited != prev_notion_edited

    # 2. Check local changes
    current_sha = file_sha256(index_path)
    prev_sha = page_state.get("local_sha256", "")
    local_changed = current_sha != prev_sha and current_sha != ""

    # First sync (no previous state)
    if not prev_notion_edited and not prev_sha:
        log(f"  First sync — pulling from Notion")
        last_edited = pull_page(client, page_id, repo_path, options,
                                dry_run=dry_run, verbose=verbose)
        if not dry_run:
            page_state["notion_last_edited"] = last_edited
            page_state["local_sha256"] = file_sha256(index_path)
            state[page_id] = page_state
        return

    log(f"  Notion changed: {notion_changed} | Local changed: {local_changed}",
        verbose_only=True, verbose=verbose)

    if not notion_changed and not local_changed:
        log(f"  SKIP — no changes")
        return

    if notion_changed and not local_changed:
        log(f"  PULL — Notion has updates")
        last_edited = pull_page(client, page_id, repo_path, options,
                                dry_run=dry_run, verbose=verbose)
        if not dry_run:
            page_state["notion_last_edited"] = last_edited
            page_state["local_sha256"] = file_sha256(index_path)
            state[page_id] = page_state
        return

    if local_changed and not notion_changed:
        log(f"  PUSH — local has updates")
        push_page(client, index_path, page_id, dry_run=dry_run, verbose=verbose)
        if not dry_run:
            page_state["local_sha256"] = file_sha256(index_path)
            page = client.get_page(page_id)
            page_state["notion_last_edited"] = page.get("last_edited_time", "")
            state[page_id] = page_state
        return

    # Both changed — conflict resolution by timestamp
    log(f"  CONFLICT — both sides changed")
    # Compare Notion edit time with file mtime
    notion_dt = datetime.fromisoformat(notion_edited.replace("Z", "+00:00"))
    local_mtime = datetime.fromtimestamp(index_path.stat().st_mtime, tz=timezone.utc)

    if notion_dt >= local_mtime:
        log(f"  Resolving: Notion is newer ({notion_edited} >= {local_mtime.isoformat()})")
        last_edited = pull_page(client, page_id, repo_path, options,
                                dry_run=dry_run, verbose=verbose)
        if not dry_run:
            page_state["notion_last_edited"] = last_edited
            page_state["local_sha256"] = file_sha256(index_path)
            state[page_id] = page_state
    else:
        log(f"  Resolving: Local is newer ({local_mtime.isoformat()} > {notion_edited})")
        push_page(client, index_path, page_id, dry_run=dry_run, verbose=verbose)
        if not dry_run:
            page_state["local_sha256"] = file_sha256(index_path)
            page = client.get_page(page_id)
            page_state["notion_last_edited"] = page.get("last_edited_time", "")
            state[page_id] = page_state


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Bidirectional Notion <-> Markdown sync"
    )
    parser.add_argument("mode", choices=["pull", "push", "sync"],
                        help="Sync direction: pull (Notion->MD), push (MD->Notion), sync (bidirectional)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would happen without making changes")
    parser.add_argument("--discipline", type=str, default=None,
                        help="Only sync a specific discipline (by name or repo path)")
    parser.add_argument("--verbose", action="store_true",
                        help="Show detailed output")

    args = parser.parse_args()
    config = load_config()
    token = get_notion_token(config)
    client = NotionClient(token)
    state = load_state()

    mappings = config["mappings"]
    if args.discipline:
        needle = args.discipline.lower()
        mappings = [
            m for m in mappings
            if needle in m["name"].lower() or needle in m["repo_path"].lower()
        ]
        if not mappings:
            print(f"ERROR: No discipline matching '{args.discipline}'", file=sys.stderr)
            sys.exit(1)

    log(f"Notion Sync — mode: {args.mode}" + (" [DRY RUN]" if args.dry_run else ""))
    log(f"Disciplines: {len(mappings)}")

    for mapping in mappings:
        try:
            sync_discipline(client, mapping, config, args.mode, state,
                            dry_run=args.dry_run, verbose=args.verbose)
        except Exception as e:
            print(f"\nERROR syncing {mapping['name']}: {e}", file=sys.stderr)
            if args.verbose:
                import traceback
                traceback.print_exc()

    if not args.dry_run:
        save_state(state)
        log(f"\nState saved to {STATE_PATH.relative_to(REPO_ROOT)}")

    log("\nDone.")


if __name__ == "__main__":
    main()
