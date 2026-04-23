"""
Kata 4 — Pipeline de Relatório
================================
Lê pedidos.csv, clientes.csv e entregas.csv,
aplica limpezas/normalizações e gera:
  - output/consolidado.csv
  - output/indicadores.json
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

# ─── Configuração de caminhos ─────────────────────────────────────────────

BASE_DIR   = Path(__file__).parent.parent
DATA_DIR   = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

CONSOLIDADO_PATH  = OUTPUT_DIR / "consolidado.csv"
INDICADORES_PATH  = OUTPUT_DIR / "indicadores.json"


# ─── Helpers de limpeza ───────────────────────────────────────────────────

_DATE_FORMATS = [
    "%d/%m/%Y",
    "%Y-%m-%d",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
]

def parse_date(value: str) -> Optional[datetime]:
    """
    Tenta parsear uma data em múltiplos formatos.
    Retorna None se não for possível — nunca levanta exceção.
    """
    if not value or not str(value).strip():
        return None
    value = str(value).strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def parse_valor(value: str) -> Optional[float]:
    """
    Normaliza valores monetários com vírgula ou ponto como decimal.
    Exemplos suportados: '1.250,99' → 1250.99 | '1250.99' → 1250.99
    """
    if not value or not str(value).strip():
        return None
    s = str(value).strip()
    # Se contém vírgula E ponto: formato europeu (1.250,99)
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    # Se contém só vírgula: decimal brasileiro (1250,99)
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def normalizar_cidade(cidade: str) -> str:
    """
    Normaliza nomes de cidades:
    1. Remove acentos
    2. Converte para Title Case
    3. Remove espaços extras

    Exemplos:
        'sao paulo' → 'Sao Paulo'
        'SAO PAULO' → 'Sao Paulo'
        'são paulo' → 'Sao Paulo'
    """
    if not cidade or not str(cidade).strip():
        return ""
    # Remove acentos via NFD
    sem_acento = unicodedata.normalize("NFD", str(cidade).strip())
    sem_acento = "".join(c for c in sem_acento if unicodedata.category(c) != "Mn")
    return " ".join(sem_acento.title().split())


# ─── Etapas do pipeline ───────────────────────────────────────────────────

def carregar_e_limpar_pedidos() -> pd.DataFrame:
    print("  [1/5] Carregando pedidos.csv...")
    df = pd.read_csv(DATA_DIR / "pedidos.csv", dtype=str)

    total = len(df)

    # Normalizar datas
    df["data_pedido_dt"] = df["data_pedido"].apply(parse_date)

    # Normalizar valores
    df["valor_total_num"] = df["valor_total"].apply(parse_valor)

    # Remover registros com id_cliente nulo (campo obrigatório)
    nulos_cliente = df["id_cliente"].isna() | (df["id_cliente"].str.strip() == "")
    df_limpo = df[~nulos_cliente].copy()

    # Remover registros com valor nulo
    nulos_valor = df_limpo["valor_total_num"].isna()
    df_limpo = df_limpo[~nulos_valor].copy()

    # Converter id_cliente para int
    df_limpo["id_cliente"] = df_limpo["id_cliente"].astype(float).astype(int)
    df_limpo["id_pedido"]  = df_limpo["id_pedido"].astype(int)

    descartados = total - len(df_limpo)
    print(f"     {total} lidos → {len(df_limpo)} válidos ({descartados} descartados por nulos obrigatórios)")
    return df_limpo


def carregar_e_limpar_clientes() -> pd.DataFrame:
    print("  [2/5] Carregando clientes.csv...")
    df = pd.read_csv(DATA_DIR / "clientes.csv", dtype=str)

    df["id_cliente"]        = df["id_cliente"].astype(int)
    df["cidade_normalizada"] = df["cidade"].apply(normalizar_cidade)

    print(f"     {len(df)} clientes carregados")
    return df


def carregar_e_limpar_entregas() -> pd.DataFrame:
    print("  [3/5] Carregando entregas.csv...")
    df = pd.read_csv(DATA_DIR / "entregas.csv", dtype=str)

    df["id_pedido"]         = df["id_pedido"].astype(float).astype(int)
    df["data_prevista_dt"]  = df["data_prevista"].apply(parse_date)
    df["data_realizada_dt"] = df["data_realizada"].apply(parse_date)

    print(f"     {len(df)} entregas carregadas")
    return df


def consolidar(pedidos: pd.DataFrame, clientes: pd.DataFrame, entregas: pd.DataFrame) -> pd.DataFrame:
    print("  [4/5] Consolidando e calculando atraso_dias...")

    # JOIN pedidos + clientes
    df = pedidos.merge(clientes[["id_cliente", "nome", "cidade_normalizada", "estado"]],
                       on="id_cliente", how="left")

    # JOIN com entregas — LEFT JOIN: pedidos sem entrega ficam com NaN
    # Registros órfãos de entregas.csv são automaticamente excluídos aqui
    df = df.merge(
        entregas[["id_pedido", "data_prevista_dt", "data_realizada_dt", "status_entrega"]],
        on="id_pedido", how="left"
    )

    # Calcular atraso_dias
    def calc_atraso(row) -> Optional[float]:
        if pd.isna(row["data_realizada_dt"]) or pd.isna(row["data_prevista_dt"]):
            return None
        delta = row["data_realizada_dt"] - row["data_prevista_dt"]
        return delta.days

    df["atraso_dias"] = df.apply(calc_atraso, axis=1)

    # Selecionar e renomear colunas finais
    resultado = df[[
        "id_pedido",
        "nome",
        "cidade_normalizada",
        "estado",
        "valor_total_num",
        "status",
        "data_pedido_dt",
        "data_prevista_dt",
        "data_realizada_dt",
        "atraso_dias",
        "status_entrega",
    ]].rename(columns={
        "nome":           "nome_cliente",
        "valor_total_num": "valor_total",
        "status":          "status_pedido",
        "data_pedido_dt":  "data_pedido",
        "data_prevista_dt": "data_prevista_entrega",
        "data_realizada_dt": "data_realizada_entrega",
    })

    # Formatar datas para string legível no CSV
    for col in ["data_pedido", "data_prevista_entrega", "data_realizada_entrega"]:
        resultado[col] = resultado[col].apply(
            lambda d: d.strftime("%Y-%m-%d") if pd.notna(d) else ""
        )

    print(f"     {len(resultado)} pedidos consolidados")
    return resultado


def calcular_indicadores(df: pd.DataFrame) -> dict:
    print("  [5/5] Calculando indicadores...")

    # Pedidos com entrega registrada
    com_entrega = df[df["data_realizada_entrega"] != ""].copy()
    com_entrega["atraso_dias"] = pd.to_numeric(com_entrega["atraso_dias"], errors="coerce")

    total_com_entrega = len(com_entrega)
    no_prazo  = len(com_entrega[com_entrega["atraso_dias"] <= 0])
    atrasados = len(com_entrega[com_entrega["atraso_dias"] > 0])

    pct_prazo   = round(no_prazo  / total_com_entrega * 100, 1) if total_com_entrega else 0
    pct_atraso  = round(atrasados / total_com_entrega * 100, 1) if total_com_entrega else 0

    # Média de atraso (apenas pedidos com atraso > 0)
    so_atrasados = com_entrega[com_entrega["atraso_dias"] > 0]["atraso_dias"]
    media_atraso = round(float(so_atrasados.mean()), 1) if len(so_atrasados) else 0

    # Top 3 cidades
    top3_cidades = (
        df.groupby("cidade_normalizada")["id_pedido"]
        .count()
        .sort_values(ascending=False)
        .head(3)
        .to_dict()
    )

    # Ticket médio por estado
    ticket_por_estado = (
        df.groupby("estado")["valor_total"]
        .mean()
        .round(2)
        .to_dict()
    )

    # Total por status de pedido
    por_status = df["status_pedido"].value_counts().to_dict()

    indicadores = {
        "total_pedidos_por_status":        por_status,
        "ticket_medio_por_estado":         ticket_por_estado,
        "entregas_no_prazo_pct":           pct_prazo,
        "entregas_com_atraso_pct":         pct_atraso,
        "top3_cidades_volume_pedidos":     top3_cidades,
        "media_atraso_dias_pedidos_atrasados": media_atraso,
    }
    return indicadores


# ─── Execução principal ───────────────────────────────────────────────────

def main():
    print("\n🚀 Pipeline de Relatório — Kata 4\n" + "="*40)

    pedidos  = carregar_e_limpar_pedidos()
    clientes = carregar_e_limpar_clientes()
    entregas = carregar_e_limpar_entregas()

    consolidado = consolidar(pedidos, clientes, entregas)

    # Salvar consolidado
    consolidado.to_csv(CONSOLIDADO_PATH, index=False, encoding="utf-8")
    print(f"\n✅ Consolidado salvo em: {CONSOLIDADO_PATH}")

    # Calcular e salvar indicadores
    indicadores = calcular_indicadores(consolidado)
    with open(INDICADORES_PATH, "w", encoding="utf-8") as f:
        json.dump(indicadores, f, ensure_ascii=False, indent=2)
    print(f"✅ Indicadores salvos em: {INDICADORES_PATH}")

    # Exibir resumo no terminal
    print("\n" + "="*40)
    print("📊 INDICADORES CONSOLIDADOS")
    print("="*40)
    print(json.dumps(indicadores, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
