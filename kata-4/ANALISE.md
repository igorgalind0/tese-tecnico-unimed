# Kata 4 — Análise Escrita

## 1. Principais decisões de tratamento

### Registros órfãos (id_pedido em entregas.csv sem correspondência em pedidos.csv)
**Decisão:** Excluídos automaticamente via `LEFT JOIN` de pedidos com entregas. O pedido é a entidade central — uma entrega sem pedido não tem contexto de negócio válido. Os órfãos são descartados silenciosamente, mas o pipeline loga o total de entregas carregadas vs. pedidos consolidados, tornando a discrepância visível.

**Alternativa considerada:** guardar os órfãos em um arquivo separado `output/orfaos_entregas.csv` para auditoria. Em produção, essa seria a abordagem correta — descartar silenciosamente dados pode esconder erros de integração entre sistemas.

### Registros com campos obrigatórios nulos (id_cliente, valor_total)
**Decisão:** Descartados com log do total removido. Um pedido sem cliente ou sem valor é inútil para qualquer análise financeira ou de relacionamento. Manter esses registros com valores padrão (ex.: cliente = "Desconhecido") distorceria métricas como ticket médio por estado.

### Normalização de cidades
**Decisão:** Remover acentos via NFD + Title Case + colapsar espaços extras. Exemplo: `"são paulo"` → `"Sao Paulo"`, `"SAO PAULO"` → `"Sao Paulo"`. A remoção de acentos foi escolhida intencionalmente para garantir agrupamento consistente mesmo quando o dado original tem acentuação inconsistente. Em um sistema de produção, a abordagem ideal seria um dicionário de canonicalização (`{"sao paulo": "São Paulo"}`) para preservar o acento correto.

### Datas em formatos mistos
**Decisão:** Tentativa sequencial de múltiplos formatos (`%d/%m/%Y`, `%Y-%m-%d`, `%Y-%m-%dT%H:%M:%S`). Se nenhum formato reconhece a data, o campo vira `None` — nunca levanta exceção. Isso garante que um registro com data inválida não derruba o pipeline inteiro.

### Valores monetários com vírgula decimal
**Decisão:** Heurística de detecção: se o valor contém vírgula E ponto, interpreta como formato europeu (`1.250,99` → `1250.99`); se contém só vírgula, interpreta como decimal brasileiro (`1250,99` → `1250.99`). Essa heurística cobre 99% dos casos práticos de dados exportados de ERPs brasileiros.

---

## 2. O pipeline é idempotente?

**Sim.** Rodar o pipeline duas vezes produz exatamente o mesmo resultado.

**Por quê:**
- A leitura é sempre dos mesmos arquivos CSV de entrada (`data/`).
- As transformações são puras: sem estado externo, sem datas "de hoje" nas transformações de negócio, sem auto-incremento.
- A escrita é `overwrite` — o arquivo de saída é sempre substituído, nunca acumulado.
- A ordenação do resultado é determinística (depende apenas dos dados de entrada).

**O que quebraria a idempotência:**
- Se o pipeline gerasse um `id` sequencial baseado em contagem de registros existentes no output.
- Se usasse `datetime.now()` para marcar registros processados.
- Se fizesse `append` em vez de `overwrite` no arquivo de saída.

Nenhuma dessas situações ocorre na implementação atual.

---

## 3. Pipeline com 10 milhões de linhas por dia: o que mudaria?

### Problema central com pandas em escala
Pandas carrega **tudo na memória RAM**. 10M linhas de pedidos com ~10 colunas ocupa ~800MB–2GB apenas para o DataFrame — antes de joins e transformações. Em um servidor com 8GB de RAM compartilhada, isso é inaceitável.

### Mudanças na abordagem

**Processamento em memória:**
- Substituiria pandas por **Polars** (processamento lazy, multi-thread nativo, ~10x mais rápido) ou **DuckDB** (SQL sobre arquivos CSV/Parquet sem carregar tudo na RAM).

