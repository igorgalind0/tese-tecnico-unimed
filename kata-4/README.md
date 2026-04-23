# Kata 4 — Pipeline de Relatório

> **Contexto:** três arquivos CSV exportados de sistemas diferentes, com dados sujos e inconsistentes. O objetivo é construir um pipeline de transformação que produza um relatório consolidado com indicadores de desempenho logístico.

---

## Tecnologia utilizada

**Python 3.10+ + pandas 2.2**

| Tecnologia | Por quê |
|------------|---------|
| **Python** | Linguagem dominante em engenharia de dados; ecossistema maduro para ETL |
| **pandas** | Biblioteca padrão para transformação de dados tabulares em Python; joins, groupby, apply — tudo em uma API coesa |
| **csv (stdlib)** | Geração dos dados de exemplo sem dependências extras |
| **json (stdlib)** | Saída dos indicadores em formato estruturado e legível |

**Por que pandas e não outra coisa?**
Para o volume deste kata (dezenas a milhares de linhas), pandas é a escolha mais direta e legível. Para escala real (10M+ linhas/dia), a análise escrita em `ANALISE.md` explica a migração para Polars ou DuckDB.

---

## Como o código está organizado

```
kata-4/
├── requirements.txt          # só: pandas
├── ANALISE.md                # respostas às 4 perguntas do enunciado
│
├── data/                     # CSVs de entrada (gerados por gerar_dados.py)
│   ├── pedidos.csv
│   ├── clientes.csv
│   └── entregas.csv
│
├── output/                   # saída do pipeline
│   ├── consolidado.csv       # um registro por pedido, todas as colunas
│   └── indicadores.json      # KPIs calculados
│
└── src/
    ├── gerar_dados.py        # gera os 3 CSVs com problemas intencionais
    └── pipeline.py           # pipeline completo de ETL
```

---

## Problemas nos dados e como são tratados

Cada problema listado no enunciado tem tratamento explícito no código:

| Problema | Onde aparece | Como é tratado |
|----------|-------------|----------------|
| Datas em formatos mistos (`DD/MM/AAAA`, `AAAA-MM-DD`, timestamps) | `pedidos.csv`, `entregas.csv` | Função `parse_date()` tenta múltiplos formatos em sequência; retorna `None` se nenhum funcionar |
| Valores monetários com vírgula decimal (`1.250,99`) | `pedidos.csv` | Função `parse_valor()` detecta formato europeu vs. brasileiro pela presença de vírgula + ponto |
| Campos nulos em colunas obrigatórias | `pedidos.csv` (`id_cliente`, `valor_total`) | Registros descartados com log do total removido |
| IDs órfãos em `entregas.csv` | pedidos referenciados que não existem | Excluídos automaticamente via LEFT JOIN — entrega sem pedido não tem contexto válido |
| Cidades com grafias inconsistentes (`são paulo`, `SAO PAULO`) | `clientes.csv` | Função `normalizar_cidade()`: remove acentos via NFD + Title Case + colapsa espaços |

---

## Etapas do pipeline

O pipeline executa em 5 etapas numeradas, exibidas no terminal durante a execução:

```
[1/5] Carregar e limpar pedidos.csv
[2/5] Carregar e limpar clientes.csv
[3/5] Carregar e limpar entregas.csv
[4/5] JOIN das três fontes + cálculo de atraso_dias
[5/5] Cálculo dos indicadores consolidados
```

**Cálculo de `atraso_dias`:**
```
atraso_dias = data_realizada - data_prevista (em dias)
  negativo  → entrega antecipada
  zero      → entregue exatamente no prazo
  positivo  → entregue com atraso
  nulo      → ainda não entregue
```

---

## Como executar

### Pré-requisitos
- Python 3.10+ (`python --version`)

### Instalar dependências

```bash
cd kata-4
pip install -r requirements.txt
```

### Gerar os dados de exemplo

```bash
python src/gerar_dados.py
```

Cria os três CSVs em `data/` com problemas intencionais embutidos:
- `pedidos.csv` — 30 registros (com valores em formato europeu, datas mistas, nulos)
- `clientes.csv` — 10 registros (com grafias inconsistentes de cidade)
- `entregas.csv` — 35 registros (com 6 registros órfãos e datas em formatos mistos)

### Executar o pipeline

```bash
python src/pipeline.py
```

Saída no terminal:
```
🚀 Pipeline de Relatório — Kata 4
========================================
  [1/5] Carregando pedidos.csv...
     30 lidos → 26 válidos (4 descartados por nulos obrigatórios)
  [2/5] Carregando clientes.csv...
     10 clientes carregados
  [3/5] Carregando entregas.csv...
     35 entregas carregadas
  [4/5] Consolidando e calculando atraso_dias...
     35 pedidos consolidados

✅ Consolidado salvo em: kata-4/output/consolidado.csv
✅ Indicadores salvos em: kata-4/output/indicadores.json

📊 INDICADORES CONSOLIDADOS
========================================
{
  "total_pedidos_por_status": { "pago": 19, "em_processamento": 8, "cancelado": 8 },
  "ticket_medio_por_estado": { "BA": 1322.48, "CE": 1135.14, "PE": 1127.22, "SP": 1027.72 },
  "entregas_no_prazo_pct": 30.4,
  "entregas_com_atraso_pct": 69.6,
  "top3_cidades_volume_pedidos": { "Sao Paulo": 22, "Fortaleza": 6, "Recife": 4 },
  "media_atraso_dias_pedidos_atrasados": 8.1
}
```

---

## Colunas do arquivo consolidado

| Coluna | Descrição |
|--------|-----------|
| `id_pedido` | ID único do pedido |
| `nome_cliente` | Nome do cliente (de clientes.csv) |
| `cidade_normalizada` | Cidade sem acentos, Title Case |
| `estado` | UF do cliente |
| `valor_total` | Valor numérico normalizado (float) |
| `status_pedido` | Status do pedido (pago, cancelado, em_processamento) |
| `data_pedido` | Data normalizada para `YYYY-MM-DD` |
| `data_prevista_entrega` | Data prevista normalizada para `YYYY-MM-DD` |
| `data_realizada_entrega` | Data realizada normalizada (vazio se ainda não entregue) |
| `atraso_dias` | Diferença em dias (negativo = antecipado, nulo = pendente) |
| `status_entrega` | Status da entrega |

---

## Análise completa

As perguntas do enunciado (decisões de tratamento, idempotência, escala para 10M linhas, estratégia de testes) estão respondidas em detalhe em [`ANALISE.md`](./ANALISE.md).
