# Evals

Gates de qualidade dos artefatos do plugin:

- **skill-hygiene**: todo `SKILL.md` tem frontmatter `name`/`description` e comandos executáveis
- **script-validation**: `python3 scripts/gate.py hooks/*.py store/*.py scripts/*.py dashboard/*.py` deve passar
- **behavior-conformance** (futuro): cenários de teste dos agentes cost-analyst/budget-guardian/agent-auditor

Rodar localmente:
```bash
python3 scripts/gate.py hooks/telemetry.py store/db.py store/ingest_transcripts.py scripts/*.py dashboard/generate_dashboard.py
```
