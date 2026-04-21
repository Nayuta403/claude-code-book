#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — render 23 chapter markdown files into D-style HTML pages.

Input:  /Users/nayuta/ai/claude-code-rev/book/chapters/ch??-*.md
Output: /Users/nayuta/ai/claude-code-book/ch??/index.html

Zero dependencies (stdlib only). Custom markdown parser tailored to this
book's usage: h1..h4, paragraphs, inline code, fenced code blocks with
language and optional "// path:line" first-line caption, blockquotes,
GFM-style tables, ordered/unordered lists, bold/italic/links, and
auto-linking for file:line citations and bare chNN cross-refs.

Plus a minimal TypeScript/JavaScript syntax highlighter.

Usage:  python3 tools/build.py
"""

from __future__ import annotations

import html
import os
import re
import sys
from pathlib import Path

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

SRC_DIR  = Path("/Users/nayuta/ai/claude-code-rev/book/chapters")
OUT_ROOT = Path("/Users/nayuta/ai/claude-code-book")

CHAPTERS: list[dict] = [
    {"id": 1,  "slug": "ch01-feature-inventory",           "en": "Feature Inventory",    "cn": "功能全景清单",                     "part": 1, "topic": "入口 · 命令 · 工具"},
    {"id": 2,  "slug": "ch02-use-case-showcase",           "en": "Showcase",             "cn": "典型使用场景",                     "part": 1, "topic": "five real tasks"},
    {"id": 3,  "slug": "ch03-agent-loop",                  "en": "Agent Loop",           "cn": "推理·工具循环主引擎",              "part": 2, "topic": "QueryEngine · query"},
    {"id": 4,  "slug": "ch04-multi-agent",                 "en": "Multi-Agent",          "cn": "Sub-Agent 协程调度",              "part": 2, "topic": "coroutine"},
    {"id": 5,  "slug": "ch05-plan-mode",                   "en": "Plan Mode",            "cn": "让 Agent 先想后做",                "part": 2, "topic": "read-only"},
    {"id": 6,  "slug": "ch06-worktree",                    "en": "Worktree",             "cn": "隔离模式",                          "part": 2, "topic": "git isolation"},
    {"id": 7,  "slug": "ch07-context-memory",              "en": "Context",              "cn": "上下文管理与记忆",                  "part": 2, "topic": "compaction"},
    {"id": 8,  "slug": "ch08-tool-system",                 "en": "Tools",                "cn": "Tool 接口与 ToolSearch",           "part": 2, "topic": "deferred tools"},
    {"id": 9,  "slug": "ch09-permission-model",            "en": "Permissions",          "cn": "每次都问却不烦",                    "part": 2, "topic": "ladder"},
    {"id": 10, "slug": "ch10-skills",                      "en": "Skills",               "cn": "技能系统",                          "part": 3, "topic": "prompt pack"},
    {"id": 11, "slug": "ch11-plugins",                     "en": "Plugins",              "cn": "插件系统",                          "part": 3, "topic": "out-of-tree"},
    {"id": 12, "slug": "ch12-mcp",                         "en": "MCP",                  "cn": "集成与 upstream 代理",              "part": 3, "topic": "bridge"},
    {"id": 13, "slug": "ch13-cron-scheduling",             "en": "Cron",                 "cn": "定时任务",                          "part": 3, "topic": "schedule"},
    {"id": 14, "slug": "ch14-hooks",                       "en": "Hooks",                "cn": "可编程生命周期",                    "part": 3, "topic": "lifecycle"},
    {"id": 15, "slug": "ch15-proactive",                   "en": "Proactive",            "cn": "主动提示而不打扰",                  "part": 4, "topic": "nudges"},
    {"id": 16, "slug": "ch16-background-tasks",            "en": "Background",           "cn": "后台任务",                          "part": 4, "topic": "async"},
    {"id": 17, "slug": "ch17-remote-sessions",             "en": "Remote",               "cn": "Sessions 与 Teleport",              "part": 4, "topic": "broker"},
    {"id": 18, "slug": "ch18-ide-chrome-computer-use",     "en": "Multi-host",           "cn": "IDE / Chrome / Computer Use",       "part": 4, "topic": "integration"},
    {"id": 19, "slug": "ch19-buddy",                       "en": "Buddy",                "cn": "宠物系统",                          "part": 4, "topic": "companion"},
    {"id": 20, "slug": "ch20-voice-vim-keybindings",       "en": "Input",                "cn": "语音 / Vim / 键位",                 "part": 4, "topic": "input stack"},
    {"id": 21, "slug": "ch21-ink-ui",                      "en": "Ink UI",               "cn": "终端 UI 背后的工程",                "part": 5, "topic": "react in terminal"},
    {"id": 22, "slug": "ch22-cost-observability",          "en": "Observability",        "cn": "成本 / 可观测 / 调试",              "part": 5, "topic": "cost · trace"},
    {"id": 23, "slug": "ch23-agent-sdk",                   "en": "Agent SDK",            "cn": "把 Claude Code 当库用",             "part": 5, "topic": "embed"},
]

PARTS = {
    1: {"id": "I",   "en": "Overview",     "cn": "总览"},
    2: {"id": "II",  "en": "Core Engine",  "cn": "核心引擎"},
    3: {"id": "III", "en": "Extensions",   "cn": "扩展机制"},
    4: {"id": "IV",  "en": "Interactions", "cn": "交互与集成"},
    5: {"id": "V",   "en": "Engineering",  "cn": "工程与 SDK"},
}

# ------------------------------------------------------------------
# Syntax highlighter (TypeScript / JavaScript / JSON / misc.)
# ------------------------------------------------------------------

TS_KEYWORDS = {
    "abstract","as","async","await","break","case","catch","class","const",
    "continue","debugger","declare","default","delete","do","else","enum",
    "export","extends","false","finally","for","from","function","get",
    "if","implements","import","in","infer","instanceof","interface",
    "is","keyof","let","new","null","of","override","private","protected",
    "public","readonly","return","set","static","super","switch","this",
    "throw","true","try","type","typeof","undefined","var","void","while",
    "with","yield","satisfies","unknown","never","any","namespace",
    "module","package",
}

# Tokenize TypeScript/JavaScript lines. Operates on HTML-escaped text.
TOKEN_RE = re.compile(
    r"(?P<cm>//[^\n]*|/\*[\s\S]*?\*/)"          # comments (line or block)
    r"|(?P<tmpl>`(?:[^`\\]|\\.)*`)"             # template strings (no interp inside)
    r"|(?P<dstr>\"(?:[^\"\\]|\\.)*\")"          # double-quoted strings
    r"|(?P<sstr>'(?:[^'\\]|\\.)*')"             # single-quoted strings
    r"|(?P<num>\b\d[\d_]*(?:\.\d+)?(?:e[+-]?\d+)?\b)"  # numbers
    r"|(?P<ident>\b[A-Za-z_$][A-Za-z0-9_$]*\b)" # identifiers / keywords
)

def highlight_ts(code_escaped: str) -> str:
    """Colourise TS/JS using simple regex tokenizer. Input is already HTML-escaped."""
    out: list[str] = []
    pos = 0
    for m in TOKEN_RE.finditer(code_escaped):
        if m.start() > pos:
            out.append(code_escaped[pos:m.start()])
        tok = m.group()
        if m.group("cm"):
            out.append(f'<span class="hl-cm">{tok}</span>')
        elif m.group("tmpl") or m.group("dstr") or m.group("sstr"):
            out.append(f'<span class="hl-str">{tok}</span>')
        elif m.group("num"):
            out.append(f'<span class="hl-num">{tok}</span>')
        elif m.group("ident"):
            if tok in TS_KEYWORDS:
                out.append(f'<span class="hl-kw">{tok}</span>')
            elif tok[:1].isupper():  # type-ish
                out.append(f'<span class="hl-type">{tok}</span>')
            else:
                out.append(tok)
        else:
            out.append(tok)
        pos = m.end()
    if pos < len(code_escaped):
        out.append(code_escaped[pos:])
    return "".join(out)

JSON_TOKEN_RE = re.compile(
    r"(?P<str>\"(?:[^\"\\]|\\.)*\")"
    r"|(?P<num>-?\b\d[\d_]*(?:\.\d+)?(?:e[+-]?\d+)?\b)"
    r"|(?P<kw>\b(?:true|false|null)\b)"
)

def highlight_json(code_escaped: str) -> str:
    out: list[str] = []
    pos = 0
    for m in JSON_TOKEN_RE.finditer(code_escaped):
        if m.start() > pos:
            out.append(code_escaped[pos:m.start()])
        if m.group("str"):
            out.append(f'<span class="hl-str">{m.group()}</span>')
        elif m.group("num"):
            out.append(f'<span class="hl-num">{m.group()}</span>')
        else:
            out.append(f'<span class="hl-kw">{m.group()}</span>')
        pos = m.end()
    if pos < len(code_escaped):
        out.append(code_escaped[pos:])
    return "".join(out)

def highlight(code: str, lang: str) -> str:
    esc = html.escape(code)
    if lang in ("ts", "tsx", "js", "jsx"):
        return highlight_ts(esc)
    if lang in ("json", "jsonc"):
        return highlight_json(esc)
    if lang in ("md", "markdown"):
        return highlight_markdown(esc)
    if lang in ("xml", "html"):
        return highlight_xml(esc)
    if lang in ("bash", "sh", "shell", "zsh"):
        return highlight_bash(esc)
    return esc

# --- extra language tokenizers ---

_MD_CODE_SPAN_RE = re.compile(r"`([^`\n]+)`")
_MD_HEADING_RE   = re.compile(r"^(#+)(\s.*)$")

def _md_inline(s: str) -> str:
    return _MD_CODE_SPAN_RE.sub(r'<span class="hl-str">`\1`</span>', s)

def highlight_markdown(code_escaped: str) -> str:
    out = []
    for ln in code_escaped.split("\n"):
        if ln.strip() == "---":
            out.append(f'<span class="hl-kw">{ln}</span>')
            continue
        m = _MD_HEADING_RE.match(ln)
        if m:
            out.append(f'<span class="hl-kw">{m.group(1)}</span>{_md_inline(m.group(2))}')
            continue
        # YAML-ish frontmatter "key: value"
        m = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):(\s.*)$", ln)
        if m:
            out.append(f'<span class="hl-type">{m.group(1)}</span>:{_md_inline(m.group(2))}')
            continue
        out.append(_md_inline(ln))
    return "\n".join(out)

_XML_TAG_RE = re.compile(r"(&lt;/?)([a-zA-Z][a-zA-Z0-9_.-]*)(\s[^&]*?)?(/?&gt;)")

def highlight_xml(code_escaped: str) -> str:
    def repl(m: re.Match) -> str:
        lt    = m.group(1)
        name  = m.group(2)
        attrs = m.group(3) or ""
        gt    = m.group(4)
        # color attribute values inside attrs
        attrs_colored = re.sub(
            r"(&quot;[^&]*&quot;|'[^']*')",
            r'<span class="hl-str">\1</span>',
            attrs,
        )
        return (
            f'<span class="hl-cm">{lt}</span>'
            f'<span class="hl-kw">{name}</span>'
            f'{attrs_colored}'
            f'<span class="hl-cm">{gt}</span>'
        )
    return _XML_TAG_RE.sub(repl, code_escaped)

def highlight_bash(code_escaped: str) -> str:
    out = []
    for ln in code_escaped.split("\n"):
        stripped = ln.lstrip()
        if stripped.startswith("#"):
            out.append(f'<span class="hl-cm">{ln}</span>')
            continue
        # Colourise leading "$ " prompt
        m = re.match(r"^(\s*)(\$\s)(.*)$", ln)
        if m:
            rest = _bash_strings(m.group(3))
            out.append(f'{m.group(1)}<span class="hl-kw">{m.group(2)}</span>{rest}')
            continue
        out.append(_bash_strings(ln))
    return "\n".join(out)

def _bash_strings(s: str) -> str:
    return re.sub(
        r"(&quot;[^&\n]*?&quot;|'[^'\n]*?')",
        r'<span class="hl-str">\1</span>',
        s,
    )

# ------------------------------------------------------------------
# Inline markdown
# ------------------------------------------------------------------

# Detect file:line citations (inside an already-extracted code span).
FILE_LINE_RE = re.compile(
    r"^([A-Za-z0-9_./@~-]+\.(?:ts|tsx|js|jsx|json|jsonc|md|mdx|css|sh|py|yaml|yml|toml|lock|env))"
    r"(:\d+(?:[-–]\d+)?)?$"
)

# Bare chNN ref in prose.  Allow ch01..ch23 at word boundary, not followed
# by a markdown-ish alphanumeric continuation.
CHREF_RE = re.compile(r"(?<![A-Za-z0-9_])ch(0[1-9]|1[0-9]|2[0-3])(?![A-Za-z0-9_-])")

# Inline element regexes run in a post-protection phase.
BOLD_RE   = re.compile(r"\*\*([^*\n]+?)\*\*")
# Italic: only *text* where * is not part of **; use a guard.
ITALIC_RE = re.compile(r"(?<!\*)\*([^*\n][^*\n]*?)\*(?!\*)")
LINK_RE   = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)")
AUTOLINK_RE = re.compile(r"&lt;(https?://[^>\s&]+)&gt;")

def render_inline(text: str) -> str:
    """Turn markdown inline markup into HTML. Text is NOT yet HTML-escaped."""
    # 1) Extract code spans (backtick-delimited) with placeholders.
    code_spans: list[str] = []
    def stash_code(m: re.Match) -> str:
        token = m.group(1)
        esc = html.escape(token)
        if FILE_LINE_RE.match(token):
            # Style as a file:line reference
            placeholder = f'<code class="ref">{esc}</code>'
        else:
            placeholder = f'<code>{esc}</code>'
        code_spans.append(placeholder)
        return f"\x00C{len(code_spans) - 1}\x00"
    # Match double-backtick first (allows backticks inside), then single.
    text = re.sub(r"``([^`]+)``", stash_code, text)
    text = re.sub(r"`([^`\n]+)`", stash_code, text)

    # 2) Escape remaining HTML in the non-code text.
    text = html.escape(text, quote=False)

    # 3) Markdown: links, bold, italic, autolink
    text = LINK_RE.sub(lambda m: _link_html(m.group(1), m.group(2), m.group(3)), text)
    text = AUTOLINK_RE.sub(lambda m: f'<a href="{m.group(1)}" rel="noreferrer">{m.group(1)}</a>', text)
    text = BOLD_RE.sub(r"<strong>\1</strong>", text)
    text = ITALIC_RE.sub(r"<em>\1</em>", text)

    # 4) Cross-chapter refs (bare chNN) → pretty chip links
    text = CHREF_RE.sub(lambda m: f'<a class="chref" href="../ch{m.group(1)}/">ch.{m.group(1)}</a>', text)

    # 5) Restore code spans. Loop until stable: nested placeholders
    #    (a placeholder whose stored HTML contains another placeholder)
    #    need multiple passes.
    def unstash(m: re.Match) -> str:
        idx = int(m.group(1))
        return code_spans[idx]
    for _ in range(4):
        new_text = re.sub(r"\x00C(\d+)\x00", unstash, text)
        if new_text == text:
            break
        text = new_text
    return text

def _link_html(label: str, url: str, title: str | None) -> str:
    label_html = html.escape(label, quote=False)
    url_html = html.escape(url, quote=True)
    title_attr = f' title="{html.escape(title or "", quote=True)}"' if title else ""
    rel = " rel=\"noreferrer\"" if url.startswith("http") else ""
    return f'<a href="{url_html}"{title_attr}{rel}>{label_html}</a>'

# ------------------------------------------------------------------
# Block parser
# ------------------------------------------------------------------

HEAD_RE     = re.compile(r"^(#{1,4}) +(.+?)\s*#*\s*$")
FENCE_RE    = re.compile(r"^```([A-Za-z0-9_+\-]*)\s*$")
TABLE_SEP_RE = re.compile(r"^\|?\s*:?-+:?(\s*\|\s*:?-+:?)+\s*\|?\s*$")
LIST_RE_ORD = re.compile(r"^(\s*)(\d+)\.\s+(.*)$")
LIST_RE_UL  = re.compile(r"^(\s*)([-*])\s+(.*)$")
HR_RE       = re.compile(r"^-{3,}\s*$|^_{3,}\s*$|^\*{3,}\s*$")

_SLUG_STRIP_RE = re.compile(r"[^A-Za-z0-9\u3400-\u9fff\-_]+")

def slugify(text: str, used: dict[str, int]) -> str:
    """Turn heading text into a URL-fragment-safe slug.

    Keep ASCII alphanumerics, CJK chars, `-`, `_`. Drop HTML tags first,
    then replace runs of anything-else with `-`. Ensure uniqueness within
    a chapter via the ``used`` counter dict."""
    bare = re.sub(r"<[^>]+>", "", text)          # strip any HTML
    bare = bare.replace("&amp;", "&")             # decode a couple common entities
    bare = bare.replace("&#x27;", "'")
    bare = bare.replace("&quot;", '"')
    # Replace non-slug chars with hyphen, strip edges
    slug = _SLUG_STRIP_RE.sub("-", bare).strip("-").lower()
    if not slug:
        slug = "section"
    n = used.get(slug, 0)
    used[slug] = n + 1
    return slug if n == 0 else f"{slug}-{n + 1}"

def parse_blocks(src: str) -> str:
    lines = src.splitlines()
    n = len(lines)
    out: list[str] = []
    i = 0
    slug_used: dict[str, int] = {}
    # Skip the leading h1 (handled separately as the chapter title).
    while i < n:
        if lines[i].strip().startswith("# "):
            i += 1
            break
        if lines[i].strip():
            # If the chapter has no h1 (shouldn't happen), stop skipping
            break
        i += 1

    first_para_emitted = False

    while i < n:
        line = lines[i]
        stripped = line.rstrip()

        # Blank line
        if not stripped.strip():
            i += 1
            continue

        # Fenced code block
        fm = FENCE_RE.match(stripped)
        if fm:
            lang = fm.group(1) or "text"
            i += 1
            code_lines: list[str] = []
            while i < n and not FENCE_RE.match(lines[i].rstrip()):
                code_lines.append(lines[i])
                i += 1
            if i < n:
                i += 1  # consume closing fence
            out.append(render_code_block(code_lines, lang))
            continue

        # Heading
        hm = HEAD_RE.match(stripped)
        if hm:
            lvl = len(hm.group(1))
            content = render_inline(hm.group(2))
            slug = slugify(hm.group(2), slug_used)
            out.append(
                f'<h{lvl} id="{slug}">{content}'
                f'<a class="h-anchor" href="#{slug}" aria-label="permalink">¶</a>'
                f'</h{lvl}>'
            )
            i += 1
            continue

        # Horizontal rule
        if HR_RE.match(stripped):
            out.append('<hr>')
            i += 1
            continue

        # Blockquote
        if stripped.startswith(">"):
            bq_lines: list[str] = []
            while i < n and lines[i].lstrip().startswith(">"):
                s = lines[i].lstrip()[1:]
                if s.startswith(" "):
                    s = s[1:]
                bq_lines.append(s)
                i += 1
            inner = parse_blocks_inner("\n".join(bq_lines))
            out.append(f"<blockquote>{inner}</blockquote>")
            continue

        # Table: require a separator row on line i+1 after a header-looking row.
        if stripped.startswith("|") and i + 1 < n and TABLE_SEP_RE.match(lines[i + 1].rstrip()):
            tbl_lines: list[str] = []
            while i < n and lines[i].lstrip().startswith("|"):
                tbl_lines.append(lines[i])
                i += 1
            out.append(render_table(tbl_lines))
            continue

        # Ordered list
        if LIST_RE_ORD.match(stripped):
            list_lines, i = gather_list(lines, i, ordered=True)
            out.append(render_list(list_lines, ordered=True))
            continue

        # Unordered list
        if LIST_RE_UL.match(stripped):
            list_lines, i = gather_list(lines, i, ordered=False)
            out.append(render_list(list_lines, ordered=False))
            continue

        # Paragraph
        para_lines = [line]
        i += 1
        while i < n and lines[i].strip() and not is_block_start(lines[i]):
            para_lines.append(lines[i])
            i += 1
        para_text = " ".join(l.strip() for l in para_lines)
        rendered = render_inline(para_text)
        cls = ""
        if not first_para_emitted:
            first_para_emitted = True
            # Drop-cap only if the paragraph starts with an alphabetic/CJK char
            if rendered and not rendered.lstrip().startswith(("<", "§", "—", "·")):
                cls = ' class="drop"'
        out.append(f"<p{cls}>{rendered}</p>")

    return "\n".join(out)

def parse_blocks_inner(src: str) -> str:
    """Parse a sub-block (no h1 skipping, no drop-cap)."""
    lines = src.splitlines()
    n = len(lines)
    out: list[str] = []
    i = 0
    while i < n:
        line = lines[i]
        stripped = line.rstrip()
        if not stripped.strip():
            i += 1
            continue
        fm = FENCE_RE.match(stripped)
        if fm:
            lang = fm.group(1) or "text"
            i += 1
            code_lines: list[str] = []
            while i < n and not FENCE_RE.match(lines[i].rstrip()):
                code_lines.append(lines[i])
                i += 1
            if i < n:
                i += 1
            out.append(render_code_block(code_lines, lang))
            continue
        hm = HEAD_RE.match(stripped)
        if hm:
            lvl = min(len(hm.group(1)) + 1, 4)
            out.append(f"<h{lvl}>{render_inline(hm.group(2))}</h{lvl}>")
            i += 1
            continue
        if LIST_RE_ORD.match(stripped):
            list_lines, i = gather_list(lines, i, ordered=True)
            out.append(render_list(list_lines, ordered=True))
            continue
        if LIST_RE_UL.match(stripped):
            list_lines, i = gather_list(lines, i, ordered=False)
            out.append(render_list(list_lines, ordered=False))
            continue
        # paragraph
        para_lines = [line]
        i += 1
        while i < n and lines[i].strip() and not is_block_start(lines[i]):
            para_lines.append(lines[i])
            i += 1
        text = " ".join(l.strip() for l in para_lines)
        out.append(f"<p>{render_inline(text)}</p>")
    return "\n".join(out)

def is_block_start(line: str) -> bool:
    s = line.rstrip()
    if not s.strip():
        return True
    return (
        HEAD_RE.match(s) is not None
        or FENCE_RE.match(s) is not None
        or s.lstrip().startswith(">")
        or (s.lstrip().startswith("|") and "|" in s.lstrip()[1:])
        or LIST_RE_ORD.match(s) is not None
        or LIST_RE_UL.match(s) is not None
        or HR_RE.match(s) is not None
    )

def gather_list(lines: list[str], i: int, ordered: bool) -> tuple[list[str], int]:
    """Collect all lines belonging to a list, including continuation/indented lines."""
    n = len(lines)
    out = []
    head_re = LIST_RE_ORD if ordered else LIST_RE_UL
    while i < n:
        line = lines[i]
        if not line.strip():
            # Blank line: peek at next non-blank — if indented or list, keep; else stop.
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            if j < n and (head_re.match(lines[j].rstrip()) or lines[j].startswith("  ")):
                out.append(line)
                i += 1
                continue
            break
        if head_re.match(line.rstrip()) or line.startswith(("    ", "   ", "  ")):
            out.append(line)
            i += 1
            continue
        # Another block starting at column 0 — stop
        break
    return out, i

def render_list(list_lines: list[str], ordered: bool) -> str:
    """Render a flat or nested list. Supports one level of nesting via 2+ space indent."""
    tag = "ol" if ordered else "ul"
    out = [f"<{tag}>"]
    head_re = LIST_RE_ORD if ordered else LIST_RE_UL
    i = 0
    n = len(list_lines)
    while i < n:
        line = list_lines[i]
        m = head_re.match(line.rstrip())
        if not m:
            i += 1
            continue
        base_indent = len(m.group(1))
        if ordered:
            content = m.group(3)
        else:
            content = m.group(3)
        item_lines = [content]
        i += 1
        # gather continuation & nested lines
        while i < n:
            nxt = list_lines[i]
            if not nxt.strip():
                i += 1
                continue
            nm_ord = LIST_RE_ORD.match(nxt.rstrip())
            nm_ul  = LIST_RE_UL.match(nxt.rstrip())
            nxt_indent = len(re.match(r"^(\s*)", nxt).group(1))
            if (nm_ord or nm_ul) and nxt_indent <= base_indent:
                break
            # nested list item or continuation
            item_lines.append(nxt[base_indent + 2:] if nxt.startswith(" " * (base_indent + 2)) else nxt.strip())
            i += 1
        item_src = "\n".join(item_lines)
        # Treat as block content when the item contains block-level markup:
        # nested list, fenced code, blockquote, table, or a blank-separated
        # continuation paragraph. Otherwise inline-only for tight rendering.
        has_block = (
            any(re.match(r"^\s*([-*]|\d+\.)\s", l) for l in item_lines[1:])
            or any(FENCE_RE.match(l.rstrip()) for l in item_lines)
            or any(l.lstrip().startswith(">") for l in item_lines[1:])
            or any(l.lstrip().startswith("|") for l in item_lines[1:])
        )
        if has_block:
            item_html = parse_blocks_inner(item_src)
            # Drop <p> wrapper on first paragraph for tighter list items
            item_html = re.sub(r"^<p>(.*?)</p>", r"\1", item_html, count=1, flags=re.DOTALL)
            out.append(f"<li>{item_html}</li>")
        else:
            out.append(f"<li>{render_inline(item_src.replace(chr(10), ' '))}</li>")
    out.append(f"</{tag}>")
    return "\n".join(out)

def render_table(tbl_lines: list[str]) -> str:
    # Split each row by |, strip outer empty cells.
    def split_row(row: str) -> list[str]:
        r = row.strip()
        if r.startswith("|"):
            r = r[1:]
        if r.endswith("|"):
            r = r[:-1]
        return [c.strip() for c in r.split("|")]

    if len(tbl_lines) < 2:
        return ""
    header = split_row(tbl_lines[0])
    # lines[1] is the separator
    body_rows = [split_row(r) for r in tbl_lines[2:]]

    thead = "<tr>" + "".join(f"<th>{render_inline(c)}</th>" for c in header) + "</tr>"
    tbody = "\n".join(
        "<tr>" + "".join(f"<td>{render_inline(c)}</td>" for c in row) + "</tr>"
        for row in body_rows
    )
    return f'<div class="table-wrap"><table><thead>{thead}</thead><tbody>{tbody}</tbody></table></div>'

def render_code_block(code_lines: list[str], lang: str) -> str:
    """Render a fenced code block. If first line looks like a file-path
    comment (// src/foo.ts:12-34), lift it into the figcaption."""
    caption_file: str | None = None
    body_lines = list(code_lines)
    if body_lines:
        first = body_lines[0].strip()
        m = re.match(r"^//\s*(.+\.[a-zA-Z]+(?::\d+(?:-\d+)?)?)\s*$", first)
        if m:
            candidate = m.group(1)
            # Only treat as file:line caption if it plausibly is a path
            if "/" in candidate or re.search(r"\.(ts|tsx|js|jsx|json|md|mdx|css|sh|py)(:|$)", candidate):
                caption_file = candidate
                body_lines = body_lines[1:]
                # drop a trailing empty first line left behind
                while body_lines and not body_lines[0].strip():
                    body_lines = body_lines[1:]

    code = "\n".join(body_lines)
    highlighted = highlight(code, lang)
    caption_html = ""
    if caption_file:
        caption_html = (
            f'<figcaption><span class="file">{html.escape(caption_file)}</span>'
            f'<span class="lang">{html.escape(lang)}</span></figcaption>'
        )
    else:
        caption_html = (
            f'<figcaption><span></span>'
            f'<span class="lang">{html.escape(lang)}</span></figcaption>'
        )
    return (
        f'<figure class="codeblock">{caption_html}'
        f'<pre><code class="language-{html.escape(lang)}">{highlighted}</code></pre>'
        f'</figure>'
    )

# ------------------------------------------------------------------
# Chapter title extraction
# ------------------------------------------------------------------

def extract_title(src: str) -> tuple[str, str]:
    """Return (primary_title, subtitle_hint). Parses the first h1 line."""
    for line in src.splitlines():
        if line.startswith("# "):
            raw = line[2:].strip()
            # Common patterns:
            #   "第 N 章 标题"           -> subtitle = ""
            #   "chNN Title：中文副标"    -> split on ":" or "："
            #   "chNN · Title — sub"     -> dashes
            text = raw
            # Strip "第 N 章 " / "chNN " / "chNN. " / "chNN · " / "chNN、"
            text = re.sub(r"^第\s*\d+\s*章[　\s]*", "", text)
            text = re.sub(r"^ch\s*\d+[\.·、\s　]*", "", text, flags=re.IGNORECASE)
            # Split on first colon / em-dash etc.
            parts = re.split(r"[:：—]\s*", text, maxsplit=1)
            head = parts[0].strip()
            sub  = parts[1].strip() if len(parts) > 1 else ""
            return head, sub
    return "", ""

# ------------------------------------------------------------------
# Page template
# ------------------------------------------------------------------

FONTS_HEAD = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;1,300;1,400;1,500'
    '&family=Albert+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400'
    '&family=JetBrains+Mono:wght@300;400;500&display=swap" rel="stylesheet">'
    '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/lxgw-wenkai-webfont@1.7.0/style.css">'
)

