# Kata 1 — Análise Escrita

## 1. Estrutura de dados escolhida para modelar a fila

Utilizei uma **lista Python comum** (`list`) combinada com **ordenação in-place** via `sorted()` (Timsort).

**Por quê não uma priority queue (`heapq`)?**

| Critério | `list` + `sorted()` | `heapq` |
|----------|---------------------|---------|
| Caso de uso | Ordenar uma lista completa de uma vez | Inserção/remoção dinâmica frequente |
| Complexidade de ordenação | O(n log n) | O(log n) por operação |
| Múltiplos critérios de desempate | Trivial com tupla-chave | Requer wrapper |
| Leitura de todo o estado da fila | O(1) | O(n log n) |

O problema descrito é **batch**: a triagem recebe todos os pacientes e retorna a fila ordenada. Não há inserção contínua em tempo real — por isso `list + sorted` é a escolha mais simples e eficiente para este contexto.

Se o sistema precisasse de **inserção dinâmica** (pacientes chegando a qualquer momento, atendimentos acontecendo simultaneamente), migraria para `heapq` com uma chave composta `(-urgencia_efetiva, chegada_dt, id_sequencial)`.

---

## 2. Complexidade de tempo do algoritmo

**Fase de aplicação de regras:** O(n × k), onde k é o número de regras (constante atualmente = 2). Simplifica para **O(n)**.

**Fase de ordenação:** Python usa Timsort — **O(n log n)** no caso médio e pior caso.

**Total: O(n log n)**

### E com 1 milhão de pacientes?

O algoritmo **funcionaria**, mas com considerações:

- **Tempo:** Timsort em 10⁶ elementos é ~20M operações de comparação. Em Python puro, isso pode levar alguns segundos. Em produção, usaria **numpy** ou **pandas** para vetorização, ou implementaria em C# com LINQ otimizado.
- **Memória:** 10⁶ objetos `Paciente` em Python consomem ~500MB–1GB. Para produção, processaria em **chunks** ou delegaria a um banco de dados com `ORDER BY` indexado.
- **Abordagem diferente em escala:** Com volume alto, a ordenação ficaria no banco:
  ```sql
  ORDER BY urgencia_efetiva DESC, horario_chegada ASC
  ```
  com índice composto `(urgencia_efetiva, horario_chegada)`.

---

## 3. Interação entre as Regras 4 e 5

**As regras interagem, mas de forma controlada e sequencial.**

A implementação aplica as regras **em ordem**:
1. Primeiro, R4 (idoso com MÉDIA → ALTA)
2. Depois, R5 (menor de 18 → +1 nível)

Cada regra opera sobre `urgencia_efetiva`, que começa igual à urgência original e pode ser progressivamente elevada.

### Caso concreto: paciente com 15 anos e urgência MÉDIA

```
Estado inicial:       urgencia = MÉDIA,  urgencia_efetiva = MÉDIA
Após R4 (idoso?):     15 anos ≠ idoso → sem mudança → urgencia_efetiva = MÉDIA
Após R5 (menor?):     15 < 18 → +1 nível → urgencia_efetiva = ALTA
Estado final:         urgencia_efetiva = ALTA
```

**Resultado:** o paciente de 15 anos com MÉDIA chega à fila como ALTA.

### Caso hipotético de encadeamento total:
Um paciente de 12 anos com urgência BAIXA passaria por:
- R4: não se aplica (não é idoso)
- R5: BAIXA → MÉDIA

Se houvesse uma R3.5 futura para "menor + MÉDIA → ALTA", o encadeamento poderia ser problemático sem controle de ordem. A arquitetura atual (lista `_REGRAS`) garante determinismo pela sequência de aplicação.

---

## 4. Extensibilidade para uma 6ª regra

O código foi projetado com extensibilidade explícita em mente. Uma nova regra é adicionada em **dois passos apenas**:

**Passo 1:** Escrever a função da regra:
```python
def _aplicar_regra_gestante(paciente: Paciente) -> None:
    """Regra 6: Gestantes com qualquer urgência sobem +1 nível."""
    if paciente.is_gestante:
        novo_nivel = min(paciente.urgencia_efetiva.value + 1, Urgencia.CRITICA.value)
        paciente.urgencia_efetiva = Urgencia(novo_nivel)
```

**Passo 2:** Adicionar à lista `_REGRAS`:
```python
_REGRAS = [
    _aplicar_regra_idoso,
    _aplicar_regra_menor,
    _aplicar_regra_gestante,  # ← apenas isso
]
```

**Nenhum outro código é alterado.** A função `ordenar_fila` itera sobre `_REGRAS` sem conhecer as regras individualmente. Isso segue o **Open/Closed Principle**: aberto para extensão, fechado para modificação.

Para regras mais complexas (ex.: com pesos ou condições cruzadas), o próximo passo seria extrair as funções para uma classe `Regra` com método `aplicar(paciente) -> None`, permitindo configuração via JSON/banco de dados.

---

## Parte C — Modelagem de Banco de Dados

```sql
-- Pacientes cadastrados
CREATE TABLE pacientes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nome          TEXT    NOT NULL,
    data_nascimento DATE  NOT NULL,
    cpf           TEXT    UNIQUE NOT NULL
);

-- Filas de atendimento por dia/setor
CREATE TABLE filas (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    data_fila     DATE    NOT NULL,
    setor         TEXT    NOT NULL DEFAULT 'geral',
    criada_em     DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Registros de chegada e triagem
CREATE TABLE triagem (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    fila_id             INTEGER NOT NULL REFERENCES filas(id),
    paciente_id         INTEGER NOT NULL REFERENCES pacientes(id),
    urgencia_original   TEXT    NOT NULL CHECK(urgencia_original IN ('BAIXA','MEDIA','ALTA','CRITICA')),
    urgencia_efetiva    TEXT    NOT NULL CHECK(urgencia_efetiva  IN ('BAIXA','MEDIA','ALTA','CRITICA')),
    horario_chegada     DATETIME NOT NULL,
    posicao_fila        INTEGER,  -- calculado após ordenação
    criada_em           DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Registro de atendimentos realizados
CREATE TABLE atendimentos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    triagem_id      INTEGER NOT NULL REFERENCES triagem(id),
    iniciado_em     DATETIME NOT NULL,
    concluido_em    DATETIME,
    medico          TEXT,
    observacoes     TEXT
);

-- Índice para consultas por fila e urgência efetiva
CREATE INDEX idx_triagem_fila_urgencia
    ON triagem(fila_id, urgencia_efetiva DESC, horario_chegada ASC);
```
