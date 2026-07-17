#!/usr/bin/env python3
"""Gera dashboard HTML self-contained a partir do store, no design system Avanade.

Uso: python3 dashboard/generate_dashboard.py [--days 30] [--out dashboard.html]
"""
import argparse
import datetime as dt
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "store"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import db  # noqa: E402
from rightsizing import analyze  # noqa: E402

# Sequência térmica oficial Avanade (Solar -> Luminous -> Glow -> Flame -> Thermal -> Aurora)
THERMAL = ["#FFD700", "#FFB414", "#FF5800", "#B43C14", "#C80000", "#890078"]

CSS = """
:root {
  --ava-orange:#FF5800; --ava-dark-orange:#DC4600; --ava-black:#000; --ava-white:#fff;
  --ava-grey-80:#333; --ava-grey-70:#4c4c4c; --ava-grey-60:#666; --ava-grey-50:#7f7f7f;
  --ava-grey-40:#999; --ava-grey-30:#b3b3b3; --ava-grey-20:#ccc; --ava-grey-10:#e5e5e5;
  --ava-solar:#FFD700; --ava-luminous:#FFB414; --ava-glow:#FF5800; --ava-flame:#B43C14;
  --ava-thermal:#C80000; --ava-aurora:#890078;
  --ava-gradient-master: linear-gradient(135deg, #FF5800 0%, #890078 100%);
  --ava-gradient-warm: linear-gradient(135deg, #FFD700 0%, #FF5800 100%);
  --ava-font: 'Segoe UI','Segoe UI Variable',system-ui,-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif;
  --ava-radius-sm:2px; --ava-radius-md:4px; --ava-radius-lg:8px;
  --ava-shadow-md:0 4px 12px rgba(0,0,0,.10),0 2px 4px rgba(0,0,0,.06);
  --ava-shadow-lg:0 8px 24px rgba(0,0,0,.12),0 4px 8px rgba(0,0,0,.08);
}
* { box-sizing:border-box; }
body { margin:0; font-family:var(--ava-font); color:var(--ava-grey-80); background:#fafafa; }
.wrap { max-width:1200px; margin:0 auto; padding:0 32px; }
h1,h2,h3,h4 { margin:0; font-family:var(--ava-font); }

.ava-hero { background:var(--ava-gradient-master); color:#fff; padding:80px 0 64px; position:relative; overflow:hidden; }
.ava-hero::after { content:""; position:absolute; right:-120px; top:-120px; width:460px; height:460px;
  background:radial-gradient(circle, rgba(255,215,0,.45) 0%, rgba(255,215,0,0) 70%); pointer-events:none; }
.ava-hero .kicker { font-size:13px; font-weight:600; letter-spacing:.1em; text-transform:uppercase; opacity:.92; margin-bottom:24px; }
.ava-hero h1 { font-weight:300; font-size:42px; line-height:1.06; max-width:22ch; }
.ava-hero h1 b { font-weight:700; }
.ava-hero .lede { font-weight:300; max-width:60ch; opacity:.95; margin-top:16px; font-size:16px; }
.ava-hero-pills { display:flex; gap:10px; flex-wrap:wrap; margin-top:24px; position:relative; z-index:1; }
.ava-hero-pill { background:rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.3); backdrop-filter:blur(4px);
  border-radius:999px; padding:8px 16px; font-size:13px; font-weight:600; }

.ava-arc { background:#fff; border-top:4px solid var(--ava-orange); box-shadow:var(--ava-shadow-md); position:relative; z-index:2; margin-top:-1px; }
.ava-arc-grid { display:grid; grid-template-columns:repeat(4,1fr); }
.ava-arc-cell { padding:32px 24px; border-right:1px solid var(--ava-grey-10); }
.ava-arc-cell:last-child { border-right:none; }
.ava-arc-big { font-weight:700; font-size:40px; line-height:1; color:var(--ava-dark-orange); letter-spacing:-.02em; }
.ava-arc-big--aurora { color:var(--ava-aurora); }
.ava-arc-label { font-weight:600; font-size:14px; color:var(--ava-grey-80); margin-top:8px; }
.ava-arc-sub { font-size:13px; color:var(--ava-grey-60); margin-top:4px; }

section { padding:48px 0; }
section h2 { font-weight:300; font-size:26px; color:var(--ava-grey-80); margin-bottom:6px; }
.ava-accent-bar { width:64px; height:4px; background:var(--ava-orange); margin-bottom:16px; }
section .subtitle { font-size:14px; color:var(--ava-grey-60); margin-bottom:24px; }

.ava-layer-stack { display:flex; flex-direction:column; gap:16px; }
.ava-layer { background:#fff; border:1px solid var(--ava-grey-10); border-radius:var(--ava-radius-lg);
  box-shadow:var(--ava-shadow-md); overflow:hidden; }
.ava-layer-head { display:grid; grid-template-columns:8px 64px 1fr auto; align-items:center; gap:18px; padding:20px 24px; }
.ava-layer-spine { width:8px; align-self:stretch; border-radius:4px; }
.ava-layer-tier { font-weight:700; font-size:12px; letter-spacing:.04em; text-transform:uppercase; color:var(--ava-grey-50); }
.ava-layer-tier .n { display:block; font-size:28px; line-height:1; color:var(--ava-grey-80); margin-top:2px; }
.ava-layer-title h3 { font-weight:600; font-size:18px; color:var(--ava-grey-80); }
.ava-layer-title .desc { font-size:13.5px; color:var(--ava-grey-60); margin-top:3px; }
.ava-layer-metric { text-align:right; }
.ava-layer-metric b { font-size:20px; color:var(--ava-dark-orange); display:block; }
.ava-layer-metric span { font-size:12px; color:var(--ava-grey-50); }

.ava-stat-block { background:var(--ava-black); color:#fff; border-radius:var(--ava-radius-lg); padding:42px 40px; box-shadow:var(--ava-shadow-lg); }
.ava-stat-block h3 { font-weight:300; font-size:22px; }
.ava-stat-block h3 b { font-weight:700; color:var(--ava-solar); }
.ava-stat-block .sub { color:var(--ava-grey-30); font-size:14px; margin:8px 0 32px; }
.ava-waterfall { display:flex; align-items:flex-end; gap:10px; height:220px; }
.ava-waterfall-bar { flex:1; display:flex; flex-direction:column; justify-content:flex-end; align-items:center; gap:8px; height:100%; }
.ava-waterfall-col { width:100%; border-radius:6px 6px 0 0; }
.ava-waterfall-pct { font-weight:700; font-size:14px; }
.ava-waterfall-cap { font-size:11px; color:var(--ava-grey-30); text-align:center; line-height:1.3; word-break:break-word; }

.ava-card { background:#fff; border-top:4px solid var(--ava-orange); box-shadow:var(--ava-shadow-md); padding:24px; border-radius:var(--ava-radius-sm); }

table { border-collapse:collapse; width:100%; font-size:13.5px; }
th { text-align:left; color:var(--ava-grey-50); font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:.04em;
  padding:10px 14px; border-bottom:2px solid var(--ava-grey-10); }
td { padding:10px 14px; border-bottom:1px solid var(--ava-grey-10); color:var(--ava-grey-80); }
tr:hover td { background:var(--ava-grey-10); }
.tag { display:inline-block; font-size:11px; font-weight:700; letter-spacing:.06em; text-transform:uppercase;
  padding:3px 8px; border-radius:2px; }
.tag--production { background:#00A650; color:#fff; }
.tag--validated { background:var(--ava-info,#0078D4); color:#fff; }
.tag--draft { background:var(--ava-grey-10); color:var(--ava-grey-70); }
.tag--deprecated { background:var(--ava-grey-70); color:#fff; }

.ava-roadmap { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
.ava-roadmap-step { background:#fff; border:1px solid var(--ava-grey-10); border-radius:var(--ava-radius-lg); padding:20px 22px;
  display:flex; gap:16px; box-shadow:var(--ava-shadow-md); }
.ava-roadmap-num { flex:0 0 38px; height:38px; border-radius:50%; background:var(--ava-gradient-warm); color:#fff; font-weight:700;
  display:grid; place-items:center; font-size:16px; }
.ava-roadmap-step h4 { font-weight:600; font-size:15px; color:var(--ava-grey-80); margin-bottom:4px; }
.ava-roadmap-step p { font-size:13px; color:var(--ava-grey-60); margin:0; }

.ava-footer { background:var(--ava-black); color:var(--ava-grey-30); padding:48px 0 40px; margin-top:32px; }
.ava-footer-top { display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap; gap:20px;
  padding-bottom:24px; border-bottom:1px solid var(--ava-grey-70); }
.ava-footer-wordmark { color:#fff; font-weight:700; font-size:22px; }
.ava-footer-wordmark span { color:var(--ava-orange); }
.ava-footer-tagline { font-weight:700; font-size:22px; color:var(--ava-orange); }
.ava-footer-notes { font-size:11.5px; color:var(--ava-grey-40); margin-top:24px; line-height:1.7; }
"""

