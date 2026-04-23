# Kata 2 — Painel de Tarefas

> **Contexto:** ferramenta interna de gerenciamento de tarefas com backend REST e frontend web, construída a partir de requisitos informais.

---

## Tecnologias utilizadas

### Backend — Python + FastAPI + SQLite

| Tecnologia | Versão | Por quê |
|------------|--------|---------|
| **Python** | 3.10+ | Linguagem base; ecossistema rico para APIs |
| **FastAPI** | 0.115 | Validação automática via Pydantic, docs Swagger embutidas, async nativo, performance próxima ao Node.js |
| **Pydantic v2** | 2.8 | Schemas tipados para request/response; rejeita payloads inválidos automaticamente com mensagens claras |
| **SQLite** | embutido | Zero dependências externas; SQL real (não mock em memória); fácil de inspecionar; trocar por Postgres em produção é só mudar a connection string |
| **Uvicorn** | 0.30 | Servidor ASGI de alta performance para rodar o FastAPI |

**Por que FastAPI e não Flask ou Django?**
Flask exigiria serialização manual e validação manual. Django seria pesado demais para 5 endpoints simples. FastAPI gera documentação interativa automaticamente em `/docs` — o avaliador pode testar todos os endpoints sem precisar de Postman.

### Frontend — React + TypeScript + Vite

| Tecnologia | Versão | Por quê |
|------------|--------|---------|
| **React** | 18 | Alinhado à stack recomendada pela Unimed Caruaru |
| **TypeScript** | 5.5 | Contratos explícitos com a API; erros em tempo de compilação em vez de runtime |
| **Vite** | 5.4 | Build tool moderno; dev server com HMR instantâneo; zero configuração para React+TS |

O frontend usa **apenas React puro** — sem Redux, sem React Query, sem biblioteca de componentes. A simplicidade é intencional: o enunciado pede funcionalidade, não complexidade. O código fica mais fácil de ler e avaliar.

---

## Como o código está organizado

```
kata-2/
├── REQUISITOS.md              # análise de requisitos: ambiguidades, RF, RNF
├── ENGENHARIA.md              # decisões de arquitetura e escalabilidade
│
├── backend/
│   ├── main.py                # API completa (FastAPI)
│   └── requirements.txt
│
└── frontend/
    ├── index.html             # entrada HTML
    ├── package.json           # dependências npm
    ├── vite.config.ts         # proxy /tasks → localhost:8000
    ├── tsconfig.json
    └── src/
        ├── main.tsx           # monta o React no DOM
        ├── App.tsx            # componente principal com toda a UI
        ├── api.ts             # serviço de chamadas HTTP (separado da UI)
        └── index.css          # variáveis CSS e reset global
```

### O que está em `main.py` (backend)

O arquivo tem seções claramente comentadas:

- **Configuração**: inicialização do app FastAPI, CORS middleware (aceita qualquer origem em dev)
- **Banco de dados**: `init_db()` cria a tabela na primeira execução; `get_conn()` é um context manager que garante commit/rollback/close automaticamente
- **Schemas Pydantic**: `TaskCreate`, `TaskUpdate`, `TaskResponse` — definem o contrato da API com validação de tipos e tamanhos
- **Endpoints**: 5 rotas (`GET /tasks`, `POST /tasks`, `GET /tasks/{id}`, `PATCH /tasks/{id}`, `DELETE /tasks/{id}`) + `/health`
- **Modelo de dados**: campo `priority` já está no banco e na API (valores: `low`, `medium`, `high`) — o requisito diferido do cliente está tecnicamente suportado, só falta a UI

### O que está em `App.tsx` (frontend)

- Estado gerenciado com `useState` para lista de tarefas, filtro ativo e campo do formulário
- `useCallback` + `useEffect` para buscar tarefas sempre que o filtro muda
- Estilos inline via objeto `S` (sem dependência de CSS-in-JS, sem classes externas)
- Separação clara: a UI não faz `fetch` diretamente — delega para `api.ts`

### O que está em `api.ts`

Camada de serviço isolada: todos os `fetch` ficam aqui. A UI só chama `api.list()`, `api.create()`, `api.update()`, `api.delete()`. Se a URL base mudar, só este arquivo é alterado.

---

## Como executar

### Pré-requisitos
- Python 3.10+ (`python --version`)
- Node.js 18+ e npm (`node --version`)

### Backend

```bash
cd kata-2/backend

# Instalar dependências
pip install -r requirements.txt

# Iniciar o servidor (cria tasks.db automaticamente na primeira execução)
uvicorn main:app --reload --port 8000
```

O banco SQLite (`tasks.db`) é criado automaticamente na pasta `backend/` na primeira execução. Para resetar o banco, basta apagar o arquivo.

**Documentação interativa da API:**
Abra `http://localhost:8000/docs` — o Swagger UI gerado automaticamente pelo FastAPI permite testar todos os endpoints diretamente no browser.

### Frontend

Em outro terminal:

```bash
cd kata-2/frontend

# Instalar dependências
npm install

# Iniciar o servidor de desenvolvimento
npm run dev
```

Acesse `http://localhost:5173`.

> **Importante:** o backend deve estar rodando antes de abrir o frontend. O Vite está configurado com proxy em `vite.config.ts` — chamadas para `/tasks` são redirecionadas automaticamente para `http://localhost:8000`, sem problemas de CORS em desenvolvimento.

---

## Endpoints da API

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/tasks` | Lista tarefas. Filtro opcional: `?status=pending` ou `?status=done` |
| `POST` | `/tasks` | Cria tarefa. Body: `{"title": "...", "description": "...", "priority": "low\|medium\|high"}` |
| `GET` | `/tasks/{id}` | Busca tarefa por ID |
| `PATCH` | `/tasks/{id}` | Atualização parcial. Qualquer campo pode ser omitido |
| `DELETE` | `/tasks/{id}` | Remove permanentemente. Retorna 204 (sem body) |
| `GET` | `/health` | Health check. Retorna `{"status": "ok", "timestamp": "..."}` |

**Respostas de erro são sempre JSON estruturado:**
```json
{ "detail": "Tarefa 99 não encontrada." }
```

---

## Funcionalidades da interface

- **Listagem** de todas as tarefas com badge de status colorido (verde = pendente, cinza = concluída)
- **Criação** via campo de texto + botão (ou Enter)
- **Conclusão** via checkbox — clica novamente para reverter para pendente
- **Exclusão** via botão ×, com confirmação antes de deletar
- **Filtro** por Todas / Pendentes / Concluídas com contador de resultados
- **Tratamento de erros** — mensagem visual se a API estiver fora do ar

---

## Análise completa

- Ambiguidades identificadas, decisões tomadas, RFs e RNFs: [`REQUISITOS.md`](./REQUISITOS.md)
- Arquitetura, observabilidade e plano de autenticação: [`ENGENHARIA.md`](./ENGENHARIA.md)