def build_showcase_bar() -> str:
    # Chapter pages get a clean, minimal nav: home + archive link only.
    return (
        '<nav class="showcase-bar">'
        '<a href="../">← 回目录</a>'
        '<div class="switcher">'
        '<a href="../showcase.html">设计备选</a>'
        '</div>'
        '</nav>'
    )

def build_prev_next_nav(ch: dict) -> str:
    idx = ch["id"] - 1
    prev_html = ""
    next_html = ""
    if idx > 0:
        p = CHAPTERS[idx - 1]
        prev_html = (
            f'<a class="nav-link prev" href="../ch{p["id"]:02d}/">'
            f'<span class="dir">← Ch.{p["id"]:02d} · prev <kbd class="kb">[</kbd></span>'
            f'<span class="t">{html.escape(p["en"])}<span class="cn">{html.escape(p["cn"])}</span></span>'
            f'</a>'
        )
    else:
        prev_html = '<span></span>'
    if idx < len(CHAPTERS) - 1:
        nxt = CHAPTERS[idx + 1]
        next_html = (
            f'<a class="nav-link next" href="../ch{nxt["id"]:02d}/">'
            f'<span class="dir"><kbd class="kb">]</kbd> Ch.{nxt["id"]:02d} · next →</span>'
            f'<span class="t">{html.escape(nxt["en"])}<span class="cn">{html.escape(nxt["cn"])}</span></span>'
            f'</a>'
        )
    else:
        next_html = '<span></span>'
    home = '<a class="nav-home" href="../">§ 目录</a>'
    return (
        f'<nav class="chap-nav">'
        f'{prev_html}{home}{next_html}'
        f'</nav>'
    )

