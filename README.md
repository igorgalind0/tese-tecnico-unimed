# Teste de Seleção — Desenvolvimento | Unimed Caruaru

**Nome completo**: Igor Galindo da Silva\
**E-mail**: igorgalindo950@gmail.com\
**Telefone**: 81 99172-7448

---

## Stack utilizada e justificativa

| Kata              | Stack                         | Justificativa                                                                                                                                                 |
| ----------------- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Kata 1            | **Python 3.12**               | Clareza expressiva para algoritmos; excelente suporte a `dataclasses`, `enum` e `unittest`. Facilita leitura e extensão das regras de negócio.                |
| Kata 2 — Backend  | **Python + FastAPI + SQLite** | FastAPI oferece tipagem automática, docs Swagger embutidas e async nativo. SQLite elimina dependências externas para avaliação local sem sacrificar SQL real. |
| Kata 2 — Frontend | **React + TypeScript (Vite)** | Alinhado à stack sugerida pela Unimed. Vite torna o setup mínimo e o build rápido. TypeScript garante contratos claros com a API.                             |
| Kata 4            | **Python + pandas**           | Pipeline de dados com pandas é idiomático, legível e amplamente usado em engenharia de dados.                                                                 |

---

## Como executar cada Kata

### Pré-requisitos globais

- Python 3.10+ (`python --version`)
- Node.js 18+ e npm (`node --version`)

---

### Kata 1 — Fila de Triagem

```bash
cd kata-1

# Executar a demonstração
python src/triagem.py

# Executar os testes unitários
python -m pytest tests/ -v

# Ou com unittest puro
python -m unittest discover tests/ -v
```

---

### Kata 2 — Painel de Tarefas

**Backend (FastAPI):**

```bash
cd kata-2/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# Docs Swagger disponíveis em: http://localhost:8000/docs
```

**Frontend (React + Vite):**

```bash
cd kata-2/frontend
npm install
npm run dev
# Disponível em: http://localhost:5173
```

> **Nota:** O backend deve estar rodando antes do frontend. O frontend consome a API em `http://localhost:8000`.

---

### Kata 3 — Análise de Engenharia

Kata puramente documental. Leia: `kata-3/PLANO.md`

---

### Kata 4 — Pipeline de Relatório

```bash
cd kata-4
pip install -r requirements.txt

# Gerar dados fictícios de exemplo
python src/gerar_dados.py

# Executar o pipeline completo
python src/pipeline.py

# Saída em: kata-4/output/consolidado.csv e indicadores.json
```

---

## O que eu faria diferente com mais tempo?

**Kata 1:**

- Implementaria uma priority queue real com `heapq` para inserção O(log n) em vez de ordenação completa a cada consulta — útil para filas dinâmicas de alta frequência.
- Adicionaria regras via arquivo de configuração (JSON/YAML) para tornar o motor de regras completamente plugável sem tocar no código.

**Kata 2:**

- Autenticação com JWT e suporte a múltiplos usuários (cada tarefa pertence a um `user_id`).
- Migrações de banco com Alembic em vez de `CREATE TABLE IF NOT EXISTS`.
- Testes de integração com `httpx` + `pytest-asyncio` cobrindo os endpoints E2E.
- Docker Compose unificando backend + frontend + banco.
- Frontend com React Query para cache e sincronização de estado servidor.

**Kata 4:**

- Substituiria pandas por **Polars** ou **DuckDB** para volumes de 10M+ linhas com uso de memória controlado.
- Orquestração com **Prefect** ou **Airflow** para scheduling diário, retries e alertas.
- Testes de qualidade de dados com **Great Expectations**.
- Output direto para um data warehouse (BigQuery, Redshift) em vez de CSV.

**Geral:**

- CI/CD com GitHub Actions rodando testes e linting em cada PR.
- Pre-commit hooks (ruff, black, mypy) para qualidade de código contínua.
- Containerização completa com Docker para reprodutibilidade total do ambiente.
