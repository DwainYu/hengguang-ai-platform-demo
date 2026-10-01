#!/usr/bin/env python3
"""Regenerate docs/interview/index.html from HENGGUANG_INTERVIEW_GUIDE.md.

Usage: python3 docs/interview/build_index.py
No dependencies beyond the standard library.
Produces a self-contained HTML file (no external resources).
"""

import html
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "HENGGUANG_INTERVIEW_GUIDE.md"
OUT = HERE / "index.html"


def md_inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"~~([^~]+)~~", r"<del>\1</del>", s)
    return s


def flush_table(rows):
    if not rows:
        return ""

    def split_row(r):
        return [c.strip() for c in r.strip().strip("|").split("|")]

    head = split_row(rows[0])
    if len(rows) > 2 and re.match(r"^\s*\|?[\s:|-]+\|?\s*$", rows[1]):
        body_rows = rows[2:]
    else:
        body_rows = rows[1:]
    thead = "".join(f"<th>{md_inline(c)}</th>" for c in head)
    tbody = ""
    for r in body_rows:
        cells = "".join(f"<td>{md_inline(c)}</td>" for c in split_row(r))
        tbody += f"<tr>{cells}</tr>"
    return f"<table><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table>"


def md_block(body):
    out = []
    in_code = False
    code_buf = []
    table_buf = []
    for ln in body.split("\n"):
        if ln.startswith("```"):
            if in_code:
                out.append(flush_table(table_buf))
                table_buf = []
                out.append(f"<pre><code>{md_inline(chr(10).join(code_buf))}</code></pre>")
                code_buf, in_code = [], False
            else:
                out.append(flush_table(table_buf))
                table_buf = []
                in_code = True
            continue
        if in_code:
            code_buf.append(ln)
            continue
        if ln.strip().startswith("|"):
            table_buf.append(ln)
            continue
        out.append(flush_table(table_buf))
        table_buf = []
        s = ln.rstrip()
        if not s.strip():
            out.append("")
        elif s.startswith("#### "):
            out.append(f"<h4>{md_inline(s[5:])}</h4>")
        elif s.startswith("##### "):
            out.append(f"<h5>{md_inline(s[6:])}</h5>")
        elif s.startswith(">"):
            out.append(f"<blockquote>{md_inline(s.lstrip(chr(62) + chr(32)))}</blockquote>")
        elif re.match(r"^\d+\. ", s):
            txt = re.sub(r"^\d+\. ", "", s)
            out.append(f"<li>{md_inline(txt)}</li>")
        elif s.startswith("- "):
            out.append(f"<li>{md_inline(s[2:])}</li>")
        else:
            out.append(f"<p>{md_inline(s)}</p>")
    out.append(flush_table(table_buf))
    if in_code:
        code_str = md_inline("\n".join(code_buf))
        out.append(f"<pre><code>{code_str}</code></pre>")
    return "\n".join(out)


def parse_sections(text):
    lines = text.splitlines()
    sections = []
    cur = None
    body_lines = []

    def flush_sec():
        nonlocal cur, body_lines
        if cur is not None:
            cur["body"] = "\n".join(body_lines).strip()
            sections.append(cur)
        body_lines = []

    for ln in lines:
        m1 = re.match(r"^# (.+)$", ln)
        m2 = re.match(r"^## (.+)$", ln)
        if m1:
            flush_sec()
            cur = {"title": m1.group(1), "body": ""}
            body_lines = []
        elif m2 and cur is not None:
            body_lines.append("## " + m2.group(1))
            body_lines.append("")
        else:
            body_lines.append(ln)
    flush_sec()
    return sections, lines


def parse_sec(sec):
    parts = re.split(r"^## ", sec["body"], flags=re.M)
    lead = parts[0].strip()
    qs = []
    for p in parts[1:]:
        qtitle, _, qbody = p.partition("\n")
        qs.append((qtitle.strip(), qbody.strip()))
    return lead, qs


