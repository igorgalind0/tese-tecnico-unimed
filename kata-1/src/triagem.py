"""
Kata 1 — Fila de Triagem
========================
Sistema de ordenação de fila de atendimento em clínica médica
com regras de prioridade por urgência, idade e FIFO.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import List


# ---------------------------------------------------------------------------
# Domínio
# ---------------------------------------------------------------------------

class Urgencia(IntEnum):
    """
    Representa os níveis de urgência ordenados numericamente.
    Valores maiores = maior prioridade (facilita comparação direta).
    """
    BAIXA   = 1
    MEDIA   = 2
    ALTA    = 3
    CRITICA = 4


@dataclass
class Paciente:
    nome: str
    idade: int
    urgencia: Urgencia
    horario_chegada: str  # formato "HH:MM"

    # campo calculado após aplicar regras; não passado pelo usuário
    urgencia_efetiva: Urgencia = field(init=False)

    def __post_init__(self):
        self.urgencia_efetiva = self.urgencia

    @property
    def chegada_dt(self) -> datetime:
        """Converte HH:MM em datetime para comparação FIFO."""
        return datetime.strptime(self.horario_chegada, "%H:%M")


# ---------------------------------------------------------------------------
# Motor de regras
# ---------------------------------------------------------------------------

def _aplicar_regra_idoso(paciente: Paciente) -> None:
    """
    Regra 4: Pacientes com 60+ anos e urgência MÉDIA sobem para ALTA.
    Aplica-se sobre a urgência ORIGINAL do paciente.
    """
    if paciente.idade >= 60 and paciente.urgencia == Urgencia.MEDIA:
        paciente.urgencia_efetiva = max(paciente.urgencia_efetiva, Urgencia.ALTA)


def _aplicar_regra_menor(paciente: Paciente) -> None:
    """
    Regra 5: Pacientes com menos de 18 anos ganham +1 nível de prioridade,
    limitado ao teto CRÍTICA.
    """
    if paciente.idade < 18:
        novo_nivel = min(paciente.urgencia_efetiva.value + 1, Urgencia.CRITICA.value)
        paciente.urgencia_efetiva = Urgencia(novo_nivel)


# Lista de regras aplicáveis em ordem. Adicionar uma 6ª regra = adicionar
# uma função aqui. Nenhum outro código precisa mudar.
_REGRAS = [
    _aplicar_regra_idoso,
    _aplicar_regra_menor,
]


def aplicar_regras(paciente: Paciente) -> None:
    """Aplica todas as regras de ajuste de prioridade sobre um paciente."""
    # Reseta urgência efetiva antes de reaplicar (idempotência)
    paciente.urgencia_efetiva = paciente.urgencia
    for regra in _REGRAS:
        regra(paciente)


# ---------------------------------------------------------------------------
# Ordenação da fila
# ---------------------------------------------------------------------------

def ordenar_fila(pacientes: List[Paciente]) -> List[Paciente]:
    """
    Recebe uma lista de pacientes, aplica as regras de negócio e
    retorna a fila ordenada do primeiro a ser atendido ao último.

    Critério primário : urgência_efetiva (maior = primeiro)
    Critério secundário: horário de chegada (menor = primeiro — FIFO)

    Complexidade: O(n log n) — Python usa Timsort, estável por padrão,
    o que preserva a ordem original em caso de empate total.
    """
    for p in pacientes:
        aplicar_regras(p)

    return sorted(
        pacientes,
        key=lambda p: (-p.urgencia_efetiva.value, p.chegada_dt),
    )


# ---------------------------------------------------------------------------
# Demo rápida
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pacientes = [
        Paciente("Ana Souza",      35, Urgencia.MEDIA,   "08:00"),
        Paciente("Carlos Lima",    72, Urgencia.MEDIA,   "08:05"),  # R4: MEDIA→ALTA
        Paciente("João Pedro",     15, Urgencia.MEDIA,   "08:10"),  # R5: MEDIA→ALTA
        Paciente("Maria Oliveira", 15, Urgencia.MEDIA,   "08:15"),  # R4 não se aplica; R5: MEDIA→ALTA
        Paciente("Pedro Alves",    45, Urgencia.CRITICA, "07:50"),  # Topo absoluto
        Paciente("Lúcia Ferreira", 68, Urgencia.BAIXA,  "07:45"),  # R4 não se aplica (não é MEDIA)
        Paciente("Bruno Costa",    10, Urgencia.ALTA,   "08:20"),  # R5: ALTA→CRITICA
    ]

    fila = ordenar_fila(pacientes)

    print(f"{'Pos':<4} {'Nome':<20} {'Idade':<6} {'Urgência orig.':<15} "
          f"{'Urgência efet.':<15} {'Chegada'}")
    print("-" * 75)
    for i, p in enumerate(fila, 1):
        print(
            f"{i:<4} {p.nome:<20} {p.idade:<6} "
            f"{p.urgencia.name:<15} {p.urgencia_efetiva.name:<15} {p.horario_chegada}"
        )
