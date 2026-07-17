# agent-finops

### Você sabe quanto seus agentes de IA custam este mês? Nem eu sabia.

Rodei o diagnóstico no meu próprio ecossistema de projetos e o número que voltou foi **US$ 291,61 em 30 dias**, escondido atrás de 6 modelos diferentes, sem nenhum aviso, sem nenhum dashboard — só uma pilha de sessões que ninguém tinha somado. E os agentes que geraram esse gasto? **32 deles**, espalhados por 8 projetos, e nenhum passava por um processo formal antes de ir pra produção.

---

Se isso soa familiar, não é coincidência. É o estágio natural de qualquer time que adotou IA rápido demais pra parar e organizar a casa: cada projeto ganha seu agente, cada agente ganha seu modelo, e ninguém mais sabe responder duas perguntas simples — **quanto isso custa** e **isso está pronto pra rodar sem supervisão**? Achismo não escala, e "acho que está caro" não é uma métrica.

---

`agent-finops` é o painel de controle que faltava: um plugin que **mede o custo real de cada agente** (tokens de verdade, não estimativa) e **garante que o código que ele produz passou por um portão de qualidade** antes de virar produção — as duas faces da mesma moeda, FinOps (quanto custa) e Agent OPS (o que garante confiança). Ele não substitui seus agentes; ele te dá o instrumento de painel que estava faltando no cockpit.

Por baixo do capô é simples de propósito: um hook captura cada chamada de ferramenta, um script lê os transcripts locais e extrai o consumo de tokens que de fato aconteceu — o `usage` que a API retornou, não uma conta de padaria —, e tudo cai num SQLite local. Nada sai da sua máquina; o painel é seu.

O que ele resolve, na prática:

- **Enxerga o gasto** — custo por projeto, por modelo, por dia, com recomendação de onde um modelo caro está rodando uma tarefa barata.
- **Reduz o gasto** — busca estrutural via AST (Abstract Syntax Tree, ou Árvore de Sintaxe Abstrata) em vez de ler arquivos inteiros, mais compressão de contexto, medidas e registradas.
- **Garante qualidade antes de produção** — sintaxe → testes → review arquitetural, um portão de verdade, não um "funcionou uma vez".
- **Sabe quem são seus agentes** — inventário automático com lifecycle explícito, sem agente fantasma sem dono.

**Instale agora e rode seu primeiro diagnóstico** — em 5 minutos você sabe exatamente quanto seus agentes estão custando este mês (veja *Instalação* abaixo). O resto deste README é o mapa técnico completo: anatomia, skills, e como cada camada funciona.

## O que é

Um plugin do Claude Code — instalável em qualquer máquina, ativo em qualquer projeto — construído com a anatomia padrão de plugin (skills, agentes especializados, hooks e um store central). A diferença é o que ele observa: não o código que você escreve, mas o **comportamento e o custo dos agentes que escrevem código por você**. Os dados ficam em `~/.agent-finops/telemetry.db` — nada sai da sua máquina.

## O que faz

**Enxerga o gasto.** `cost-report` cruza custo por projeto, por modelo, por dia — com os preços atuais direto da tabela oficial. `rightsizing` lê esse histórico e aponta, com números, onde um Opus está rodando uma tarefa de Haiku, onde o cache de prompt não está pegando, onde o volume já justifica a Batch API (-50%).

**Reduz o gasto, não só relata.** Duas camadas de economia real, medidas e registradas:
- `code-nav` e `safe-refactor` usam AST (ast-grep/tree-sitter) para o agente *ler menos* — busca estrutural em vez de abrir arquivos inteiros;
- `compress` conecta o [Headroom](https://github.com/chopratejas/headroom), que comprime 60–95% do que sobra antes de chegar ao modelo.

**Garante qualidade antes de ir pra produção.** `agent-gate` é o portão, em três etapas de natureza distinta: (1) validação sintática via **AST** — ast-grep/tree-sitter/parser nativo, determinístico, falha rápido sem custar uma rodada de testes; (2) a suíte de testes do projeto; (3) para mudanças arquiteturais relevantes, o veredito do [arch-review-assistant](https://github.com/juliopessan/arch-review-assistant) — um squad de 9 agentes LLM especializados em review arquitetural, **não** uma ferramenta de AST. Só depois das três etapas um agente sobe de status.

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
└── evals/           → gates de qualidade dos artefatos do plugin
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
- **agent-gate**: sintaxe (AST, determinístico) → testes → arch-review (squad LLM, não AST) → promoção
- **agent-auditor**: inventário e conformidade dos agentes dos projetos
