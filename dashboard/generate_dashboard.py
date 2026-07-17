#!/usr/bin/env python3
"""Gera dashboard HTML self-contained a partir do store.

Uso: python3 dashboard/generate_dashboard.py [--days 30] [--out dashboard.html]
"""
import argparse
import datetime
import html
import json
import sys
from pathlib import Path
from string import Template

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "store"))
import db  # noqa: E402


def q(conn, sql, params):
    return conn.execute(sql, params).fetchall()


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
    total = sum(r[1] or 0 for r in by_project)
    saved = sum(r[2] or 0 for r in savings)
    conn.close()

    def table(headers, rows, fmt=None):
        h = "".join(f"<th>{x}</th>" for x in headers)
        body = ""
        for r in rows:
            cells = "".join(f"<td>{html.escape(str((fmt or (lambda i, v: v))(i, v)))}</td>" for i, v in enumerate(r))
            body += f"<tr>{cells}</tr>"
        thead = f"<thead><tr>{h}</tr></thead>" if h else ""
        tbod = f"<tbody>{body or '<tr><td colspan=99>sem dados</td></tr>'}</tbody>"
        return f"<table>{thead}{tbod}</table>"

    money = lambda i, v: f"US$ {v:.2f}" if isinstance(v, float) else (f"{v:,}" if isinstance(v, int) else v)
    days_labels = json.dumps([r[0] for r in by_day])
    days_values = json.dumps([round(r[1] or 0, 2) for r in by_day])

    page = Template("""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>agent-finops · FinOps Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  :root{--ink:#12100E;--paper:#FAF8F4;--graphite:#3A3733;--smoke:#8A857D;--line:#E4E0D8;--ember:#FF5800;--ember-deep:#C43E00;--card:#FFFFFF;--success:#00A650;--info:#0078D4;--mono:'JetBrains Mono',monospace;--display:'Space Grotesk',sans-serif;--body:'Inter',sans-serif}
  *{margin:0;padding:0;box-sizing:border-box} html{scroll-behavior:smooth} body{background:var(--paper);color:var(--ink);font-family:var(--body);font-size:15.5px;line-height:1.65}
  .hero{background:var(--ink);color:var(--paper);padding:72px 40px 54px;margin-bottom:56px;position:relative;overflow:hidden}
  .hero::after{content:'';position:absolute;left:0;right:0;bottom:0;height:4px;background:linear-gradient(90deg,var(--ember),var(--ember-deep))}
  .hero-inner{max-width:1040px;margin:0 auto}
  .hero-eyebrow{font-family:var(--mono);font-weight:500;font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:var(--ember);margin-bottom:16px;display:flex;align-items:center;gap:10px}
  .hero-eyebrow .dot{width:7px;height:7px;border-radius:50%;background:var(--ember)}
  .hero h1{font-family:var(--display);font-weight:700;font-size:clamp(2.1rem,4.4vw,3.1rem);line-height:1.08;letter-spacing:-.02em;margin:0 0 14px}
  .hero-sub{font-family:var(--body);font-weight:400;font-size:1.15rem;max-width:740px;margin:0 0 30px;color:#D8D2C6}
  .hero-meta{display:flex;flex-wrap:wrap;gap:30px;font-family:var(--mono);font-size:.78rem;border-top:1px solid rgba(255,255,255,.15);padding-top:20px}
  .hero-meta span{color:var(--ember);display:block;font-weight:500;font-size:.66rem;text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px}
  .hero-meta div{color:#D8D2C6}
  .page{max-width:1040px;margin:0 auto;padding:0 40px 80px}
  section{margin-bottom:60px}
  .section-label{font-family:var(--mono);font-weight:500;font-size:.7rem;letter-spacing:.12em;text-transform:uppercase;color:var(--ember-deep);margin-bottom:6px}
  .section-bar{height:3px;width:56px;background:var(--ember);margin-bottom:16px}
  h2{font-family:var(--display);font-weight:700;font-size:1.9rem;letter-spacing:-.01em;color:var(--ink);margin:0 0 8px}
  .stat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:20px 0 28px}
  .stat-tile{border:1px solid var(--line);background:var(--card);border-radius:4px;padding:18px 16px;text-align:left}
  .stat-tile .stat-value{font-family:var(--display);font-size:1.9rem;font-weight:700;color:var(--ember-deep);line-height:1.1;margin-bottom:4px}
  .stat-tile .stat-label{font-family:var(--mono);font-size:.66rem;color:var(--smoke);text-transform:uppercase;letter-spacing:.05em;font-weight:500}
  table{width:100%;border-collapse:collapse;margin:12px 0 24px;font-size:.86rem;border:1px solid var(--line);border-radius:4px;overflow:hidden}
  thead{background:var(--ink)}
  th{color:var(--paper);text-align:left;padding:12px 16px;font-family:var(--mono);font-weight:600;font-size:.7rem;text-transform:uppercase;letter-spacing:.06em}
  tbody tr{border-bottom:1px solid var(--line)}
  tbody tr:last-child{border-bottom:none}
  td{padding:12px 16px;color:var(--graphite);font-size:.88rem}
  tbody tr:nth-child(even) td{background:rgba(58,55,51,.02)}
  .chart{background:var(--card);border:1px solid var(--line);border-radius:4px;padding:20px;margin-top:12px;min-height:280px;display:flex;align-items:center;justify-content:center}
  .chart canvas{width:100%;height:auto;min-height:240px;display:block}
  footer{background:var(--ink);color:var(--paper);padding:48px 40px 32px;position:relative;margin-top:40px}
  footer::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,var(--ember),var(--ember-deep))}
  .footer-inner{max-width:1040px;margin:0 auto;display:flex;justify-content:space-between;flex-wrap:wrap;gap:20px}
  .footer-wordmark{font-family:var(--display);font-weight:700;font-size:1.8rem;letter-spacing:-.02em}
  .footer-wordmark em{color:var(--ember);font-style:normal;margin:0 4px}
  @media (max-width:820px){.stat-grid{grid-template-columns:repeat(2,1fr)}}
</style>
</head>
<body>
<div class="hero">
  <div class="hero-inner">
    <div class="hero-eyebrow"><span class="dot"></span>agent-finops · telemetry local</div>
    <h1>FinOps Dashboard</h1>
    <p class="hero-sub">Painel com custo real de IA, volume de tokens e registry de agentes capturados no SQLite local.</p>
    <div class="hero-meta">
      <div><span>Período</span>Últimos $days dias</div>
      <div><span>Fonte</span>SQLite local</div>
      <div><span>Projeto</span>agent-finops</div>
      <div><span>Status</span>Dados ingeridos</div>
    </div>
  </div>
</div>
<div class="page">
  <section>
    <div class="section-label">Visão executiva</div>
    <div class="section-bar"></div>
    <h2>Resumo</h2>
    <div class="stat-grid">
      <div class="stat-tile"><div class="stat-value">US$$ $total</div><div class="stat-label">custo total</div></div>
      <div class="stat-tile"><div class="stat-value">US$$ $saved</div><div class="stat-label">economia registrada</div></div>
      <div class="stat-tile"><div class="stat-value">$len_by_project</div><div class="stat-label">projetos ativos</div></div>
      <div class="stat-tile"><div class="stat-value">$len_registry</div><div class="stat-label">agentes no registry</div></div>
    </div>
  </section>

  <section>
    <div class="section-label">Consumo</div>
    <div class="section-bar"></div>
    <h2>Custo por dia</h2>
    <div class="chart"><canvas id="c"></canvas></div>
    <h2 style="margin-top:24px">Por projeto</h2>
    $table_project
    <h2 style="margin-top:24px">Por modelo</h2>
    $table_model
  </section>

  <section>
    <div class="section-label">Economia</div>
    <div class="section-bar"></div>
    <h2>Economia por camada</h2>
    $table_savings
  </section>

  <section>
    <div class="section-label">Governança</div>
    <div class="section-bar"></div>
    <h2>Agent Registry</h2>
    $table_registry
  </section>
</div>
<footer>
  <div class="footer-inner">
    <div class="footer-wordmark">agent<em>.</em>finops</div>
    <div style="font-family:var(--mono);font-size:.76rem;color:#8A857D">Gerado localmente em $today</div>
  </div>
</footer>
<script>
const L=$days_labels,V=$days_values;
const canvas=document.getElementById('c');
if(canvas&&L.length>0&&V.length>0){
  const rect=canvas.parentElement.getBoundingClientRect();
  canvas.width=Math.max(rect.width-32,600);
  canvas.height=220;
  const c=canvas.getContext('2d');
  const W=canvas.width,H=canvas.height,m=Math.max(...V,1);
  c.strokeStyle='#FF5800';c.lineWidth=2.5;c.beginPath();
  V.forEach((v,i)=>{const x=40+i*(W-80)/Math.max(V.length-1,1),y=H-40-(v/m)*(H-80);i?c.lineTo(x,y):c.moveTo(x,y);});
  c.stroke();
  c.fillStyle='#FF5800';c.font='11px sans-serif';c.textAlign='center';c.fillStyle='#8A857D';
  L.forEach((l,i)=>{if(i%Math.ceil(L.length/8)===0)c.fillText(l.slice(5),40+i*(W-80)/Math.max(L.length-1,1),H-10);});
}
</script>
</body>
</html>""")
    page = page.substitute(
        days=args.days,
        total=f"{total:.2f}",
        saved=f"{saved:.2f}",
        len_by_project=len(by_project),
        len_registry=len(registry),
        table_project=table(["projeto", "custo", "tokens"], by_project, money),
        table_model=table(["modelo", "custo"], by_model, money),
        table_savings=table(["camada", "tokens poupados", "USD"], savings, money),
        table_registry=table(["agente", "projeto", "modelo", "status", "owner"], registry),
        days_labels=days_labels,
        days_values=days_values,
        today=datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
    )
    Path(args.out).write_text(page, encoding='utf-8')
    print(f"Dashboard gerado: {args.out}")


if __name__ == "__main__":
    main()