LAYER_INFO = {
    "ast": ("01", "Navegação estrutural (AST)", "code-nav / safe-refactor — ast-grep/tree-sitter, lê menos texto antes de tudo", THERMAL[0]),
    "headroom": ("02", "Compressão de contexto", "compress (Headroom) — comprime 60–95% do que sobra antes do modelo", THERMAL[2]),
    "rightsizing": ("03", "Rightsizing de modelo", "modelo certo por tarefa, caching e Batch API", THERMAL[5]),
}


def q(conn, sql, params):
    return conn.execute(sql, params).fetchall()


def esc(v) -> str:
    return html.escape(str(v))


def table(headers, rows, fmt=None, status_col=None):
    h = "".join(f"<th>{esc(x)}</th>" for x in headers)
    body = ""
    for r in rows:
        cells = []
        for i, v in enumerate(r):
            val = (fmt or (lambda i, v: v))(i, v)
            if status_col is not None and i == status_col:
                cells.append(f'<td><span class="tag tag--{esc(v)}">{esc(v)}</span></td>')
            else:
                cells.append(f"<td>{esc(val)}</td>")
        body += f"<tr>{''.join(cells)}</tr>"
    return f"<table><tr>{h}</tr>{body or f'<tr><td colspan={len(headers)}>sem dados</td></tr>'}</table>"


