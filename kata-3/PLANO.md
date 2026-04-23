# Kata 3 — Plano de Ação Técnico: Sistema Legado em Colapso

---

## Seção 1 — Diagnóstico

### Problema 1 — Endpoint de consulta de pedidos: 8–12 segundos em horário de pico

**Causa raiz mais provável:**
Queries sem índices adequados sobre tabelas crescentes, ou N+1 queries (carregar pedido → para cada pedido, carregar cliente → carregar itens em loop). Com 800 pedidos/dia e 5 anos de operação, a tabela tem ~1,4 milhão de registros — suficiente para tornar um full table scan crítico.

**Risco técnico:** Timeout em clientes HTTP (padrão 10s), respostas incompletas, degradação que piora com o crescimento do volume.

**Risco de negócio:** 8–12 segundos é tempo suficiente para o usuário abandonar a tela ou ligar para o suporte. Comprometimento direto da experiência do cliente e aumento de carga no atendimento humano.

**Classificação (Matriz de Eisenhower):** 🔴 **Urgente e Importante** — afeta usuários ativamente, piora com o tempo, tem solução técnica relativamente rápida.

---

### Problema 2 — Pedidos criados em duplicidade

**Causa raiz mais provável:**
Ausência de controle de idempotência na camada de criação de pedidos. O usuário clica em "confirmar" duas vezes (double-click, clique após timeout aparente), o frontend dispara duas requisições, e o backend não possui verificação de unicidade (constraint UNIQUE ou chave idempotente). Pode também ser race condition em ambiente com múltiplas instâncias.

**Risco técnico:** Inconsistência de dados, pedidos fantasmas, dificuldade de reconciliação financeira.

**Risco de negócio:** Pedidos duplicados resultam em cobranças duplicadas, estoque incorreto, custo de atendimento para estorno. Em e-commerce, isso pode gerar chargebacks e dano à reputação.

**Classificação:** 🔴 **Urgente e Importante** — já causou impacto real, pode acontecer novamente a qualquer momento.

---

### Problema 3 — Correção de bug em produção sem PR e sem teste

**Causa raiz mais provável:**
Ausência de processo de engenharia (branching strategy, code review, CI/CD). Cultura de "apagar incêndio" diretamente no servidor. Pode ter sido motivado por pressão de tempo durante incidente.

**Risco técnico:** O código em produção diverge do repositório. A próxima deploy sobrescreve o hotfix. O bug pode retornar sem aviso. Ninguém sabe o que exatamente foi alterado.

**Risco de negócio:** Perda de rastreabilidade de mudanças. Em caso de auditoria ou novo incidente, é impossível saber o estado exato do sistema.

**Classificação:** 🟡 **Não urgente, mas Importante** — não está causando dano imediato agora, mas aumenta o risco de todos os outros problemas.

---

### Problema 4 — Arquivo de 4.000 linhas na camada de negócio

**Causa raiz mais provável:**
Crescimento orgânico sem refatoração — cada feature nova foi adicionada ao mesmo arquivo por conveniência. Ausência de arquitetura definida (camadas, módulos, responsabilidades).

**Risco técnico:** Alto acoplamento, impossibilidade de testar unidades isoladas, merges conflituosos frequentes, dificuldade de onboarding de novos membros.

**Risco de negócio:** Velocidade de desenvolvimento cai com o tempo. Custo de manutenção cresce. Qualquer mudança pode ter efeito colateral imprevisível.

**Classificação:** 🟡 **Não urgente, mas Importante** — não está causando incidente agora, mas é o solo fértil de onde todos os outros problemas crescem.

---

### Problema 5 — Ausência total de testes automatizados

**Causa raiz mais provável:**
Nunca foi priorizado ("funciona então não mexa"). Pode ter começado como MVP e nunca maturado. Com arquivo de 4.000 linhas e alto acoplamento, escrever testes retroativamente é difícil — o que cria um ciclo vicioso.

**Risco técnico:** Nenhuma validação automática de regressão. Qualquer mudança pode quebrar qualquer coisa. O time vive com medo de fazer deploys.