def count_refs(src: str) -> int:
    return sum(1 for _ in re.finditer(r"`[A-Za-z0-9_./@-]+\.(ts|tsx|js|json|md|css|sh|py):\d", src))

def estimate_reading_minutes(src: str) -> int:
    # strip code blocks roughly
    plain = re.sub(r"```[\s\S]*?```", "", src)
    cjk = sum(1 for c in plain if '\u3400' <= c <= '\u9fff' or '\u4e00' <= c <= '\u9fff')
    words = len(re.findall(r"[A-Za-z0-9]+", plain))
    # ~400 cjk/min, ~200 words/min
    return max(3, round(cjk / 400 + words / 200))

def render_page(ch: dict, title: str, cn_hint: str, body_html: str, src: str) -> str:
    part = PARTS[ch["part"]]
    refs = count_refs(src)
    read_min = estimate_reading_minutes(src)
    showcase_bar = build_showcase_bar()
    chap_nav = build_prev_next_nav(ch)
    outline_entries = extract_h2_outline(body_html)
    outline_html = render_outline(outline_entries)
    part_tag_class = f"p{ch['part']}"

    # English display title.  Prefer the config "en" (clean) then fall back to
    # the parsed title head.
    display_en = ch["en"]
    display_cn = ch["cn"] if ch["cn"] else (cn_hint or title)

    page_title = f"Ch.{ch['id']:02d} {display_en} · {display_cn} — Claude Code 源码解读"
    og_desc    = f"《Claude Code 源码解读》第 {ch['id']} 章 —— {display_cn}（{ch['topic']}）"

    chapter_url = f"https://nayuta403.github.io/claude-code-book/ch{ch['id']:02d}/"
    book_url    = "https://nayuta403.github.io/claude-code-book/"
    # JSON-LD Article schema (escape-safe: pre-build dict, json.dumps for safety)
    import json as _json
    jsonld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": f"Ch.{ch['id']:02d} {display_en} · {display_cn}",
        "description": og_desc,
        "inLanguage": "zh-Hans",
        "datePublished": "2026-04-20",
        "author":    {"@type": "Person",       "name": "Nayuta"},
        "publisher": {"@type": "Organization", "name": "Claude Code 源码解读"},
        "isPartOf":  {"@type": "Book", "name": "Claude Code 源码解读", "url": book_url},
        "mainEntityOfPage": chapter_url,
        "position":  ch["id"],
    }
    jsonld_script = (
        '<script type="application/ld+json">'
        + _json.dumps(jsonld, ensure_ascii=False, separators=(",", ":"))
        + '</script>'
    )

    out = f"""<!DOCTYPE html>
<html lang="zh-Hans">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(page_title)}</title>
<meta name="description" content="{html.escape(og_desc)}">
<meta property="og:title" content="{html.escape(page_title)}">
<meta property="og:description" content="{html.escape(og_desc)}">
<meta property="og:type" content="article">
<meta property="og:url" content="https://nayuta403.github.io/claude-code-book/ch{ch['id']:02d}/">
<meta property="og:locale" content="zh_CN">
<meta name="twitter:card" content="summary">
<link rel="icon" type="image/svg+xml" href="../favicon.svg">
{FONTS_HEAD}
<link rel="stylesheet" href="../assets/book.css">
{jsonld_script}
</head>
<body>

{showcase_bar}

<header class="chap-head">
  <div>
    <div class="crumb">
      <a href="../">目录</a>
      <span class="sep">/</span>
      <span class="part-tag {part_tag_class}">Part {part['id']} · {html.escape(part['cn'])}</span>
    </div>
    <div class="chap-num">Chapter · {ch['id']:02d} / 23</div>
    <h1 class="chap-title">{html.escape(display_en)}<span class="cn">{html.escape(display_cn)}</span></h1>
  </div>
  <aside class="chap-meta">
    <div><div class="km">part</div><div class="vm">{html.escape(part['cn'])}（{html.escape(part['en'])}）</div></div>
    <div><div class="km">topic</div><div class="vm m">{html.escape(ch['topic'])}</div></div>
    <div><div class="km">reading</div><div class="vm">≈ {read_min} min</div></div>
    <div><div class="km">source refs</div><div class="vm m">{refs}</div></div>
  </aside>
</header>

<article class="article">
  <div class="prose">
{outline_html}{body_html}
  </div>
</article>

{chap_nav}

<script src="../assets/book.js" defer></script>

<footer class="colophon">
  <div class="left">Claude <span class="dot">&amp;</span> Code</div>
  <div class="right">
    set in EB garamond · albert sans · jetbrains mono · LXGW wenkai<br>
    《Claude Code 源码解读》 · ch.{ch['id']:02d}
  </div>
</footer>

</body>
</html>
"""
    return out

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def extract_h2_outline(body_html: str) -> list[tuple[str, str]]:
    """Return [(slug, text)] for each top-level h2 in the rendered body."""
    entries: list[tuple[str, str]] = []
    for m in re.finditer(r'<h2 id="([^"]+)">([\s\S]+?)</h2>', body_html):
        slug = m.group(1)
        inner = m.group(2)
        inner = re.sub(r'<a class="h-anchor"[\s\S]*?</a>', '', inner)
        text = re.sub(r'<[^>]+>', '', inner).strip()
        if text:
            entries.append((slug, text))
    return entries

