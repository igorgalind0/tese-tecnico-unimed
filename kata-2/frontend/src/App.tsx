import { useState, useEffect, useCallback } from 'react';
import { api, Task, TaskStatus } from './api';

// ─── Estilos inline (evita dependência de CSS-in-JS) ──────────────────────

const S = {
  container: {
    maxWidth: 720,
    margin: '0 auto',
    padding: '32px 16px',
  } as React.CSSProperties,

  header: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    marginBottom: 32,
  } as React.CSSProperties,

  logo: {
    width: 36,
    height: 36,
    background: 'var(--primary)',
    borderRadius: 8,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#fff',
    fontWeight: 700,
    fontSize: 18,
    flexShrink: 0,
  } as React.CSSProperties,

  title: {
    fontSize: 22,
    fontWeight: 600,
    color: 'var(--text)',
  } as React.CSSProperties,

  card: {
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    padding: 20,
    marginBottom: 16,
    boxShadow: 'var(--shadow)',
  } as React.CSSProperties,

  formRow: {
    display: 'flex',
    gap: 8,
  } as React.CSSProperties,

  input: {
    flex: 1,
    padding: '10px 12px',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    fontSize: 14,
    outline: 'none',
    fontFamily: 'inherit',
  } as React.CSSProperties,

  btnPrimary: {
    padding: '10px 18px',
    background: 'var(--primary)',
    color: '#fff',
    border: 'none',
    borderRadius: 'var(--radius)',
    cursor: 'pointer',
    fontWeight: 600,
    fontSize: 14,
    fontFamily: 'inherit',
    whiteSpace: 'nowrap',
  } as React.CSSProperties,

  filterRow: {
    display: 'flex',
    gap: 8,
    marginBottom: 16,
  } as React.CSSProperties,

  taskItem: (done: boolean): React.CSSProperties => ({
    background: done ? '#fafafa' : 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    padding: '14px 16px',
    marginBottom: 8,
    display: 'flex',
    alignItems: 'flex-start',
    gap: 12,
    opacity: done ? 0.75 : 1,
    transition: 'opacity 0.2s',
  }),

  checkbox: {
    width: 18,
    height: 18,
    marginTop: 2,
    accentColor: 'var(--primary)',
    cursor: 'pointer',
    flexShrink: 0,
  } as React.CSSProperties,

  taskTitle: (done: boolean): React.CSSProperties => ({
    fontWeight: 500,
    textDecoration: done ? 'line-through' : 'none',
    color: done ? 'var(--text-muted)' : 'var(--text)',
    flex: 1,
    wordBreak: 'break-word',
  }),

  badge: (status: TaskStatus): React.CSSProperties => ({
    fontSize: 11,
    fontWeight: 600,
    padding: '2px 8px',
    borderRadius: 20,
    background: status === 'done' ? '#edf2f7' : 'var(--primary-light)',
    color: status === 'done' ? 'var(--text-muted)' : 'var(--primary)',
    flexShrink: 0,
    alignSelf: 'center',
  }),

  deleteBtn: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    color: 'var(--text-muted)',
    fontSize: 18,
    padding: '0 4px',
    lineHeight: 1,
    flexShrink: 0,
  } as React.CSSProperties,

  error: {
    background: 'var(--danger-light)',
    border: '1px solid #feb2b2',
    borderRadius: 'var(--radius)',
    padding: '10px 14px',
    color: 'var(--danger)',
    marginBottom: 16,
    fontSize: 13,
  } as React.CSSProperties,

  empty: {
    textAlign: 'center' as const,
    color: 'var(--text-muted)',
    padding: '40px 0',
    fontSize: 14,
  },
};

// ─── Componente FilterButton ───────────────────────────────────────────────

function FilterBtn({
  active, onClick, children,
}: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '8px 14px',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius)',
        background: active ? 'var(--primary)' : 'var(--surface)',
        color: active ? '#fff' : 'var(--text)',
        cursor: 'pointer',
        fontWeight: active ? 600 : 400,
        fontSize: 13,
        fontFamily: 'inherit',
        transition: 'all 0.15s',
      }}
    >
      {children}
    </button>
  );
}

