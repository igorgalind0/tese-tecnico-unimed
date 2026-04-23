# Kata 3 — Sistema Legado em Colapso

> **Contexto:** análise técnica de um sistema de pedidos de e-commerce com 5 anos de vida, 800 pedidos/dia e múltiplos incidentes recentes. O objetivo é elaborar um plano de ação priorizando os problemas e propondo soluções concretas.

---

## Sobre este Kata

Este kata **não contém código**. O produto entregue é um documento técnico (`PLANO.md`) que seria apresentado ao gestor antes de uma sprint de refatoração. O que é avaliado é a qualidade da análise, a capacidade de priorizar sob incerteza e a maturidade das decisões de engenharia.

---

## Tecnologia utilizada

Nenhuma. Documento Markdown puro.

A escolha do formato é intencional: um plano técnico precisa ser legível por desenvolvedores, gestores e stakeholders não-técnicos. Markdown renderiza bem no GitHub (onde o repositório será entregue), é versionável com git e não requer nenhuma ferramenta especial para leitura.

---

## Como está organizado

```
kata-3/
├── README.md     ← este arquivo
└── PLANO.md      ← documento técnico completo (4 seções)
```

### Estrutura do `PLANO.md`

**Seção 1 — Diagnóstico**
Cada um dos 5 incidentes é analisado com: causa raiz mais provável, risco técnico, risco de negócio e classificação pela Matriz de Eisenhower (urgente/importante).

**Seção 2 — Plano de ação**
Os 3 problemas priorizados, com descrição técnica do que será feito, estimativa de esforço em horas/dias e critério de sucesso mensurável — como saber que o problema foi resolvido de verdade.

**Seção 3 — Decisão de arquitetura**
Análise das duas opções para o arquivo de 4.000 linhas: refatoração incremental vs. reescrita do zero. Inclui argumentação sobre qual escolher dado o contexto específico (sem testes, sistema em produção, time ocupado).

**Seção 4 — RNFs ignorados**
Três Requisitos Não Funcionais claramente comprometidos, cada um com nome formal, explicação baseada nos incidentes e métrica mensurável para monitoramento.

---

## Como ler o documento

```bash
# No terminal, com formatação básica:
cat kata-3/PLANO.md

# Ou abra diretamente no GitHub após o push —
# o Markdown será renderizado automaticamente.
```

---

## Resumo das decisões principais

**Prioridade 1 — Duplicidade de pedidos**
Escolhido por já ter causado impacto real e ter solução técnica rápida: constraint UNIQUE no banco + idempotência no frontend. Estimativa: 1–2 dias.

**Prioridade 2 — Performance do endpoint (8–12s)**
Análise de queries lentas + índices compostos + eliminação de N+1. Estimativa: 2–3 dias.

**Prioridade 3 — Processo de deploy (hotfix sem PR)**
Branch protegida + pipeline de CI mínimo + documentação. Estimativa: 1 dia.

**Decisão de arquitetura: Refatoração incremental (Opção A)**
A reescrita é tecnicamente elegante mas arriscada demais sem cobertura de testes. A refatoração incremental permite entregas semanais visíveis, risco localizado e escrita de testes durante o processo — não antes, não depois.

O raciocínio completo, incluindo os trade-offs de cada opção, está em [`PLANO.md`](./PLANO.md).
