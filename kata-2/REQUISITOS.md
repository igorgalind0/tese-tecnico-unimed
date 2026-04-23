# Kata 2 — Análise de Requisitos

## 1. Ambiguidades identificadas e decisões tomadas

### Ambiguidade 1 — "minhas tarefas": o sistema é multiusuário?
**Pergunta ao cliente:** "Quando você diz 'minhas tarefas', você quer que cada pessoa tenha sua própria lista isolada, ou toda a equipe compartilha a mesma lista?"

**Decisão tomada (sem resposta):** Implementei o sistema **sem autenticação** na versão atual, com uma única lista compartilhada. A arquitetura está preparada para adicionar `user_id` às tarefas sem quebrar a API (veja ENGENHARIA.md). Documentei isso como dívida técnica explícita.

---

### Ambiguidade 2 — "situação": quais são os estados possíveis?
**Pergunta ao cliente:** "Quais são os estados possíveis de uma tarefa? Apenas 'pendente' e 'concluída', ou existem outros como 'em andamento', 'cancelada', 'bloqueada'?"

**Decisão tomada:** Implementei dois estados: **`pending`** e **`done`**. O campo `status` é um enum no backend, facilitando a adição de novos estados sem migração complexa.

---

### Ambiguidade 3 — Exclusão de tarefas concluídas: soft delete ou hard delete?
**Pergunta ao cliente:** "Quando uma tarefa é deletada, ela deve sumir completamente do sistema ou ser apenas arquivada (para fins de histórico/auditoria)?"

**Decisão tomada:** Implementei **hard delete** (remoção física do banco). Se houver necessidade de histórico, adicionar coluna `deleted_at` é uma migração simples.

---

### Ambiguidade 4 — O filtro "só as pendentes ou só as concluídas" é exclusivo ou inclui "todas"?
**Pergunta ao cliente:** "O filtro deve ter três opções (todas / pendentes / concluídas) ou apenas dois estados?"

**Decisão tomada:** Implementei três opções: **todas, pendentes e concluídas**. É a UX mais natural e o endpoint suporta `?status=pending`, `?status=done` ou sem parâmetro para listar todas.

---

### Ambiguidade 5 — Campos obrigatórios: além do título, o que mais é necessário?
**Pergunta ao cliente:** "Uma tarefa precisa de descrição? Prazo? Responsável? Categoria?"

**Decisão tomada:** Implementei campos mínimos: `title` (obrigatório), `description` (opcional) e `priority` (opcional, já prevendo o requisito futuro mencionado).

---

## 2. Requisitos Funcionais (RF)

| ID   | Descrição |
|------|-----------|
| RF01 | O sistema deve permitir criar uma tarefa com título (obrigatório) e descrição (opcional). |
| RF02 | O sistema deve listar todas as tarefas, com suporte a filtro por status (pendente / concluída). |
| RF03 | O sistema deve permitir marcar uma tarefa como concluída. |
| RF04 | O sistema deve permitir excluir uma tarefa permanentemente. |
| RF05 | O sistema deve exibir indicação visual clara do status de cada tarefa na interface. |
| RF06 | O sistema deve permitir editar o título e a descrição de uma tarefa existente. |

---

## 3. Requisitos Não Funcionais (RNF)

| ID    | Descrição |
|-------|-----------|
| RNF01 | **Desempenho:** Listagem de tarefas deve responder em menos de 500ms para até 10.000 registros. |
| RNF02 | **Disponibilidade:** API deve retornar mensagens de erro estruturadas (JSON) em todos os casos de falha, nunca expondo stack traces. |
| RNF03 | **Usabilidade:** Interface deve funcionar em desktop e mobile (layout responsivo). |
| RNF04 | **Manutenibilidade:** Separação clara entre camadas (rota, serviço, repositório) para facilitar testes e extensão. |
| RNF05 | **Segurança básica:** Inputs devem ser validados no backend; IDs inválidos retornam 404, não 500. |

---

## 4. Requisito de prioridade — tratamento no backlog

O cliente indicou que a prioridade de tarefas **"pode ficar pra depois"** — linguagem clássica de requisito diferido.

**Como tratei:**

1. **Implementei o campo `priority` já no modelo de dados** (valores: `low`, `medium`, `high`, `null`). O campo é aceito na criação e atualização, mas é **ignorado na ordenação da listagem** por enquanto. Custo de implementação: ~15 minutos. Custo de não implementar e ter de migrar depois: potencialmente horas.

2. **No backlog**, este requisito entraria como uma **User Story** com critério de aceite claro:
   > *"Como usuário, quero definir uma prioridade (baixa/média/alta) ao criar ou editar uma tarefa, para que eu possa visualizar as mais importantes no topo da lista."*

3. **Priorização sugerida:** Épico "Organização" — Sprint 2 ou 3, após validação do fluxo básico de criação/conclusão/exclusão com usuários reais.