**Risco de negócio:** Deploys arriscados → deploys menos frequentes → acúmulo de mudanças → deploys ainda mais arriscados. Velocidade de entrega de valor ao negócio fica comprometida.

**Classificação:** 🟡 **Não urgente, mas Importante** — fundação que torna todos os outros problemas mais difíceis de resolver.

---

## Seção 2 — Plano de ação (top 3 priorizados)

### Prioridade 1 — Duplicidade de pedidos (Urgente + Importante)

**O que será feito:**
1. Adicionar constraint `UNIQUE` no banco de dados para a combinação `(id_cliente, id_carrinho, data_pedido::date)` ou campo `idempotency_key` gerado pelo frontend.
2. Implementar verificação na camada de serviço antes do `INSERT`: se já existe pedido com mesma chave nas últimas 24h, retornar o existente (não criar novo).
3. No frontend: desabilitar o botão "Confirmar" após o primeiro clique e mostrar loading state.

**Esforço estimado:** 1–2 dias (backend: ~4h, frontend: ~2h, testes manuais: ~2h)

**Critério de sucesso:** Zero pedidos duplicados por 30 dias em produção. Confirmado via query diária: `SELECT id_cliente, COUNT(*) FROM pedidos GROUP BY id_cliente, DATE(criado_em) HAVING COUNT(*) > 1`.

---

### Prioridade 2 — Performance do endpoint de pedidos (Urgente + Importante)

**O que será feito:**
1. **Análise de queries:** Ativar slow query log e identificar as 3 queries mais lentas relacionadas ao endpoint.
2. **Adicionar índices:** Provavelmente `CREATE INDEX idx_pedidos_cliente ON pedidos(id_cliente, criado_em DESC)` e similares.
3. **Eliminar N+1:** Reescrever o endpoint para usar JOIN em vez de múltiplas queries sequenciais.
4. **Paginação:** Se não existe, adicionar `LIMIT/OFFSET` ou cursor-based pagination para limitar o volume por request.

**Esforço estimado:** 2–3 dias (análise: 4h, índices + refatoração de query: 1 dia, validação: 4h)

**Critério de sucesso:** Endpoint responde em menos de 1 segundo para P95 em horário de pico. Medido via APM (New Relic, Datadog ou logs de tempo de resposta).

---

### Prioridade 3 — Estabelecer processo de deploy mínimo (Não urgente + Importante)

**O que será feito:**
1. Criar branch `main` como branch protegida: ninguém faz push direto.
2. Configurar pipeline mínimo de CI (GitHub Actions ou GitLab CI): lint + build a cada PR. Sem testes ainda — isso vem depois.
3. Documentar o processo em um `CONTRIBUTING.md`: como criar branch, abrir PR, fazer deploy.
4. Sincronizar o hotfix feito diretamente: descobrir o que foi alterado (diff com o repo), criar commit documentando a mudança.

**Esforço estimado:** 1 dia (pipeline básico: 3h, documentação: 2h, sync do hotfix: 1h)

**Critério de sucesso:** Zero deploys manuais diretos por 60 dias. Todos os merges em `main` passam pelo processo documentado.

---

## Seção 3 — Decisão de arquitetura: Refatoração vs. Reescrita

### Contexto reiterado
- Sem testes automatizados
- Sistema em produção com 800 pedidos/dia
- Time ocupado (implícito pelo acúmulo de problemas)
- Arquivo com 4.000 linhas de negócio crítico

### Minha escolha: **Opção A — Refatoração incremental**

**Argumentação:**

