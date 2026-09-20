#!/usr/bin/env python3
"""Render this bounded Markdown subset to a self-contained offline review document."""
import hashlib
import html
from pathlib import Path
import re

root=Path(__file__).resolve().parents[3]
source=root/'docs/specs/acp-coordination.md'
target=source.with_suffix('.html')
raw=source.read_text()
body=re.sub(r'\A---\n.*?\n---\n','',raw,flags=re.S)

def inline(text):
    text=html.escape(text)
    text=re.sub(r'`([^`]+)`',r'<code>\1</code>',text)
    text=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',text)
    text=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',lambda m:f'<a href="{m[2]}">{m[1]}</a>',text)
    return text

lines=body.splitlines()
parts=[]
nav=[]
i=0
while i<len(lines):
    line=lines[i]
    if not line.strip():
        i+=1
        continue
    if line.startswith('```'):
        language=line[3:]
        code=[]
        i+=1
        while i<len(lines) and not lines[i].startswith('```'):
            code.append(lines[i]); i+=1
        if language=='mermaid':
            labels={m[1]:m[2] for text in code for m in re.finditer(r'\b([A-Z][0-9]*)[\[{]([^\]}]+)[\]}]',text)}
            parts.append('<div class="table-wrap"><table><caption>Flow and recovery paths</caption><thead><tr><th>From</th><th>Condition</th><th>Next</th></tr></thead><tbody>')
            for edge in code:
                simplified=re.sub(r'([A-Z][0-9]*)[\[{][^\]}]+[\]}]',r'\1',edge).strip()
                match=re.match(r'^([A-Z][0-9]*)\s+--(?:(.*?)--)?>(?:\s*)([A-Z][0-9]*)$',simplified)
                if match:
                    a,condition,b=match.groups()
                    parts.append(f'<tr><td>{inline(labels.get(a,a))}</td><td>{inline(condition.strip() if condition else "Continue")}</td><td>{inline(labels.get(b,b))}</td></tr>')
            parts.append('</tbody></table></div><details><summary>Mermaid source</summary><pre>'+html.escape('\n'.join(code))+'</pre></details>')
        else:
            parts.append('<pre><code>'+html.escape('\n'.join(code))+'</code></pre>')
        i+=1
        continue
    heading=re.match(r'^(#{1,6}) (.*)',line)
    if heading:
        level=len(heading[1]); title=heading[2]
        ident=re.sub('[^a-z0-9]+','-',title.lower()).strip('-')
        parts.append(f'<h{level} id="{ident}">{inline(title)}</h{level}>')
        if level==2:
            nav.append(f'<a href="#{ident}">{inline(title)}</a>')
        i+=1
        continue
    if line.startswith('|'):
        rows=[]
        while i<len(lines) and lines[i].startswith('|'):
            rows.append([x.strip() for x in lines[i].strip().strip('|').split('|')]); i+=1
        parts.append('<div class="table-wrap"><table><thead><tr>'+''.join('<th scope="col">'+inline(c)+'</th>' for c in rows[0])+'</tr></thead><tbody>')
        for row in rows[2:]:
            parts.append('<tr>'+''.join('<td>'+inline(c)+'</td>' for c in row)+'</tr>')
        parts.append('</tbody></table></div>')
        continue
    listing=re.match(r'^(\d+\.|-) (.*)',line)
    if listing:
        ordered=listing[1]!='-'; tag='ol' if ordered else 'ul'
        parts.append('<'+tag+'>')
        while i<len(lines):
            item=re.match(r'^(\d+\.|-) (.*)',lines[i])
            if not item:
                break
            text=[item[2]]; i+=1
            while i<len(lines) and lines[i].startswith('  '):
                text.append(lines[i].strip()); i+=1
            parts.append('<li>'+inline(' '.join(text))+'</li>')
        parts.append('</'+tag+'>')
        continue
    paragraph=[line]; i+=1
    while i<len(lines) and lines[i].strip() and not re.match(r'^(#|\||```|\d+\. |\- )',lines[i]):
        paragraph.append(lines[i]); i+=1
    parts.append('<p>'+inline(' '.join(paragraph))+'</p>')

css='''
:root{color-scheme:light;--ink:#17212b;--muted:#485766;--paper:#fff;--line:#ccd5df;--link:#154f8a;--shade:#f3f6fa}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.6 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
header,main,footer{max-width:1180px;margin:auto;padding:24px 32px}header{border-bottom:1px solid var(--line);background:var(--shade)}header p{margin:.4rem 0}.eyebrow{font-size:13px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted)}nav{display:flex;flex-wrap:wrap;gap:8px 22px;font-size:14px}a{color:var(--link);text-underline-offset:3px}a:focus-visible,summary:focus-visible{outline:3px solid var(--link);outline-offset:4px}h1{font-size:2.1rem;line-height:1.2}h2{font-size:1.65rem;line-height:1.3;margin-top:3rem;border-top:1px solid var(--line);padding-top:1.3rem}h3{font-size:1.2rem;margin-top:2rem}p,li{max-width:96ch}li{margin:.6rem 0}code{font:.86em ui-monospace,SFMono-Regular,Consolas,monospace;background:var(--shade);padding:.1em .25em;overflow-wrap:anywhere}pre{background:var(--shade);padding:16px;overflow:auto;font-size:13px}.table-wrap{width:100%;overflow-x:auto;margin:1.5rem 0}table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.45}th,td{padding:12px;vertical-align:top;text-align:left;border:1px solid var(--line);min-width:145px}th{background:var(--shade);font-weight:650}caption{text-align:left;font-weight:700;padding:10px 0}summary{cursor:pointer}footer{font-size:13px;color:var(--muted);border-top:1px solid var(--line);overflow-wrap:anywhere}.skip{position:absolute;top:-100px}.skip:focus{top:4px;background:white;padding:8px} @media(max-width:600px){header,main,footer{padding:20px}body{font-size:16px}h1{font-size:1.8rem}} @media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}} @media print{header nav,.skip{display:none}header,main,footer{max-width:none;padding:8px}table{font-size:10px}h2,h3{break-after:avoid}.table-wrap{overflow:visible}a{color:inherit}}
'''
result='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>ACP multi-harness coordination specification</title><style>'''+css+'''</style></head><body><a class="skip" href="#content">Skip to specification</a><header><p class="eyebrow">AI-Forward Pack · Specification and live spike · 20 September 2026</p><p><strong>Observed transport capability is not production qualification.</strong> Verified cells apply only to the tested version, policy and environment. “Not established” is an open capability, not proof of impossibility.</p><p><a href="acp-coordination.md">Markdown source</a> · <a href="../knowledge/acp-compatibility/index.md">Evidence and reproduction</a></p><nav aria-label="Contents">'''+''.join(nav)+'''</nav></header><main id="content">'''+''.join(parts)+'''</main><footer>Self-contained offline rendition. Source SHA-256: '''+hashlib.sha256(raw.encode()).hexdigest()+'''. Flow tables preserve the Mermaid edges; the original diagram source remains available beside them.</footer></body></html>'''
target.write_text(result)
print(target)
