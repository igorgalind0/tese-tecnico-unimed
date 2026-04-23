const BASE = '/tasks';

export type TaskStatus = 'pending' | 'done';
export type TaskPriority = 'low' | 'medium' | 'high' | null;

export interface Task {
  id: number;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  created_at: string;
  updated_at: string;
}

export interface TaskCreate {
  title: string;
  description?: string;
  priority?: TaskPriority;
}

export interface TaskUpdate {
  title?: string;
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (res.status === 204) return undefined as T;
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail ?? `Erro ${res.status}`);
  return data as T;
}

export const api = {
  list: (status?: TaskStatus) =>
    request<Task[]>(`${BASE}${status ? `?status=${status}` : ''}`),

  create: (payload: TaskCreate) =>
    request<Task>(BASE, { method: 'POST', body: JSON.stringify(payload) }),

  update: (id: number, payload: TaskUpdate) =>
    request<Task>(`${BASE}/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),

  delete: (id: number) =>
    request<void>(`${BASE}/${id}`, { method: 'DELETE' }),
};
