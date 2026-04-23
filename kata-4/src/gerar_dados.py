"""
Kata 4 — Gerador de dados fictícios com problemas intencionais.
Cria os três CSVs de entrada para o pipeline.
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# ─── Dados base ───────────────────────────────────────────────────────────

NOMES = [
    "Ana Souza", "Carlos Lima", "João Pedro", "Maria Oliveira",
    "Pedro Alves", "Lúcia Ferreira", "Bruno Costa", "Fernanda Rocha",
    "Rafael Mendes", "Juliana Santos",
]

# Cidades com grafias propositalmente inconsistentes (problema 5)
CIDADES_PARES = [
    ("São Paulo",   ["São Paulo", "sao paulo", "SAO PAULO", "Sao Paulo", "são paulo"]),
    ("Recife",      ["Recife", "RECIFE", "recife"]),
    ("Caruaru",     ["Caruaru", "caruaru", "CARUARU"]),
    ("Fortaleza",   ["Fortaleza", "fortaleza", "FORTALEZA"]),
    ("Salvador",    ["Salvador", "SALVADOR", "salvador"]),
]

ESTADOS = {
    "São Paulo": "SP", "Recife": "PE", "Caruaru": "PE",
    "Fortaleza": "CE", "Salvador": "BA",
}

STATUSES_PEDIDO   = ["pago", "cancelado", "em_processamento", "pago", "pago"]
STATUSES_ENTREGA  = ["entregue", "entregue", "em_transito", "atrasado", "entregue"]


def rand_date(start: datetime, end: datetime, fmt: str) -> str:
    """Gera data aleatória entre start e end no formato especificado."""
    delta = (end - start).days
    d = start + timedelta(days=random.randint(0, delta))
    return d.strftime(fmt)


def rand_date_mixed(start: datetime, end: datetime) -> str:
    """Gera data em formato misto — problema 1."""
    delta = (end - start).days
    d = start + timedelta(days=random.randint(0, delta))
    fmt = random.choice(["%d/%m/%Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"])
    return d.strftime(fmt)


# ─── clientes.csv ─────────────────────────────────────────────────────────

clientes = []
for i in range(1, 11):
    cidade_base, variantes = random.choice(CIDADES_PARES)
    cidade_escrita = random.choice(variantes)
    clientes.append({
        "id_cliente":     i,
        "nome":           NOMES[i - 1],
        "cidade":         cidade_escrita,
        "estado":         ESTADOS[cidade_base],
        "data_cadastro":  rand_date(datetime(2019, 1, 1), datetime(2022, 12, 31), "%Y-%m-%d"),
    })

with open(DATA_DIR / "clientes.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["id_cliente", "nome", "cidade", "estado", "data_cadastro"])
    w.writeheader()
    w.writerows(clientes)

print(f"✓ clientes.csv  — {len(clientes)} registros")


# ─── pedidos.csv ──────────────────────────────────────────────────────────

pedidos = []
for i in range(1, 31):
    cliente = random.choice(clientes)

    # Problema 2: valores com vírgula como separador decimal em ~30% dos casos
    valor = round(random.uniform(50, 2000), 2)
    if random.random() < 0.3:
        valor_str = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        valor_str = str(valor)

    # Problema 3: ~10% dos registros têm id_cliente nulo
    id_cli = cliente["id_cliente"] if random.random() > 0.1 else ""

    pedidos.append({
        "id_pedido":   i,
        "data_pedido": rand_date_mixed(datetime(2023, 1, 1), datetime(2024, 6, 30)),
        "id_cliente":  id_cli,
        "valor_total": valor_str,
        "status":      random.choice(STATUSES_PEDIDO),
    })

with open(DATA_DIR / "pedidos.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["id_pedido", "data_pedido", "id_cliente", "valor_total", "status"])
    w.writeheader()
    w.writerows(pedidos)

print(f"✓ pedidos.csv   — {len(pedidos)} registros")


# ─── entregas.csv ─────────────────────────────────────────────────────────

# IDs de pedidos válidos
ids_pedidos_validos = [p["id_pedido"] for p in pedidos]

entregas = []
for i in range(1, 36):
    # Problema 4: ~15% dos registros são órfãos (id_pedido inexistente)
    if random.random() < 0.15:
        id_ped = random.randint(900, 999)  # IDs que não existem em pedidos.csv
    else:
        id_ped = random.choice(ids_pedidos_validos)

    data_prev = datetime(2023, 1, 1) + timedelta(days=random.randint(0, 540))
    atraso = random.randint(-5, 15)
    data_real = data_prev + timedelta(days=atraso)

    # ~20% ainda não entregues (data_realizada nula)
    if random.random() < 0.2:
        data_real_str = ""
    else:
        data_real_str = rand_date_mixed(data_real, data_real)

    entregas.append({
        "id_entrega":      i,
        "id_pedido":       id_ped,
        "data_prevista":   data_prev.strftime(random.choice(["%d/%m/%Y", "%Y-%m-%d"])),
        "data_realizada":  data_real_str,
        "status_entrega":  random.choice(STATUSES_ENTREGA),
    })

with open(DATA_DIR / "entregas.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["id_entrega", "id_pedido", "data_prevista", "data_realizada", "status_entrega"])
    w.writeheader()
    w.writerows(entregas)

print(f"✓ entregas.csv  — {len(entregas)} registros ({sum(1 for e in entregas if e['id_pedido'] not in ids_pedidos_validos)} órfãos)")
print(f"\nArquivos gerados em: {DATA_DIR}")