def main():
    src = SRC.read_text(encoding="utf-8")
    sections, lines = parse_sections(src)
    doc_title = sections[0]["title"]
    first_idx = next(i for i, ln in enumerate(lines) if ln.startswith("# 0 "))
    intro = "\n".join(lines[1:first_idx]).strip()
    body_secs = sections[1:]

    tag_order = [
        "FACT",
        "INFERENCE",
        "MY DESIGN",
        "PRODUCTION NEXT",
        "需要本人确认",
    ]
    section_html = []
    toc_html = []
    for sec in body_secs:
        lead, qs = parse_sec(sec)
        content = lead + ("\n" + "\n".join(q[0] + "\n" + q[1] for q in qs) if qs else "")
        tags = [t for t in tag_order if t in content]
        sid = re.sub(r"[^a-z0-9]+", "-", sec["title"].lower()).strip("-")
        q_html = []
        for qtitle, qbody in qs:
            q_html.append(
                f'<details class="q"><summary>{md_inline(qtitle)}</summary>'
                f'<div class="qbody">{md_block(qbody)}</div></details>'
            )
        lead_html = md_block(lead) if lead else ""
        section_html.append(
            f'<section id="{sid}" data-tags="{" ".join(tags)}">'
            f"<h2>{md_inline(sec['title'])}</h2>"
            f"{lead_html}{''.join(q_html)}</section>"
        )
        toc_html.append(f'<a href="#{sid}">{md_inline(sec["title"])}</a>')

    toc = "\n".join(toc_html)
    body_content = "\n".join(section_html)
    page = "\n".join(
        [
            "<!DOCTYPE html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            "<title>恒光 AI 平台工程师 · 面试题库</title>",
            "<style>",
            "\n".join(CSS_LINES),
            "</style>",
            "</head>",
            "<body>",
            "<header>",
            '<input id="q" type="search"',
            'placeholder="搜索题目 / 关键词 / 文件路径…（Enter 展开全部匹配）"',
            'autocomplete="off">',
        ]
        + TAG_BTNS
        + [
            '<span class="count" id="stat"></span>',
            "</header>",
            "<main>",
            '<nav id="toc">',
            toc,
            "</nav>",
            '<div class="content" id="content">',
            f"<h1>{md_inline(doc_title)}</h1>",
            md_block(intro),
            body_content,
            "</div>",
            "<script>",
            "\n".join(JS_LINES),
            "</script>",
            "</body>",
            "</html>",
        ]
    )
    OUT.write_text(page, encoding="utf-8")
    print(f"written {OUT} ({len(page)} bytes, {len(body_secs)} sections)")


TAG_BTNS = [
    '<span class="tagbtn" data-t="FACT">FACT</span>',
    '<span class="tagbtn" data-t="INFERENCE">INFERENCE</span>',
    '<span class="tagbtn" data-t="MY DESIGN">MY DESIGN</span>',
    '<span class="tagbtn" data-t="PRODUCTION NEXT">PRODUCTION NEXT</span>',
    '<span class="tagbtn" data-t="需要本人确认">需要本人确认</span>',
]

HEAD_LINES = [
    ":root{--bg:#0f1115;--panel:#171a21;--panel2:#1e2230;",
    "--fg:#dfe3ec;--muted:#8a93a8;--acc:#5aa9ff;--ok:#4ade80;",
    "--warn:#facc15;--line:#2a2f3d}",
]

