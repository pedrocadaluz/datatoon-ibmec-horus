"""O instantâneo da hospedagem deve responder igual ao motor com as bases originais."""

import json
import unittest

from api.main import INSTANTANEO
from casa_gemea.config import BASES
from casa_gemea.motor import Motor

RESPOSTAS = [{}, {"obra": "NAO", "vinculo": "PROPRIETARIO_QUITADO", "declaracao_unica": "SIM"},
             {"area_m2": 120, "conteudo": "MAIOR"}, {"obra": "OBRA_ESTRUTURAL"}]


@unittest.skipUnless(all(p.exists() for p in BASES.values()), "bases originais ausentes")
class InstantaneoIgualAoOriginal(unittest.TestCase):
    def test_respostas_identicas_nos_138_imoveis(self):
        original, instantaneo = Motor(), Motor.de_instantaneo(INSTANTANEO)
        self.assertEqual(list(original.casas.index), list(instantaneo.casas.index))
        for imovel in original.casas.index:
            for respostas in RESPOSTAS:
                entrada = {"versao_contrato": "1.0", "imovel_id": imovel, "respostas": respostas}
                with self.subTest(imovel=imovel, respostas=respostas):
                    self.assertEqual(json.dumps(original.recomendar(entrada), sort_keys=True, default=str),
                                     json.dumps(instantaneo.recomendar(entrada), sort_keys=True, default=str))


class InstantaneoSemDadosPessoais(unittest.TestCase):
    def test_instantaneo_sem_idade_renda_nem_endereco(self):
        colunas = set(Motor.de_instantaneo(INSTANTANEO).casas.columns)
        proibidas = {"idade", "renda_mensal", "origem_renda", "confianca_renda", "logradouro", "numero",
                     "complemento", "bairro", "cep_agregado", "latitude_aproximada", "longitude_aproximada"}
        self.assertFalse(colunas & proibidas)


if __name__ == "__main__":
    unittest.main()
