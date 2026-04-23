# Kata 2 — Análise de Engenharia

## 1. Decisões de arquitetura no backend

### Separação de responsabilidades
Mantive o projeto em um único arquivo `main.py` por ser uma aplicação pequena com 5 endpoints. Para um sistema maior, a separação natural seria:

```
backend/
├── main.py           # startup, middleware, montagem do app
├── routers/
│   └── tasks.py      # endpoints HTTP
├── services/
│   └── task_service.py  # regras de negócio
├── repositories/
│   └── task_repo.py  # acesso ao banco (SQL isolado aqui)
└── models/
    └── schemas.py    # Pydantic schemas (request/response)
```

Esse padrão (Router → Service → Repository) separa o protocolo HTTP da lógica de negócio e do acesso a dados, permitindo testar cada camada isoladamente.

### Validação na borda
Toda validação de entrada acontece nos **schemas Pydantic** antes de chegar ao código de negócio. O FastAPI retorna automaticamente erros 422 bem estruturados para payloads inválidos.

### Contexto transacional
O `@contextmanager get_conn()` garante que cada request abre uma conexão, faz commit no sucesso e rollback em falha, e fecha a conexão — evitando connection leaks.

### SQLite como persistência
Decisão consciente para este contexto de avaliação: zero dependências externas, SQL real. Em produção, bastaria trocar a connection string para PostgreSQL e adicionar um pool de conexões (ex.: `asyncpg` com SQLAlchemy async).

---

## 2. Como garantir confiabilidade em produção

### Aspecto 1 — Observabilidade com logs estruturados
```python
import structlog
log = structlog.get_logger()

# Em cada endpoint:
log.info("task.created", task_id=task.id, title=task.title, user_ip=request.client.host)
log.error("task.delete.not_found", task_id=task_id)
```
Logs estruturados (JSON) permitem indexação e busca em ferramentas como Datadog, Grafana Loki ou CloudWatch. Com logs por request, é possível rastrear qualquer incidente até a causa raiz.

### Aspecto 2 — Health check + métricas de latência
O endpoint `/health` já existe. Em produção, adicionaria:
- **Métricas Prometheus** via `prometheus-fastapi-instrumentator`: latência P50/P95/P99 por endpoint, taxa de erros, requests/segundo.
- **Alertas automáticos**: se P95 > 500ms ou taxa de erro > 1% por 5 minutos → notificação no Slack/PagerDuty.

### Aspecto adicional — Testes de integração
```python
# Com httpx + pytest:
def test_create_and_list_task(client):
    resp = client.post("/tasks", json={"title": "Nova tarefa"})
    assert resp.status_code == 201
    task_id = resp.json()["id"]

    resp = client.get("/tasks")
    ids = [t["id"] for t in resp.json()]
    assert task_id in ids
```
Testes E2E contra um banco SQLite de teste (`:memory:`) cobrem o fluxo completo sem dependências externas.

---

## 3. O que mudaria para suportar múltiplos usuários com autenticação

### Mudanças no modelo de dados
```sql
-- Nova tabela de usuários
CREATE TABLE users (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    email        TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at   TEXT NOT NULL
);

-- Adicionar FK em tasks
ALTER TABLE tasks ADD COLUMN user_id INTEGER REFERENCES users(id);
```

### Mudanças na API
1. **Autenticação JWT:** endpoint `POST /auth/login` retorna `access_token`. Middleware de autenticação valida o token em cada request protegido.

2. **Isolamento por usuário:** cada query de `tasks` filtra por `user_id` extraído do token:
   ```python
   current_user: User = Depends(get_current_user)
   conn.execute("SELECT * FROM tasks WHERE user_id = ?", (current_user.id,))
   ```

3. **Autorização:** verificar que o usuário só pode modificar suas próprias tarefas (retornar 403 para tentativas de acessar tarefas de outros).

4. **Refresh tokens** + expiração curta do `access_token` para segurança.

### Mudanças de infraestrutura
- Trocar SQLite por **PostgreSQL** (suporte a múltiplas conexões simultâneas)
- Adicionar **Redis** para blacklist de tokens revogados
- Rate limiting por usuário para evitar abuso da API