CSS_LINES = [
    ":root{--bg:#0f1115;--panel:#171a21;--panel2:#1e2230;",
    "--fg:#dfe3ec;--muted:#8a93a8;--acc:#5aa9ff;--ok:#4ade80;",
    "--warn:#facc15;--line:#2a2f3d}",
    "*{box-sizing:border-box}",
    "body{margin:0;background:var(--bg);color:var(--fg);",
    "font:15px/1.65 system-ui,-apple-system,'Segoe UI',Roboto,",
    "'PingFang SC','Microsoft YaHei',sans-serif}",
    "header{position:sticky;top:0;background:var(--panel);",
    "border-bottom:1px solid var(--line);padding:12px 20px;z-index:10;",
    "display:flex;align-items:center;gap:8px;flex-wrap:wrap}",
    "header input{width:min(460px,44%);padding:8px 12px;border-radius:8px;",
    "border:1px solid var(--line);background:var(--panel2);color:var(--fg);",
    "font-size:14px}",
    ".tagbtn{padding:6px 10px;border-radius:8px;border:1px solid var(--line);",
    "background:var(--panel2);color:var(--muted);cursor:pointer;",
    "font-size:12px;font-family:ui-monospace,monospace}",
    ".tagbtn.active{color:var(--fg);border-color:var(--acc);background:#1b2b45}",
    ".count{font-size:12px;color:var(--muted);margin-left:auto}",
    "main{display:grid;grid-template-columns:240px minmax(0,1fr);",
    "max-width:1400px;margin:0 auto}",
    "nav{position:sticky;top:56px;align-self:start;",
    "max-height:calc(100vh - 56px);overflow:auto;padding:14px 10px;",
    "border-right:1px solid var(--line)}",
    "nav a{display:block;color:var(--muted);text-decoration:none;",
    "padding:3px 8px;border-radius:6px;font-size:13px;white-space:nowrap;",
    "overflow:hidden;text-overflow:ellipsis}",
    "nav a:hover{background:var(--panel2);color:var(--fg)}",
    "nav a.on{color:var(--acc);background:#1b2b45}",
    ".content{padding:20px 26px 80px;min-width:0}",
    "h1{font-size:22px;margin:0 0 8px}",
    "h2{font-size:18px;margin:28px 0 10px;border-bottom:1px solid var(--line);",
    "padding-bottom:6px}",
    "h4{font-size:14px;margin:14px 0 4px;color:var(--acc)}",
    "h5{font-size:13px;margin:10px 0 4px;color:var(--muted)}",
    "p{margin:6px 0}",
    "code{background:var(--panel2);padding:1px 5px;border-radius:4px;",
    "font-size:13px;font-family:ui-monospace,Menlo,Consolas,monospace}",
    "pre{background:var(--panel2);padding:12px;border-radius:8px;overflow:auto;",
    "font-size:13px;line-height:1.5}",
    "pre code{background:none;padding:0}",
    "table{border-collapse:collapse;width:100%;margin:10px 0;font-size:13px}",
    "th,td{border:1px solid var(--line);padding:6px 8px;",
    "text-align:left;vertical-align:top}",
    "th{background:var(--panel2)}",
    "blockquote{border-left:3px solid var(--acc);margin:8px 0;",
    "padding:4px 12px;color:var(--muted);",
    "background:rgba(90,169,255,.06);border-radius:0 6px 6px 0}",
    "li{margin:3px 0}",
    "details.q{margin:12px 0;border:1px solid var(--line);border-radius:8px;",
    "background:var(--panel);overflow:hidden}",
    "details.q summary{cursor:pointer;padding:10px 14px;font-weight:600;",
    "font-size:14px;background:var(--panel2)}",
    "details.q summary::-webkit-details-marker{display:none}",
    "details.q summary::before{content:'▸ ';color:var(--acc)}",
    "details.q[open] summary::before{content:'▾ '}",
    ".qbody{padding:10px 16px}",
    ".tag{display:inline-block;padding:0 6px;margin:0 2px;border-radius:4px;",
    "font-size:11px;font-family:ui-monospace,monospace;white-space:nowrap}",
    ".tag.FACT{color:var(--ok);border:1px solid var(--ok)}",
    ".tag.INFERENCE{color:var(--warn);border:1px solid var(--warn)}",
    ".tag.MYDESIGN{color:var(--acc);border:1px solid var(--acc)}",
    ".tag.PRODUCTIONNEXT{color:#c084fc;border:1px solid #c084fc}",
    ".tag.CONFIRM{color:#f472b6;border:1px solid #f472b6}",
    "section{margin-bottom:34px}",
    ".hidden{display:none}",
    "@media(max-width:900px){main{grid-template-columns:1fr}nav{display:none}}",
]

