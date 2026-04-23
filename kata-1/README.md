# Kata 1 — Fila de Triagem

> **Contexto:** sistema de ordenação de pacientes para clínica médica, respeitando regras de urgência, idade e ordem de chegada.

---

## Tecnologia utilizada

**Python 3.10+** — sem nenhuma dependência externa além do `pytest` para testes.

A escolha foi intencional: o problema é puramente algorítmico e de modelagem de domínio. Usar um framework ou biblioteca aqui seria ruído. Python oferece `dataclasses`, `enum` e `sorted()` estável nativamente — exatamente o que o problema pede.

---

## Como o código está organizado

```
kata-1/
├── src/
│   └── triagem.py        # toda a lógica do sistema
├── tests/
│   └── test_triagem.py   # 17 testes unitários
├── ANALISE.md            # respostas às perguntas do enunciado
└── requirements.txt      # só pytest
```

### O que está em `triagem.py`

O arquivo tem quatro partes bem delimitadas:

**1. Domínio (`Urgencia`, `Paciente`)**
`Urgencia` é um `IntEnum` — os níveis têm valores numéricos crescentes (BAIXA=1, CRÍTICA=4), o que permite comparação direta com `>` e `min()`/`max()` sem nenhum `if`. `Paciente` é um `dataclass` com dois campos de urgência: a original (imutável, como o médico classificou) e a efetiva (calculada após aplicar as regras).

**2. Motor de regras**
Cada regra de negócio é uma função isolada que recebe um `Paciente` e modifica sua `urgencia_efetiva`. As funções ficam numa lista `_REGRAS` e são aplicadas em sequência. Adicionar uma 6ª regra é só escrever a função e colocá-la na lista — nenhum outro código muda.

**3. Ordenação**
`ordenar_fila()` aplica todas as regras e retorna a lista ordenada por `(-urgencia_efetiva, horario_chegada)`. O sinal negativo inverte a ordem (maior urgência = primeiro). O Timsort do Python é estável, o que garante o critério FIFO automaticamente em caso de empate total.

**4. Demo**
O bloco `if __name__ == "__main__"` mostra uma fila de exemplo com todos os cenários das regras, incluindo promoções de urgência visíveis na saída.

---

## Como executar

### Pré-requisitos
- Python 3.10 ou superior (`python --version`)

### Instalar dependências
```bash
pip install -r requirements.txt
```

### Rodar a demonstração
```bash
python src/triagem.py
```

Saída esperada (a ordem respeita todas as 5 regras):
```
Pos  Nome                 Idade  Urgência orig.  Urgência efet.  Chegada
---------------------------------------------------------------------------
1    Pedro Alves          45     CRITICA         CRITICA         07:50
2    Bruno Costa          10     ALTA            CRITICA         08:20   ← Regra 5
3    Carlos Lima          72     MEDIA           ALTA            08:05   ← Regra 4
4    João Pedro           15     MEDIA           ALTA            08:10   ← Regra 5
5    Maria Oliveira       15     MEDIA           ALTA            08:15   ← Regra 5
6    Ana Souza            35     MEDIA           MEDIA           08:00
7    Lúcia Ferreira       68     BAIXA           BAIXA           07:45
```

### Rodar os testes
```bash
python -m pytest tests/ -v
```

Todos os 17 testes passam. Eles cobrem:
- Regra 4 isolada (idoso + MÉDIA → ALTA, com casos de borda: 59 anos, urgência BAIXA, urgência CRÍTICA)
- Regra 5 isolada (menor + cada nível, incluindo CRÍTICA que não pode subir mais, limite exato de 18 anos)
- Interação entre R4 e R5 (o caso do paciente de 15 anos com MÉDIA do enunciado)
- Ordenação completa (CRÍTICA sempre primeiro, FIFO dentro do mesmo nível, lista vazia, paciente único)

---

## Decisões de design

**Por que `IntEnum` e não `str`?**
Comparações de prioridade como `urgencia_a > urgencia_b` funcionam diretamente com `IntEnum`. Com strings precisaria de um dicionário auxiliar de mapeamento para qualquer comparação.

**Por que separar `urgencia` de `urgencia_efetiva`?**
Preservar a urgência original permite auditoria ("o médico classificou como MÉDIA, o sistema promoveu para ALTA pela regra 4"). Também evita efeitos colaterais se a fila for reordenada mais de uma vez — `aplicar_regras()` sempre parte do valor original.

**Por que lista `_REGRAS` e não `if/elif`?**
Com `if/elif`, adicionar uma nova regra exige modificar o bloco central da função. Com a lista, a função `aplicar_regras()` nunca precisa ser tocada. Isso segue o Open/Closed Principle e facilita testes — cada regra pode ser testada individualmente ou removida da lista para debug.

---

## Análise completa

As perguntas do enunciado (estrutura de dados, complexidade, interação R4+R5, extensibilidade) estão respondidas em detalhe em [`ANALISE.md`](./ANALISE.md), incluindo a modelagem de banco de dados SQL opcional.