// ─── App principal ─────────────────────────────────────────────────────────

type FilterValue = 'all' | 'pending' | 'done';

export default function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [filter, setFilter] = useState<FilterValue>('all');
  const [newTitle, setNewTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = useCallback(async (f: FilterValue) => {
    setLoading(true);
    setError(null);
    try {
      const status = f === 'all' ? undefined : (f as TaskStatus);
      const data = await api.list(status);
      setTasks(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchTasks(filter); }, [filter, fetchTasks]);

  const handleCreate = async () => {
    const title = newTitle.trim();
    if (!title) return;
    setError(null);
    try {
      await api.create({ title });
      setNewTitle('');
      fetchTasks(filter);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const handleToggle = async (task: Task) => {
    const newStatus: TaskStatus = task.status === 'pending' ? 'done' : 'pending';
    try {
      await api.update(task.id, { status: newStatus });
      fetchTasks(filter);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Excluir esta tarefa permanentemente?')) return;
    try {
      await api.delete(id);
      fetchTasks(filter);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <div style={S.container}>
      {/* Header */}
      <div style={S.header}>
        <div style={S.logo}>T</div>
        <h1 style={S.title}>Painel de Tarefas</h1>
      </div>

      {/* Formulário de criação */}
      <div style={S.card}>
        <div style={{ marginBottom: 12, fontWeight: 600 }}>Nova tarefa</div>
        <div style={S.formRow}>
          <input
            style={S.input}
            placeholder="Digite o título da tarefa..."
            value={newTitle}
            onChange={e => setNewTitle(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleCreate()}
            maxLength={255}
          />
          <button style={S.btnPrimary} onClick={handleCreate} disabled={!newTitle.trim()}>
            + Criar
          </button>
        </div>
      </div>

      {/* Mensagem de erro */}
      {error && (
        <div style={S.error}>
          ⚠️ {error}
        </div>
      )}

      {/* Filtros */}
      <div style={S.filterRow}>
        <FilterBtn active={filter === 'all'}     onClick={() => setFilter('all')}>Todas</FilterBtn>
        <FilterBtn active={filter === 'pending'} onClick={() => setFilter('pending')}>Pendentes</FilterBtn>
        <FilterBtn active={filter === 'done'}    onClick={() => setFilter('done')}>Concluídas</FilterBtn>
        <span style={{ marginLeft: 'auto', color: 'var(--text-muted)', alignSelf: 'center', fontSize: 13 }}>
          {loading ? 'Carregando...' : `${tasks.length} tarefa${tasks.length !== 1 ? 's' : ''}`}
        </span>
      </div>

      {/* Lista de tarefas */}
      {tasks.length === 0 && !loading ? (
        <div style={S.empty}>
          {filter === 'all'
            ? 'Nenhuma tarefa cadastrada. Crie a primeira acima!'
            : `Nenhuma tarefa ${filter === 'pending' ? 'pendente' : 'concluída'}.`}
        </div>
      ) : (
        tasks.map(task => (
          <div key={task.id} style={S.taskItem(task.status === 'done')}>
            <input
              type="checkbox"
              style={S.checkbox}
              checked={task.status === 'done'}
              onChange={() => handleToggle(task)}
              title={task.status === 'done' ? 'Marcar como pendente' : 'Marcar como concluída'}
            />
            <span style={S.taskTitle(task.status === 'done')}>{task.title}</span>
            <span style={S.badge(task.status)}>
              {task.status === 'done' ? 'Concluída' : 'Pendente'}
            </span>
            <button
              style={S.deleteBtn}
              onClick={() => handleDelete(task.id)}
              title="Excluir tarefa"
            >
              ×
            </button>
          </div>
        ))
      )}
    </div>
  );
}