JS_LINES = [
    "(function(){",
    'var sections=[].slice.call(document.querySelectorAll("section"));',
    'var tocLinks=[].slice.call(document.querySelectorAll("#toc a"));',
    'var q=document.getElementById("q");',
    'var stat=document.getElementById("stat");',
    'var tagbtns=[].slice.call(document.querySelectorAll(".tagbtn"));',
    "var activeTags={};",
    "",
    "// 标签高亮：[FACT] [INFERENCE] [MY DESIGN] [PRODUCTION NEXT/_NEXT] [需要本人确认：...]",
    'document.querySelectorAll("p,li,td,th,blockquote,h4,h5,summary").forEach(function(el){',
    "el.innerHTML=el.innerHTML.replace(/\\[(FACT|INFERENCE|MY DESIGN|PRODUCTION NEXT|PRODUCTION_NEXT|\\u9700\\u8981\\u672c\\u4eba\\u786e\\u8ba4[\\u4e00-\\u9fff\\u3a\\u003a\\w]*)/g, function(m, kw){",  # noqa: E501
    'var cls = {FACT:"FACT",INFERENCE:"INFERENCE","MY DESIGN":"MYDESIGN",'
    '"PRODUCTION NEXT":"PRODUCTIONNEXT",PRODUCTION_NEXT:"PRODUCTIONNEXT"}'
    '[kw] || "CONFIRM";',
    'if (kw.indexOf("\\u9700\\u8981\\u672c\\u4eba\\u786e\\u8ba4") === 0) {',
    'var rest = kw.slice(6).replace(/^[\\[\\]:\\uff1a\\u003a\\s]*/, "");',
    "return '<span class=\"tag CONFIRM\">\\u9700\\u8981\\u672c\\u4eba\\u786e\\u8ba4</span>'",
    '  + (rest ? "]" + rest : "");',
    "}",
    "return '<span class=\"tag '+cls+'\">'+kw+'</span>';",
    "});",
    "});",
    "",
    "function apply(){",
    "var term=q.value.trim().toLowerCase();",
    "var vis=0;",
    "sections.forEach(function(s){",
    "var ok=true;",
    "if(term && s.textContent.toLowerCase().indexOf(term)===-1) ok=false;",
    'var tags=(s.dataset.tags||"").split(" ");',
    "Object.keys(activeTags).forEach(function(t){",
    "if(activeTags[t] && tags.indexOf(t)===-1) ok=false;",
    "});",
    "s.classList.toggle('hidden',!ok);",
    "if(ok)vis++;",
    "});",
    'document.querySelectorAll("section:not(.hidden) details.q").forEach(function(d){',
    "d.open = term ? (d.textContent.toLowerCase().indexOf(term)!==-1)",
    "  : true;",
    "});",
    'stat.textContent=vis+" / "+sections.length+" 节";',
    "}",
    "q.addEventListener('input',apply);",
    "q.addEventListener('keydown',function(e){ if(e.key==='Enter'){",
    'document.querySelectorAll("section:not(.hidden) details.q").forEach('
    "function(d){d.open=true;});",
    "} });",
    "tagbtns.forEach(function(b){",
    "b.addEventListener('click',function(){",
    "var t=b.dataset.t;",
    "activeTags[t]=!activeTags[t];",
    "b.classList.toggle('active',!!activeTags[t]);",
    "apply();",
    "});",
    "});",
    'if("IntersectionObserver" in window){',
    "var io=new IntersectionObserver(function(entries){",
    "entries.forEach(function(e){",
    "if(e.isIntersecting){",
    "tocLinks.forEach(function(a){a.classList.remove('on');});",
    'var ln=document.querySelector("#toc a[href=\'#" + e.target.id + "\']");',
    "if(ln)ln.classList.add('on');",
    "}",
    "});",
    "},{rootMargin:'-40% 0px -55% 0px'});",
    "sections.forEach(function(s){io.observe(s);});",
    "}",
    "apply();",
    "})();",
]


if __name__ == "__main__":
    main()
