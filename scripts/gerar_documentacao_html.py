import re
from pathlib import Path

def generate_html_documentation():
    base_dir = Path(__file__).resolve().parent.parent
    md_path = base_dir / "DOCUMENTACAO_SISTEMA_NYMPHIA.md"
    html_path = base_dir / "DOCUMENTACAO_SISTEMA_NYMPHIA.html"

    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    lines = md_text.split('\n')
    body_html = []
    
    in_code = False
    code_lang = ""
    code_buffer = []

    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Code block / Mermaid
        if line.startswith('```'):
            if in_code:
                in_code = False
                if code_lang == 'mermaid':
                    raw_mermaid = "\n".join(code_buffer)
                    body_html.append(f'<div class="mermaid-wrapper"><div class="mermaid">\n{raw_mermaid}\n</div></div>')
                else:
                    escaped = "\n".join(code_buffer).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    body_html.append(f'<pre class="code-block {code_lang}"><code>{escaped}</code></pre>')
                code_buffer = []
            else:
                in_code = True
                code_lang = line[3:].strip()
                code_buffer = []
            i += 1
            continue

        if in_code:
            code_buffer.append(line)
            i += 1
            continue

        # Blank
        if not line.strip():
            i += 1
            continue

        # Horizontal rule
        if line.strip() in ('---', '***', '___'):
            body_html.append('<hr/>')
            i += 1
            continue

        # Headings
        if line.startswith('# '):
            title = line[2:].strip()
            body_html.append(f'<h1 class="doc-title">{title}</h1>')
            i += 1
            continue

        if line.startswith('## '):
            h2 = line[3:].strip()
            slug = re.sub(r'[^a-zA-Z0-9]+', '-', h2).strip('-').lower()
            body_html.append(f'<h2 id="{slug}">{h2}</h2>')
            i += 1
            continue

        if line.startswith('### '):
            h3 = line[4:].strip()
            body_html.append(f'<h3>{h3}</h3>')
            i += 1
            continue

        # Callouts / Quotes
        if line.startswith('> '):
            callout = line[2:].strip()
            # Process inline formatting
            callout = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', callout)
            callout = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2" target="_blank">\1</a>', callout)
            callout = re.sub(r'`([^`]+)`', r'<code>\1</code>', callout)
            body_html.append(f'<div class="callout"><span class="badge">Aviso Clínico / Nota</span><p>{callout}</p></div>')
            i += 1
            continue

        # Table
        if line.startswith('|') and '|' in line[1:]:
            t_lines = [line]
            i += 1
            while i < len(lines) and lines[i].strip().startswith('|'):
                t_lines.append(lines[i].strip())
                i += 1
            
            rows = []
            for tl in t_lines:
                if re.match(r'^\|\s*[-:]+[-|\s:]*\|$', tl):
                    continue
                cols = [c.strip() for c in tl.strip('|').split('|')]
                rows.append(cols)

            if rows:
                table_html = ['<div class="table-responsive"><table>']
                # Header
                table_html.append('<thead><tr>')
                for c in rows[0]:
                    table_html.append(f'<th>{c}</th>')
                table_html.append('</tr></thead>')
                # Body
                table_html.append('<tbody>')
                for r in rows[1:]:
                    table_html.append('<tr>')
                    for c_idx, c in enumerate(r):
                        # Formatting
                        c_fmt = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', c)
                        c_fmt = re.sub(r'`([^`]+)`', r'<code>\1</code>', c_fmt)
                        c_fmt = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2" target="_blank">\1</a>', c_fmt)
                        if c_idx == 1 and ('/' in c or 'GET' in c or 'POST' in c):
                            table_html.append(f'<td class="code-col">{c_fmt}</td>')
                        else:
                            table_html.append(f'<td>{c_fmt}</td>')
                    table_html.append('</tr>')
                table_html.append('</tbody></table></div>')
                body_html.append("\n".join(table_html))
            continue

        # Lists (Bullets or numbers)
        if line.startswith('* ') or line.startswith('- ') or re.match(r'^\d+\.\s', line):
            list_items = []
            is_ordered = bool(re.match(r'^\d+\.\s', line))
            tag = 'ol' if is_ordered else 'ul'
            
            while i < len(lines) and (lines[i].startswith('* ') or lines[i].startswith('- ') or re.match(r'^\d+\.\s', lines[i])):
                item_raw = re.sub(r'^(\*|-|\d+\.)\s+', '', lines[i]).strip()
                item_fmt = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', item_raw)
                item_fmt = re.sub(r'`([^`]+)`', r'<code>\1</code>', item_fmt)
                item_fmt = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2" target="_blank">\1</a>', item_fmt)
                list_items.append(f'<li>{item_fmt}</li>')
                i += 1
            
            body_html.append(f'<{tag}>\n' + '\n'.join(list_items) + f'\n</{tag}>')
            continue

        # Normal paragraph
        p_raw = line.strip()
        p_fmt = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', p_raw)
        p_fmt = re.sub(r'`([^`]+)`', r'<code>\1</code>', p_fmt)
        p_fmt = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2" target="_blank">\1</a>', p_fmt)
        body_html.append(f'<p>{p_fmt}</p>')
        i += 1

    content_str = "\n".join(body_html)

    full_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Nymphia — Documentação Técnica & Arquitetura Oficial (v2.3.0)</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --vinho: #5C1A2A;
      --rosa: #C2185B;
      --dourado: #C9A84C;
      --rosa-claro: #FDF0F2;
      --bg-cinza: #F8F9FA;
      --borda: #E5D4D8;
      --texto-primario: #1F2937;
      --texto-secundario: #4B5563;
      --radius: 8px;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      font-family: 'Inter', sans-serif;
      color: var(--texto-primario);
      background-color: #FDFDFE;
      line-height: 1.65;
      padding: 32px 16px;
    }}

    .container {{
      max-width: 960px;
      margin: 0 auto;
      background: #FFFFFF;
      padding: 48px;
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(92, 26, 42, 0.06);
      border: 1px solid var(--borda);
    }}

    .doc-header {{
      border-bottom: 2px solid var(--vinho);
      padding-bottom: 24px;
      margin-bottom: 32px;
    }}

    .doc-logo {{
      display: inline-flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;
    }}

    .doc-logo svg {{
      width: 40px;
      height: 40px;
      fill: var(--vinho);
    }}

    .doc-logo span {{
      font-size: 1.8rem;
      font-weight: 800;
      color: var(--vinho);
      letter-spacing: -0.5px;
    }}

    h1.doc-title {{
      font-size: 1.75rem;
      font-weight: 800;
      color: var(--vinho);
      line-height: 1.25;
      margin-bottom: 8px;
    }}

    .doc-subtitle {{
      font-size: 1.05rem;
      color: var(--rosa);
      font-weight: 500;
      margin-bottom: 16px;
    }}

    .metadata-card {{
      background: var(--rosa-claro);
      border-left: 4px solid var(--rosa);
      padding: 14px 18px;
      border-radius: 6px;
      font-size: 0.9rem;
      color: var(--texto-secundario);
      margin-bottom: 24px;
    }}

    .metadata-card strong {{
      color: var(--vinho);
    }}

    .metadata-card a {{
      color: var(--rosa);
      text-decoration: none;
      word-break: break-all;
    }}

    .metadata-card a:hover {{
      text-decoration: underline;
    }}

    h2 {{
      font-size: 1.35rem;
      font-weight: 700;
      color: var(--vinho);
      margin-top: 36px;
      margin-bottom: 14px;
      padding-bottom: 6px;
      border-bottom: 1px solid var(--borda);
    }}

    h3 {{
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--rosa);
      margin-top: 20px;
      margin-bottom: 8px;
    }}

    p {{
      font-size: 0.95rem;
      color: var(--texto-secundario);
      margin-bottom: 14px;
    }}

    ul, ol {{
      margin-left: 24px;
      margin-bottom: 16px;
      font-size: 0.93rem;
      color: var(--texto-secundario);
    }}

    li {{
      margin-bottom: 6px;
    }}

    hr {{
      border: 0;
      height: 1px;
      background: var(--borda);
      margin: 28px 0;
    }}

    code {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.86rem;
      background: #F3ECEE;
      color: var(--vinho);
      padding: 2px 6px;
      border-radius: 4px;
      font-weight: 600;
    }}

    pre.code-block {{
      background: #23272E;
      color: #E6EDF3;
      padding: 16px 20px;
      border-radius: 8px;
      overflow-x: auto;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.82rem;
      line-height: 1.45;
      margin: 16px 0;
      box-shadow: inset 0 1px 3px rgba(0,0,0,0.3);
    }}

    pre.code-block code {{
      background: transparent;
      color: inherit;
      padding: 0;
      font-weight: 400;
    }}

    .callout {{
      background: #FFF9FA;
      border: 1px solid var(--borda);
      border-left: 4px solid var(--rosa);
      padding: 14px 18px;
      border-radius: 6px;
      margin: 18px 0;
    }}

    .callout .badge {{
      display: inline-block;
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--rosa);
      margin-bottom: 4px;
    }}

    .callout p {{
      margin-bottom: 0;
      font-size: 0.92rem;
      color: var(--vinho);
      font-style: italic;
    }}

    .table-responsive {{
      overflow-x: auto;
      margin: 20px 0;
      border: 1px solid var(--borda);
      border-radius: 8px;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.88rem;
    }}

    th {{
      background: var(--vinho);
      color: #FFFFFF;
      font-weight: 600;
      text-align: left;
      padding: 10px 14px;
      white-space: nowrap;
    }}

    td {{
      padding: 10px 14px;
      border-bottom: 1px solid var(--borda);
      color: var(--texto-secundario);
      vertical-align: top;
    }}

    tr:nth-child(even) {{
      background: #FAF7F8;
    }}

    tr:hover {{
      background: #F5EBEF;
    }}

    td.code-col {{
      font-family: 'JetBrains Mono', monospace;
      color: var(--vinho);
      font-weight: 600;
      font-size: 0.84rem;
    }}

    .action-bar {{
      position: sticky;
      top: 16px;
      background: #FFFFFF;
      padding: 12px 18px;
      border-radius: 30px;
      box-shadow: 0 4px 16px rgba(0,0,0,0.12);
      border: 1px solid var(--borda);
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 24px;
      z-index: 100;
    }}

    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: var(--rosa);
      color: #FFFFFF;
      border: none;
      padding: 8px 16px;
      border-radius: 20px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
      transition: background 0.2s ease;
    }}

    .btn:hover {{
      background: #A0134B;
    }}

    .btn-secondary {{
      background: #F3ECEE;
      color: var(--vinho);
    }}

    .btn-secondary:hover {{
      background: #E8D9DE;
    }}

    .mermaid-wrapper {{
      background: #FFFFFF;
      border: 1px solid var(--borda);
      border-radius: 8px;
      padding: 24px 16px;
      margin: 20px 0;
      overflow-x: auto;
      text-align: center;
      box-shadow: 0 2px 10px rgba(92, 26, 42, 0.04);
    }}

    .mermaid-wrapper .mermaid {{
      display: inline-block;
      text-align: left;
    }}

    @media print {{
      body {{
        padding: 0;
        background: #FFFFFF;
      }}
      .container {{
        border: none;
        box-shadow: none;
        padding: 0;
        max-width: 100%;
      }}
      .action-bar {{
        display: none;
      }}
      h2 {{
        page-break-before: auto;
      }}
      pre.code-block, table, .mermaid-wrapper {{
        page-break-inside: avoid;
      }}
    }}
  </style>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>
    document.addEventListener("DOMContentLoaded", function() {{
      if (window.mermaid) {{
        mermaid.initialize({{
          startOnLoad: true,
          theme: 'base',
          themeVariables: {{
            primaryColor: '#FDF0F2',
            primaryTextColor: '#5C1A2A',
            primaryBorderColor: '#C2185B',
            lineColor: '#C2185B',
            secondaryColor: '#FFF8E7',
            tertiaryColor: '#FFFFFF',
            fontFamily: 'Inter, sans-serif',
            fontSize: '13px'
          }}
        }});
      }}
    }});
  </script>