def render_outline(entries: list[tuple[str, str]]) -> str:
    """Render a collapsible 本章目录 block. Skip if chapter has <3 h2s."""
    if len(entries) < 3:
        return ""
    items = "".join(
        f'<li><a href="#{slug}">{html.escape(text, quote=False)}</a></li>'
        for slug, text in entries
    )
    return (
        '<details class="chap-outline">'
        f'<summary>§ 本章目录 <span class="count">· {len(entries)} 节</span></summary>'
        f'<ol>{items}</ol>'
        '</details>'
    )

def build_chapter(ch: dict) -> Path:
    src_path = SRC_DIR / f"{ch['slug']}.md"
    src = src_path.read_text(encoding="utf-8")
    title, cn_hint = extract_title(src)
    body = parse_blocks(src)
    html_out = render_page(ch, title, cn_hint, body, src)
    out_dir = OUT_ROOT / f"ch{ch['id']:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "index.html"
    out_path.write_text(html_out, encoding="utf-8")
    return out_path

def main() -> int:
    only = None
    if len(sys.argv) > 1:
        only = sys.argv[1]
    built = []
    for ch in CHAPTERS:
        if only and ch["slug"] != only and f"ch{ch['id']:02d}" != only:
            continue
        try:
            path = build_chapter(ch)
            built.append((ch["id"], path))
            print(f"  built ch{ch['id']:02d}  →  {path}")
        except Exception as e:
            print(f"  FAIL  ch{ch['id']:02d}: {e}", file=sys.stderr)
            raise
    print(f"\n  total: {len(built)} chapters")
    return 0

if __name__ == "__main__":
    sys.exit(main())
