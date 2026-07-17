# agent-finops

> O painel de controle que faltava para quem tem agentes de IA espalhados por vários projetos.

## A história

Em algum momento você percebeu: tem agentes de IA rodando em quase todo projeto seu — chatbot no WhatsApp, review de arquitetura, migração de dados, SDK de requirements. Cada um com seu próprio agente, seu próprio modelo, sua própria fatura silenciosa somando no fim do mês.

O problema não é *ter* agentes. É não saber **quanto cada um custa, se está usando o modelo certo, e se o que ele produz é confiável o suficiente para ir pra produção**. Sem essa visibilidade, toda decisão vira palpite: "acho que o Orion está caro", "acho que aquele agente do migrateiq tá bom pra produção". Achismo não escala.

Rodamos o primeiro diagnóstico neste próprio ecossistema e o retrato apareceu na hora: **US$ 291,61 gastos em 30 dias**, espalhados por 6 modelos diferentes, com o Fable 5 sozinho respondendo por **US$ 94** — maior custo, mas não necessariamente o culpado, porque volume de mensagens (não o modelo) é que dominava a conta. Ao mesmo tempo, um inventário automático descobriu **32 agentes** perdidos entre 8 projetos, nenhum deles com um processo formal de "isso está pronto pra produção".

`agent-finops` nasceu para resolver isso: **medir o custo real de cada agente e garantir que o código que ele produz é confiável antes de virar produção** — as duas faces da mesma moeda, FinOps (quanto custa) e Agent OPS (o que garante qualidade).

## O que é

Um plugin do Claude Code — instalável em qualquer máquina, ativo em qualquer projeto — construído sobre a mesma anatomia usada pelo [hve-core](https://github.com/microsoft/hve-core) da Microsoft: skills, agentes especializados, hooks e um store central. A diferença é o que ele observa: não o código que você escreve, mas o **comportamento e o custo dos agentes que escrevem código por você**.

Por baixo do capô é simples de propósito: um hook captura cada chamada de ferramenta, um script real lê os transcripts do Claude Code e extrai o consumo de tokens que de fato aconteceu (não estimativa — o `usage` que a API retornou), e tudo cai num SQLite local (`~/.agent-finops/telemetry.db`). Nada sai da sua máquina.

## O que faz

**Enxerga o gasto.** `cost-report` cruza custo por projeto, por modelo, por dia — com os preços atuais direto da tabela oficial. `rightsizing` lê esse histórico e aponta, com números, onde um Opus está rodando uma tarefa de Haiku, onde o cache de prompt não está pegando, onde o volume já justifica a Batch API (-50%).

**Reduz o gasto, não só relata.** Duas camadas de economia real, medidas e registradas:
- `code-nav` e `safe-refactor` usam AST (ast-grep/tree-sitter) para o agente *ler menos* — busca estrutural em vez de abrir arquivos inteiros;
- `compress` conecta o [Headroom](https://github.com/chopratejas/headroom), que comprime 60–95% do que sobra antes de chegar ao modelo.

**Garante qualidade antes de ir pra produção.** `agent-gate` é o portão: valida sintaticamente o código gerado (parse AST — falha rápido, sem custar uma rodada de testes), roda a suíte do projeto, e para mudanças arquiteturais relevantes, aciona o squad do [arch-review-assistant](https://github.com/juliopessan/arch-review-assistant) como terceiro gate. Só depois disso um agente sobe de status.

**Sabe quem são seus agentes.** `sync_registry` varre seus projetos e popula um registro central com lifecycle explícito — `draft → validated → production → deprecated`. Nada de agente fantasma rodando sem dono.

**Mostra o quadro completo.** Um dashboard HTML autocontido (sem servidor, sem dependência externa) reúne custo, economia por camada e o registro de agentes numa página só.

## O que resolve

| Antes | Depois |
|---|---|
| "Acho que esse projeto está caro" | US$ exato por projeto, modelo e dia |
| Modelo escolhido por hábito | Recomendação de rightsizing baseada em uso real |
| Agente promovido a produção "porque funcionou uma vez" | Gate de 3 camadas: sintaxe → testes → review arquitetural |
| 32 agentes espalhados, ninguém sabe o inventário completo | Registry único, com status e dono |
| Token gasto lendo arquivos inteiros | Busca estrutural via AST + compressão Headroom |

## Anatomia

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

## Instalação

```bash
claude plugin marketplace add /caminho/para/agent-finops
claude plugin install agent-finops@agent-finops-marketplace
```

A partir daí o hook de telemetria registra tool calls automaticamente. Os dados de tokens **reais** vêm do ingest de transcripts — não estimativa.

Dependências opcionais das camadas de economia:
```bash
brew install ast-grep       # code-nav, safe-refactor
pipx install headroom-ai    # compress
```

## Uso rápido

```bash
python3 store/ingest_transcripts.py                 # coleta usage real dos transcripts
python3 scripts/cost_report.py --days 30 --by model # relatório
python3 scripts/rightsizing.py                      # recomendações de economia
python3 scripts/gate.py src/*.py                    # gate sintático
python3 scripts/sync_registry.py <raiz> --owner eu  # inventário de agentes
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