</head>
<body>
  <div class="container">
    <div class="action-bar">
      <div style="font-weight: 700; color: var(--vinho); font-size: 0.9rem;">
        Plataforma Nymphia v2.3.0
      </div>
      <div style="display: flex; gap: 8px;">
        <button class="btn btn-secondary" onclick="window.print()">🖨️ Imprimir / Salvar em PDF</button>
        <a class="btn" href="DOCUMENTACAO_SISTEMA_NYMPHIA.pdf" download="DOCUMENTACAO_SISTEMA_NYMPHIA.pdf">📥 Baixar PDF Direto</a>
      </div>
    </div>

    <div class="doc-header">
      <div class="doc-logo">
        <svg viewBox="0 0 100 100">
          <path d="M50 15 C45 35 25 45 15 50 C35 55 45 75 50 85 C55 75 75 55 85 50 C75 45 55 35 50 15 Z" fill="#5C1A2A"/>
          <path d="M50 28 C46 40 32 46 25 50 C38 54 46 68 50 72 C54 68 62 54 75 50 C68 46 54 40 50 28 Z" fill="#C2185B"/>
          <circle cx="50" cy="50" r="7" fill="#C9A84C"/>
        </svg>
        <span>Nymphia</span>
      </div>
      <div class="metadata-card">
        <strong>Status:</strong> Produção Cloud Ready (2027 Ready) • <strong>Slogan:</strong> "Cada batimento importa."<br/>
        <strong>Diretrizes Clínicas:</strong> Ministério da Saúde, FEBRASGO, ACOG, CDC e Resolução CFM 2.454/2026<br/>
        <strong>Ambiente em Nuvem:</strong> <a href="https://nymphia-plataforma-ia.onrender.com" target="_blank">https://nymphia-plataforma-ia.onrender.com</a><br/>
        <strong>Repositório GitHub:</strong> <a href="https://github.com/Gabrie-Pokk/Nymphia.git" target="_blank">https://github.com/Gabrie-Pokk/Nymphia.git</a>
      </div>
    </div>

    <div class="doc-content">
      {content_str}
    </div>
  </div>
</body>
</html>"""

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(full_html)

    print(f"Sucesso: HTML gerado com sucesso em: {html_path}")
    print(f"Tamanho do arquivo: {html_path.stat().st_size} bytes")


if __name__ == "__main__":
    generate_html_documentation()
