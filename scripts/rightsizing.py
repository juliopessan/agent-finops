#!/usr/bin/env python3
"""Analisa a telemetria e emite recomendações de otimização de custo."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "store"))
import db  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    args = ap.parse_args()
    conn = db.connect()
    since = f"-{args.days} days"

    rows = conn.execute(
        """SELECT project, model, SUM(input_tokens), SUM(output_tokens),
                  SUM(cache_read_tokens), SUM(cost_usd), COUNT(*)
           FROM usage WHERE ts >= datetime('now', ?)
           GROUP BY project, model HAVING SUM(cost_usd) > 0.5
           ORDER BY SUM(cost_usd) DESC""",
        [since],
    ).fetchall()

    print(f"\n== Rightsizing · últimos {args.days} dias ==\n")
    recs = 0
    for proj, model, inp, out, cread, usd, n in rows:
        model = model or "?"
        avg_out = (out or 0) / max(n, 1)
        cache_ratio = (cread or 0) / max((inp or 0) + (cread or 0), 1)
        tags = []
        if ("opus" in model or "fable" in model) and avg_out < 300:
            tags.append("DOWNGRADE? outputs curtos — testar sonnet-5/haiku-4-5 com agent-gate")
        if cache_ratio < 0.5 and (inp or 0) > 100_000:
            tags.append(f"CACHE baixo ({cache_ratio:.0%}) — verificar invalidadores de prefixo")
        if usd > 20:
            tags.append("VOLUME alto — avaliar Batch API (-50%) e compressão Headroom")
        if tags:
            recs += 1
            print(f"[{proj} · {model}]  US$ {usd:.2f}  ({n} msgs, avg_out={avg_out:.0f} tok, cache={cache_ratio:.0%})")
            for t in tags:
                print(f"   -> {t}")
            print()
    if not recs:
        print("Nenhuma recomendação relevante — perfil de uso saudável ou dados insuficientes.")
    conn.close()


if __name__ == "__main__":
    main()
