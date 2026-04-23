"""
Kata 2 — Backend: Painel de Tarefas
=====================================
API REST construída com FastAPI + SQLite.
"""

from __future__ import annotations

import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configuração

DB_PATH = os.environ.get("DB_PATH", "tasks.db")

app = FastAPI(
    title="Painel de Tarefas — Unimed Caruaru",
    version="1.0.0",
    description="API REST para gerenciamento de tarefas da equipe interna.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção: restringir para o domínio do frontend
    allow_methods=["*"],
    allow_headers=["*"],
)


# Banco de dados

def init_db() -> None:
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                description TEXT,
                status      TEXT    NOT NULL DEFAULT 'pending'
                                    CHECK(status IN ('pending', 'done')),
                priority    TEXT             DEFAULT NULL
                                    CHECK(priority IS NULL OR priority IN ('low', 'medium', 'high')),
                created_at  TEXT    NOT NULL,
                updated_at  TEXT    NOT NULL
            )
        """)


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@app.on_event("startup")
def startup():
    init_db()


# Schemas (Pydantic)

class TaskStatus(str, Enum):
    pending = "pending"
    done    = "done"


class TaskPriority(str, Enum):
    low    = "low"
    medium = "medium"
    high   = "high"


class TaskCreate(BaseModel):
    title:       str            = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    priority:    Optional[TaskPriority] = None


class TaskUpdate(BaseModel):
    title:       Optional[str]          = Field(None, min_length=1, max_length=255)
    description: Optional[str]          = Field(None, max_length=2000)
    status:      Optional[TaskStatus]   = None
    priority:    Optional[TaskPriority] = None


class TaskResponse(BaseModel):
    id:          int
    title:       str
    description: Optional[str]
    status:      TaskStatus
    priority:    Optional[TaskPriority]
    created_at:  str
    updated_at:  str


def _row_to_task(row: sqlite3.Row) -> TaskResponse:
    return TaskResponse(
        id          = row["id"],
        title       = row["title"],
        description = row["description"],
        status      = row["status"],
        priority    = row["priority"],
        created_at  = row["created_at"],
        updated_at  = row["updated_at"],
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Endpoints

@app.get("/tasks", response_model=List[TaskResponse], summary="Listar tarefas")
def list_tasks(
    status: Optional[TaskStatus] = Query(
        None,
        description="Filtrar por status: 'pending' ou 'done'. Omita para listar todas."
    )
):
    """Retorna todas as tarefas, opcionalmente filtradas por status."""
    with get_conn() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC",
                (status.value,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC"
            ).fetchall()
    return [_row_to_task(r) for r in rows]


@app.post("/tasks", response_model=TaskResponse, status_code=201, summary="Criar tarefa")
def create_task(payload: TaskCreate):
    """Cria uma nova tarefa com status inicial 'pending'."""
    now = _now()
    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO tasks (title, description, priority, status, created_at, updated_at)
            VALUES (?, ?, ?, 'pending', ?, ?)
            """,
            (payload.title, payload.description, payload.priority, now, now),
        )
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return _row_to_task(row)


@app.get("/tasks/{task_id}", response_model=TaskResponse, summary="Buscar tarefa por ID")
def get_task(task_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Tarefa {task_id} não encontrada.")
    return _row_to_task(row)


@app.patch("/tasks/{task_id}", response_model=TaskResponse, summary="Atualizar tarefa")
def update_task(task_id: int, payload: TaskUpdate):
    """
    Atualização parcial (PATCH).
    Aceita qualquer combinação de campos: title, description, status, priority.
    """
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="Nenhum campo fornecido para atualização.")

    updates["updated_at"] = _now()

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [task_id]

    with get_conn() as conn:
        cursor = conn.execute(
            f"UPDATE tasks SET {set_clause} WHERE id = ?", values
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Tarefa {task_id} não encontrada.")
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

    return _row_to_task(row)


@app.delete("/tasks/{task_id}", status_code=204, summary="Excluir tarefa")
def delete_task(task_id: int):
    """Remove a tarefa permanentemente. Retorna 404 se não existir."""
    with get_conn() as conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"Tarefa {task_id} não encontrada.")


# Health check (para observabilidade)

@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "timestamp": _now()}