A Opção B (reescrita) é sedutora do ponto de vista técnico, mas é exatamente o tipo de decisão que Joel Spolsky chamou de ["o pior erro estratégico que uma empresa pode cometer"](https://www.joelonsoftware.com/2000/04/06/things-you-should-never-do-part-i/). A frase é forte, mas o princípio é sólido: o código legado, por pior que seja esteticamente, carrega **conhecimento implícito** de regras de negócio que foram aprendidas com incidentes reais. Uma reescrita do zero provavelmente vai recriar os mesmos bugs — só que desta vez sem o histórico de correções.

No contexto específico deste sistema:

**Contra a reescrita:**
- Sem testes, não há como garantir que a reescrita preserva o comportamento atual. Cada divergência é um bug em potencial em produção.
- O time está ocupado. Uma reescrita cria uma longa fase de "dois sistemas em paralelo" que drena energia e aumenta a superfície de manutenção.
- O risco de regressão é altíssimo: sem cobertura de testes, qualquer edge case não documentado (e há muitos em 5 anos de código) pode causar incidente.

**A favor da refatoração incremental:**
- O sistema **continua funcionando** durante todo o processo.
- Cada extração de módulo pode vir acompanhada de testes escritos **durante** a extração (estratégia de "pinça": escrevo o teste que descreve o comportamento atual, extraio o módulo, o teste passa → avançamos com segurança).
- Resultados visíveis ao gestor em semanas, não meses.
- Risco de regressão localizado a cada mudança incremental.

**Plano de execução da refatoração incremental:**
1. Identificar os 5–7 "domínios" dentro do arquivo (ex.: cálculo de frete, gestão de estoque, notificações, pagamento).
2. Começar pelo domínio **mais isolado** (menos acoplado), não pelo mais importante.
3. Para cada extração: escrever testes de caracterização → mover código → garantir testes verdes → PR → deploy.
4. Em 6–8 semanas, o arquivo de 4.000 linhas estará particionado em módulos testáveis.

---

## Seção 4 — Requisitos Não Funcionais ignorados

### RNF 1 — Desempenho (Performance)

**Por que está comprometido:** O endpoint de consulta demora 8–12 segundos. O limite aceitável para interfaces interativas é 1–2 segundos (Nielsen Norman Group). Qualquer tempo acima de 10 segundos faz o usuário desengajar completamente.

**Métrica mensurável:**
- Latência P95 do endpoint `/pedidos` < 1.000ms em horário de pico (9h–12h e 14h–18h).
- Medido via APM com janela de 7 dias. Alerta automático se P95 > 2.000ms por mais de 5 minutos consecutivos.

---

### RNF 2 — Confiabilidade / Integridade de dados (Reliability)

**Por que está comprometido:** Dois pedidos duplicados criados em uma semana indicam falha de integridade. Em um sistema de e-commerce, integridade de dados é a base de tudo: estoque, faturamento, logística.

**Métrica mensurável:**
- Taxa de pedidos duplicados = 0 por sprint (quinzenal).
- Verificado por query automatizada executada diariamente: qualquer resultado diferente de zero dispara alerta.
- Meta secundária: < 0.01% de divergência entre pedidos no sistema e pedidos na base financeira.

---

### RNF 3 — Manutenibilidade (Maintainability)

**Por que está comprometido:** Arquivo de 4.000 linhas em uma única camada, sem testes, com deploys manuais diretos em produção. A definição de manutenibilidade da ISO 25010 inclui modularidade, testabilidade e analisabilidade — nenhuma das três é atendida.

**Métrica mensurável:**
- **Cobertura de testes:** inicialmente 0%; meta de 40% em 3 meses e 70% em 6 meses.
- **Complexidade ciclomática média por função:** medida via ferramentas de análise estática (SonarQube, Code Climate). Meta: nenhuma função com complexidade > 10.
- **Tempo médio de onboarding:** novo desenvolvedor consegue fazer um deploy seguro em menos de 2 dias. Medido via checklist de onboarding.

---

### RNF 4 (bônus) — Rastreabilidade / Auditabilidade

**Por que está comprometido:** Um bug foi corrigido diretamente em produção sem PR, sem registro, sem revisão. É impossível saber o estado exato do código em produção ou quem fez o quê e quando.

**Métrica mensurável:**
- 100% dos deploys rastreáveis via git log com autor, data e descrição da mudança.
- Zero commits diretos em `main` por 60 dias (verificado via proteção de branch com relatório mensal).
