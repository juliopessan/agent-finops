#!/usr/bin/env python3
"""Gera dashboard HTML self-contained a partir do store.

Uso: python3 dashboard/generate_dashboard.py [--days 30] [--out dashboard.html]
"""
import argparse
import html
import json
import sys
from pathlib import Path

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
        return f"<table><tr>{h}</tr>{body or '<tr><td colspan=99>sem dados</td></tr>'}</table>"

    money = lambda i, v: f"US$ {v:.2f}" if isinstance(v, float) else (f"{v:,}" if isinstance(v, int) else v)
    days_labels = json.dumps([r[0] for r in by_day])
    days_values = json.dumps([round(r[1] or 0, 2) for r in by_day])

    page = f"""<!doctype html><html><head><meta charset="utf-8"><title>agent-finops</title>
<style>
body{{font-family:-apple-system,sans-serif;margin:2rem;background:#0f1117;color:#e6e6e6}}
h1{{color:#7dd3fc}} h2{{color:#a5b4fc;margin-top:2rem}}
.cards{{display:flex;gap:1rem}} .card{{background:#1a1d27;padding:1rem 1.5rem;border-radius:10px}}
.card b{{font-size:1.6rem;color:#7dd3fc;display:block}}
table{{border-collapse:collapse;margin-top:.5rem;width:100%}}
td,th{{border-bottom:1px solid #2a2e3d;padding:.4rem .8rem;text-align:left;font-size:.9rem}}
th{{color:#a5b4fc}} #chart{{background:#1a1d27;border-radius:10px;padding:1rem;margin-top:.5rem}}
</style></head><body>
<h1>agent-finops · últimos {args.days} dias</h1>
<div class="cards">
  <div class="card"><b>US$ {total:.2f}</b>custo total</div>
  <div class="card"><b>US$ {saved:.2f}</b>economia registrada</div>
  <div class="card"><b>{len(by_project)}</b>projetos ativos</div>
  <div class="card"><b>{len(registry)}</b>agentes no registry</div>
</div>
<h2>Custo por dia</h2><div id="chart"><canvas id="c" width="1100" height="220"></canvas></div>
<h2>Por projeto</h2>{table(["projeto", "custo", "tokens"], by_project, money)}
<h2>Por modelo</h2>{table(["modelo", "custo"], by_model, money)}
<h2>Economia por camada</h2>{table(["camada", "tokens poupados", "USD"], savings, money)}
<h2>Agent Registry</h2>{table(["agente", "projeto", "modelo", "status", "owner"], registry)}
<script>
const L={days_labels},V={days_values},c=document.getElementById('c').getContext('2d');
const W=1100,H=220,m=Math.max(...V,1);c.strokeStyle='#7dd3fc';c.fillStyle='#7dd3fc';c.beginPath();
V.forEach((v,i)=>{{const x=30+i*(W-60)/Math.max(V.length-1,1),y=H-20-(v/m)*(H-50);
i?c.lineTo(x,y):c.moveTo(x,y);}});c.stroke();
c.font='10px sans-serif';c.fillStyle='#888';
L.forEach((l,i)=>{{if(i%Math.ceil(L.length/10)===0)c.fillText(l.slice(5),25+i*(W-60)/Math.max(L.length-1,1),H-5)}});
</script></body></html>"""
    Path(args.out).write_text(page)
    print(f"Dashboard gerado: {args.out}")


if __name__ == "__main__":
    main()
