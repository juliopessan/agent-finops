# agent-finops

Sistema de **Agent OPS + FinOps** para projetos com agentes IA, empacotado como plugin do Claude Code (anatomia inspirada no [microsoft/hve-core](https://github.com/microsoft/hve-core)).

```
agent-finops/
├── hooks/           → telemetria: cada tool call vira evento (PostToolUse)
├── store/           → SQLite central (~/.agent-finops/telemetry.db) + ingest de transcripts + pricing
├── skills/
│   ├── cost-report      → FinOps: custo × projeto × modelo × período
│   ├── rightsizing      → recomendações de modelo/caching/batch
│   ├── compress         → Headroom (wrap/proxy/MCP) + registro de economia
│   ├── code-nav         → AST: busca estrutural (ast-grep/tree-sitter)
│   ├── safe-refactor    → AST: refatoração estrutural multi-arquivo
│   └── agent-gate       → validação sintática pós-geração + lifecycle do registry
├── agents/          → cost-analyst, budget-guardian, agent-auditor
├── dashboard/       → gerador de dashboard HTML self-contained
└── evals/           → gates de qualidade (padrão hve-core)
```

## Instalação (plugin local)

```bash
claude plugin install /caminho/para/agent-finops
# ou adicionar via marketplace local / --plugin-dir
```

O hook de telemetria passa a registrar tool calls automaticamente. Os dados de tokens **reais** vêm do ingest de transcripts.

## Uso rápido

```bash
python3 store/ingest_transcripts.py                 # coleta usage real dos transcripts
python3 scripts/cost_report.py --days 30 --by model # relatório
python3 scripts/rightsizing.py                      # recomendações de economia
python3 scripts/gate.py src/*.py                    # gate sintático
python3 dashboard/generate_dashboard.py             # dashboard HTML
```

Ou pelas skills no Claude Code: `/cost-report`, `/rightsizing`, `/compress`, `/code-nav`, `/safe-refactor`, `/agent-gate`.

## Camadas de economia (ordem de aplicação)

1. **code-nav (AST)** — lê menos (busca estrutural em vez de arquivos inteiros)
2. **compress (Headroom)** — comprime o que sobra (60–95% menos tokens)
3. **rightsizing** — modelo certo p/ tarefa certa (Opus→Sonnet→Haiku), caching, batch
4. Tudo medido no store e visível no `cost-report`/dashboard (tabela `savings`).

## Agent OPS

- **Registry** de agentes com lifecycle `draft → validated → production → deprecated`
- **agent-gate**: sintaxe (AST) → testes → arch-review → promoção
- **agent-auditor**: inventário e conformidade dos agentes dos projetos
