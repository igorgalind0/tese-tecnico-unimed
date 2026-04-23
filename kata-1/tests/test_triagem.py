"""
Testes unitários — Kata 1: Fila de Triagem
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from triagem import Paciente, Urgencia, ordenar_fila, aplicar_regras


class TestRegra4Idoso(unittest.TestCase):
    """Regra 4: pacientes 60+ com MÉDIA sobem para ALTA."""

    def test_idoso_media_sobe_para_alta(self):
        p = Paciente("Dona Maria", 60, Urgencia.MEDIA, "08:00")
        aplicar_regras(p)
        self.assertEqual(p.urgencia_efetiva, Urgencia.ALTA)

    def test_idoso_media_nao_ultrapassa_critica(self):
        """Regra 4 apenas sobe MEDIA → ALTA. CRITICA já estava no topo."""
        p = Paciente("Sr. José", 70, Urgencia.CRITICA, "08:00")
        aplicar_regras(p)
        self.assertEqual(p.urgencia_efetiva, Urgencia.CRITICA)

    def test_idoso_baixa_nao_muda(self):
        """Regra 4 só age sobre MÉDIA — BAIXA não deve ser afetada."""
        p = Paciente("Sr. Antônio", 65, Urgencia.BAIXA, "08:00")
        aplicar_regras(p)
        self.assertEqual(p.urgencia_efetiva, Urgencia.BAIXA)

    def test_adulto_59_media_nao_muda(self):
        """Limite exato de idade: 59 anos NÃO é idoso."""
        p = Paciente("Paulo", 59, Urgencia.MEDIA, "08:00")
        aplicar_regras(p)
        self.assertEqual(p.urgencia_efetiva, Urgencia.MEDIA)


class TestRegra5Menor(unittest.TestCase):
    """Regra 5: menores de 18 anos ganham +1 nível."""

    def test_menor_baixa_sobe_para_media(self):
        p = Paciente("Lucas", 10, Urgencia.BAIXA, "08:00")
        aplicar_regras(p)
        self.assertEqual(p.urgencia_efetiva, Urgencia.MEDIA)

    def test_menor_media_sobe_para_alta(self):
        p = Paciente("Bia", 14, Urgencia.MEDIA, "08:00")
        aplicar_regras(p)
        self.assertEqual(p.urgencia_efetiva, Urgencia.ALTA)

    def test_menor_alta_sobe_para_critica(self):
        p = Paciente("Theo", 16, Urgencia.ALTA, "08:00")
        aplicar_regras(p)
        self.assertEqual(p.urgencia_efetiva, Urgencia.CRITICA)

    def test_menor_critica_permanece_critica(self):
        """Não existe nível acima de CRÍTICA — deve permanecer."""
        p = Paciente("Sara", 5, Urgencia.CRITICA, "08:00")
        aplicar_regras(p)
        self.assertEqual(p.urgencia_efetiva, Urgencia.CRITICA)

    def test_adulto_18_nao_afetado(self):
        """Exato 18 anos não é menor de idade."""
        p = Paciente("Carla", 18, Urgencia.BAIXA, "08:00")
        aplicar_regras(p)
        self.assertEqual(p.urgencia_efetiva, Urgencia.BAIXA)


class TestInteracaoRegras4e5(unittest.TestCase):
    """
    Interação entre R4 e R5.
    Regras são aplicadas em sequência: primeiro R4, depois R5.
    """

    def test_menor_15_urgencia_media(self):
        """
        Caso do enunciado: 15 anos + MÉDIA.
        R4 NÃO se aplica (não é idoso).
        R5 aplica: MÉDIA → ALTA.
        Resultado esperado: ALTA.
        """
        p = Paciente("João", 15, Urgencia.MEDIA, "08:00")
        aplicar_regras(p)
        self.assertEqual(p.urgencia_efetiva, Urgencia.ALTA)

    def test_idoso_menor_impossivel_mas_hipoteticamente(self):
        """
        Cenário teórico: paciente 15 anos + idoso não existe,
        mas garantimos que a cadeia de regras é estável.
        Aqui testamos um adulto normal para isolar R4 e R5.
        """
        p = Paciente("Adulto normal", 40, Urgencia.MEDIA, "08:00")
        aplicar_regras(p)
        self.assertEqual(p.urgencia_efetiva, Urgencia.MEDIA)

    def test_menor_baixa_regra5_e_sem_interferencia_r4(self):
        """
        Paciente 10 anos, BAIXA. R4 não interfere. R5: BAIXA → MEDIA.
        """
        p = Paciente("Criança", 10, Urgencia.BAIXA, "08:00")
        aplicar_regras(p)
        self.assertEqual(p.urgencia_efetiva, Urgencia.MEDIA)


class TestOrdenacaoFila(unittest.TestCase):
    """Testa a ordenação completa da fila."""

    def _make(self, nome, idade, urgencia, chegada):
        return Paciente(nome, idade, Urgencia[urgencia], chegada)

    def test_critica_sempre_primeiro(self):
        pacientes = [
            self._make("A", 30, "BAIXA",   "07:00"),
            self._make("B", 30, "ALTA",    "07:01"),
            self._make("C", 30, "CRITICA", "07:59"),  # chegou depois, mas CRÍTICA
        ]
        fila = ordenar_fila(pacientes)
        self.assertEqual(fila[0].nome, "C")

    def test_fifo_dentro_do_mesmo_nivel(self):
        pacientes = [
            self._make("Segundo", 30, "ALTA", "09:00"),
            self._make("Primeiro", 30, "ALTA", "08:00"),
        ]
        fila = ordenar_fila(pacientes)
        self.assertEqual(fila[0].nome, "Primeiro")
        self.assertEqual(fila[1].nome, "Segundo")

    def test_ordenacao_completa_com_regras(self):
        """
        Fila mista com várias regras ativas.
        Esperado: CRITICA > ALTA (incluindo promovidos) > MEDIA > BAIXA.
        """
        pacientes = [
            self._make("AnaMedia35",    35, "MEDIA",   "08:00"),
            self._make("CarlosIdoso72", 72, "MEDIA",   "08:05"),  # R4 → ALTA
            self._make("JoaoPedro15",   15, "MEDIA",   "08:10"),  # R5 → ALTA
            self._make("PedroAltaCrit", 45, "CRITICA", "07:50"),
            self._make("BrunoMenorAlt", 10, "ALTA",    "08:20"),  # R5 → CRITICA
        ]
        fila = ordenar_fila(pacientes)

        # posição 0 e 1 devem ser os CRITICA (PedroAltaCrit e BrunoMenorAlt)
        criticos = {p.nome for p in fila[:2]}
        self.assertIn("PedroAltaCrit", criticos)
        self.assertIn("BrunoMenorAlt", criticos)

        # dentro dos CRITICA, PedroAltaCrit chegou primeiro
        self.assertEqual(fila[0].nome, "PedroAltaCrit")

        # os ALTA promovidos vêm depois dos CRITICA
        altas = {p.nome for p in fila[2:4]}
        self.assertIn("CarlosIdoso72", altas)
        self.assertIn("JoaoPedro15", altas)

        # MEDIA original no fim
        self.assertEqual(fila[4].nome, "AnaMedia35")

    def test_lista_vazia(self):
        self.assertEqual(ordenar_fila([]), [])

    def test_paciente_unico(self):
        p = self._make("Único", 30, "ALTA", "10:00")
        self.assertEqual(ordenar_fila([p]), [p])


if __name__ == "__main__":
    unittest.main(verbosity=2)