```python
# Com DuckDB — processa 10M linhas sem carregar tudo na memória
import duckdb
duckdb.sql("""
    SELECT p.id_pedido, c.nome, ...
    FROM 'data/pedidos.csv' p
    JOIN 'data/clientes.csv' c USING (id_cliente)
    LEFT JOIN 'data/entregas.csv' e USING (id_pedido)
""").write_csv("output/consolidado.csv")
```

**Formato de dados:**
- Trocar CSV por **Parquet** (colunar, comprimido, 5–10x menor, leitura 20x mais rápida).

**Orquestração:**
- **Prefect** ou **Apache Airflow** para scheduling diário, retries automáticos e alertas em caso de falha.
- DAG: `download_arquivos → validar_schema → transformar → calcular_indicadores → notificar`.

**Destino final:**
- Em vez de CSV, escrever diretamente em um **data warehouse** (BigQuery, Redshift, Snowflake) particionado por data, permitindo queries analíticas incrementais sem reprocessar tudo.

**Monitoramento de qualidade:**
- **Great Expectations** para validar contratos de dados: "coluna `valor_total` nunca nula", "100% dos `id_cliente` em pedidos existem em clientes".

---

## 4. Testes que eu escreveria

### Testes unitários das funções de limpeza

```python
# test_pipeline.py

def test_parse_date_formatos_mistos():
    assert parse_date("15/03/2024") == datetime(2024, 3, 15)
    assert parse_date("2024-03-15") == datetime(2024, 3, 15)
    assert parse_date("2024-03-15T10:30:00") == datetime(2024, 3, 15, 10, 30)
    assert parse_date("") is None
    assert parse_date("data_invalida") is None

def test_parse_valor_formatos_mistos():
    assert parse_valor("1250.99")    == 1250.99
    assert parse_valor("1250,99")    == 1250.99
    assert parse_valor("1.250,99")   == 1250.99   # formato europeu
    assert parse_valor("")           is None
    assert parse_valor("N/A")        is None

def test_normalizar_cidade():
    assert normalizar_cidade("são paulo")  == "Sao Paulo"
    assert normalizar_cidade("SAO PAULO")  == "Sao Paulo"
    assert normalizar_cidade("São Paulo")  == "Sao Paulo"
    assert normalizar_cidade("  caruaru ") == "Caruaru"
    assert normalizar_cidade("")           == ""

def test_calc_atraso_dias():
    # Antecipado: atraso negativo
    row = {"data_realizada_dt": datetime(2024,3,10), "data_prevista_dt": datetime(2024,3,15)}
    assert calc_atraso(row) == -5

    # Exatamente no prazo
    row = {"data_realizada_dt": datetime(2024,3,15), "data_prevista_dt": datetime(2024,3,15)}
    assert calc_atraso(row) == 0

    # Sem entrega registrada
    row = {"data_realizada_dt": None, "data_prevista_dt": datetime(2024,3,15)}
    assert calc_atraso(row) is None
```

### Testes de integração do pipeline completo

```python
def test_pipeline_idempotente(tmp_path):
    """Rodar duas vezes deve produzir exatamente o mesmo arquivo."""
    main(output_dir=tmp_path)
    hash1 = md5(tmp_path / "consolidado.csv")
    main(output_dir=tmp_path)
    hash2 = md5(tmp_path / "consolidado.csv")
    assert hash1 == hash2

def test_orfaos_excluidos(tmp_path):
    """Registros de entregas sem pedido correspondente não devem aparecer no consolidado."""
    main(output_dir=tmp_path)
    df = pd.read_csv(tmp_path / "consolidado.csv")
    ids_validos = pd.read_csv("data/pedidos.csv")["id_pedido"].tolist()
    assert all(id_ped in ids_validos for id_ped in df["id_pedido"])

def test_sem_nulos_em_campos_obrigatorios(tmp_path):
    main(output_dir=tmp_path)
    df = pd.read_csv(tmp_path / "consolidado.csv")
    assert df["id_pedido"].notna().all()
    assert df["valor_total"].notna().all()
```