def money(i, v):
    return f"US$ {v:,.2f}" if isinstance(v, float) else (f"{v:,}" if isinstance(v, int) else v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--out", default=str(Path(__file__).parent / "dashboard.html"))
    args = ap.parse_args()
    conn = db.connect()
    since = [f"-{args.days} days"]

    by_project = q(conn, "SELECT project, SUM(cost_usd), SUM(input_tokens+output_tokens) FROM usage WHERE ts>=datetime('now',?) GROUP BY project ORDER BY 2 DESC LIMIT 15", since)
    by_model = q(conn, "SELECT model, SUM(cost_usd) FROM usage WHERE ts>=datetime('now',?) GROUP BY model ORDER BY 2 DESC", since)
    by_day = q(conn, "SELECT date(ts), SUM(cost_usd) FROM usage WHERE ts>=datetime('now',?) GROUP BY 1 ORDER BY 1", since)
    savings = q(conn, "SELECT source, SUM(tokens_saved), SUM(usd_saved) FROM savings WHERE ts>=datetime('now',?) GROUP BY source", since)
    registry = q(conn, "SELECT name, project, model, status, owner FROM agent_registry ORDER BY updated_at DESC", [])
    recs = analyze(conn, args.days)[:4]
    conn.close()

    total = sum(r[1] or 0 for r in by_project)
    saved_usd = sum(r[2] or 0 for r in savings)
    saved_tokens = sum(r[1] or 0 for r in savings)

    # ---- Hero ----
    now = dt.datetime.now().strftime("%d/%m/%Y")
    hero = f"""
<div class="ava-hero"><div class="wrap">
  <div class="kicker">RELATÓRIO GERADO EM {now} · ÚLTIMOS {args.days} DIAS</div>
  <h1>Quanto seus <b>agentes de IA</b> realmente custam — e o que já foi economizado</h1>
  <p class="lede">Custo real (tokens de verdade, não estimativa), economia por camada de otimização e o inventário de agentes com seu lifecycle de qualidade.</p>
  <div class="ava-hero-pills">
    <div class="ava-hero-pill">{len(by_project)} projetos ativos</div>
    <div class="ava-hero-pill">{len(registry)} agentes no registry</div>
    <div class="ava-hero-pill">{len(by_model)} modelos em uso</div>
  </div>
</div></div>"""

    # ---- Arc de KPIs ----
    arc = f"""
<div class="ava-arc"><div class="wrap"><div class="ava-arc-grid">
  <div class="ava-arc-cell"><div class="ava-arc-big">US$ {total:,.2f}</div><div class="ava-arc-label">Custo total</div><div class="ava-arc-sub">últimos {args.days} dias</div></div>
  <div class="ava-arc-cell"><div class="ava-arc-big ava-arc-big--aurora">US$ {saved_usd:,.2f}</div><div class="ava-arc-label">Economia registrada</div><div class="ava-arc-sub">{saved_tokens:,.0f} tokens poupados</div></div>
  <div class="ava-arc-cell"><div class="ava-arc-big">{len(by_project)}</div><div class="ava-arc-label">Projetos ativos</div><div class="ava-arc-sub">com telemetria no período</div></div>
  <div class="ava-arc-cell"><div class="ava-arc-big">{len(registry)}</div><div class="ava-arc-label">Agentes no registry</div><div class="ava-arc-sub">Agent OPS lifecycle</div></div>
</div></div></div>"""

    # ---- Layer stack: economia por camada ----
    sav_by_source = {s[0]: (s[1] or 0, s[2] or 0) for s in savings}
    layers_html = ""
    for key, (num, title, desc, color) in LAYER_INFO.items():
        tk, usd = sav_by_source.get(key, (0, 0.0))
        layers_html += f"""
    <div class="ava-layer">
      <div class="ava-layer-head">
        <div class="ava-layer-spine" style="background:{color}"></div>
        <div class="ava-layer-tier">CAMADA<span class="n">{num}</span></div>
        <div class="ava-layer-title"><h3>{esc(title)}</h3><div class="desc">{esc(desc)}</div></div>
        <div class="ava-layer-metric"><b>US$ {usd:,.2f}</b><span>{tk:,.0f} tokens</span></div>
      </div>
    </div>"""
    layers = f"""
<section><div class="wrap">
  <div class="ava-accent-bar"></div>
  <h2>Economia por camada</h2>
  <p class="subtitle">Sequência oficial de otimização — da leitura estrutural até o rightsizing de modelo.</p>
  <div class="ava-layer-stack">{layers_html}</div>
</div></section>"""

    # ---- Stat block dark: custo por modelo (waterfall) ----
    top_models = by_model[:6] or [("sem dados", 0.0)]
    max_usd = max((m[1] or 0) for m in top_models) or 1
    bars = ""
    for i, (model, usd) in enumerate(top_models):
        h_pct = max(6, round((usd or 0) / max_usd * 100))
        color = THERMAL[min(i, len(THERMAL) - 1)]
        bars += f"""
      <div class="ava-waterfall-bar">
        <div class="ava-waterfall-pct" style="color:{color}">US$ {usd:,.0f}</div>
        <div class="ava-waterfall-col" style="height:{h_pct}%;background:{color}"></div>
        <div class="ava-waterfall-cap">{esc(model)}</div>
      </div>"""
    statblock = f"""
<section><div class="wrap">
  <div class="ava-stat-block">
    <h3>Custo total de <b>US$ {total:,.2f}</b> decomposto por modelo</h3>
    <div class="sub">Barras na sequência térmica — do maior (Solar) ao menor gasto (Aurora)</div>
    <div class="ava-waterfall">{bars}</div>
  </div>
</div></section>"""

    # ---- Custo por dia (line chart) ----
    days_labels = json.dumps([r[0] for r in by_day])
    days_values = json.dumps([round(r[1] or 0, 2) for r in by_day])
    daychart = f"""
<section><div class="wrap">
  <div class="ava-accent-bar"></div>
  <h2>Custo por dia</h2>
  <div class="ava-card"><canvas id="c" width="1100" height="220" style="width:100%;height:220px"></canvas></div>
</div></section>"""

    # ---- Tabelas ----
    tables = f"""
<section><div class="wrap">
  <div class="ava-accent-bar"></div>
  <h2>Por projeto</h2>
  {table(["projeto", "custo", "tokens"], by_project, money)}
</div></section>
<section style="padding-top:0"><div class="wrap">
  <div class="ava-accent-bar"></div>
  <h2>Por modelo</h2>
  {table(["modelo", "custo"], by_model, money)}
</div></section>"""

    # ---- Roadmap: recomendações de rightsizing ----
    roadmap_html = ""
    for i, r in enumerate(recs, 1):
        primary_tag = r["tags"][0] if r["tags"] else ""
        roadmap_html += f"""
    <div class="ava-roadmap-step">
      <div class="ava-roadmap-num">{i}</div>
      <div><h4>{esc(r['project'])} · {esc(r['model'])} — US$ {r['usd']:,.2f}</h4><p>{esc(primary_tag)}</p></div>
    </div>"""
    roadmap = f"""
<section><div class="wrap">
  <div class="ava-accent-bar"></div>
  <h2>Plano de ação — rightsizing</h2>
  <p class="subtitle">Top oportunidades de otimização detectadas na telemetria (skill <code>rightsizing</code>).</p>
  <div class="ava-roadmap">{roadmap_html or '<p class="subtitle">Nenhuma recomendação relevante no período.</p>'}</div>
</div></section>""" if recs else ""

    # ---- Registry ----
    registry_html = f"""
<section><div class="wrap">
  <div class="ava-accent-bar"></div>
  <h2>Agent Registry</h2>
  <p class="subtitle">Lifecycle Agent OPS: draft → validated → production → deprecated.</p>
  {table(["agente", "projeto", "modelo", "status", "owner"], registry, status_col=3)}
</div></section>"""

    # ---- Footer ----
    footer = f"""
<div class="ava-footer"><div class="wrap">
  <div class="ava-footer-top">
    <div><div class="ava-footer-wordmark">agent-finops<span>.</span></div>
      <div style="font-size:12px;color:var(--ava-grey-40);margin-top:4px;letter-spacing:.04em">AGENT OPS + FINOPS PARA AGENTES DE IA</div></div>
    <div class="ava-footer-tagline">Measure what runs.</div>
  </div>
  <div class="ava-footer-notes">Gerado em {now} a partir de <b>~/.agent-finops/telemetry.db</b> — dados 100% locais, tokens reais extraídos dos transcripts.<br>
  Preços conforme <b>store/pricing.json</b>. Nenhum dado sai da máquina.</div>
</div></div>"""

    page = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>agent-finops · Dashboard</title><style>{CSS}</style></head><body>
{hero}{arc}{layers}{statblock}{daychart}{tables}{roadmap}{registry_html}{footer}
<script>
const L={days_labels},V={days_values},c=document.getElementById('c').getContext('2d');
const W=1100,H=220,m=Math.max(...V,1);
c.clearRect(0,0,W,H);
c.strokeStyle='#FF5800';c.lineWidth=2;c.beginPath();
V.forEach((v,i)=>{{const x=30+i*(W-60)/Math.max(V.length-1,1),y=H-24-(v/m)*(H-54);
i?c.lineTo(x,y):c.moveTo(x,y);}});c.stroke();
c.fillStyle='#FF5800';
V.forEach((v,i)=>{{const x=30+i*(W-60)/Math.max(V.length-1,1),y=H-24-(v/m)*(H-54);
c.beginPath();c.arc(x,y,3,0,7);c.fill();}});
c.font='11px Segoe UI, sans-serif';c.fillStyle='#7f7f7f';
L.forEach((l,i)=>{{if(i%Math.ceil(L.length/10)===0)c.fillText(l.slice(5),25+i*(W-60)/Math.max(L.length-1,1),H-4)}});
</script></body></html>"""
    Path(args.out).write_text(page)
    print(f"Dashboard gerado: {args.out}")


if __name__ == "__main__":
    main()
