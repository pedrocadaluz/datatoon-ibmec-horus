"""Testes do limite HTTP, privacidade e paridade com a entrega oficial."""

import csv
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from api.main import app

RAIZ = Path(__file__).resolve().parents[1]


class ContratoHTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = TestClient(app)
        cls.client = cls.context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.context.__exit__(None, None, None)

    def recomendar(self, imovel="IMO_CASO_00003_01", respostas=None):
        return self.client.post("/api/recomendar", json={"versao_contrato": "1.0", "imovel_id": imovel, "respostas": respostas or {}})

    def test_lista_so_expoe_identificadores_e_localidade(self):
        data = self.client.get("/api/imoveis").json()
        self.assertEqual(len(data["imoveis"]), 138)
        for imovel in data["imoveis"]:
            self.assertEqual(set(imovel), {"imovel_id", "cliente_id", "municipio", "uf"})

    def test_recomendacoes_e_faixas_iguais_a_entrega_sem_respostas(self):
        with (RAIZ / "entrega/template_coberturas_times.csv").open(encoding="utf-8-sig") as f:
            faixas = {(r["imovel_id"], r["cobertura"]): r for r in csv.DictReader(f)}
        with (RAIZ / "entrega/template_resultado_times.csv").open(encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                with self.subTest(imovel=row["imovel_id"]):
                    result = self.recomendar(row["imovel_id"])
                    self.assertEqual(result.status_code, 200)
                    data = result.json()
                    self.assertEqual(data["recomendacao"]["plano"], row["plano_recomendado"])
                    self.assertEqual(data["recomendacao"]["confianca_geral"], row["confianca_geral"])
                    self.assertEqual(data["elegibilidade"]["status"], {"SIM": "ELEGIVEL", "PENDENTE_VALIDACAO": "ELEGIVEL_CONDICIONADO", "NAO": "INELEGIVEL"}[row["elegivel"]])
                    # Na entrega, os adicionais com faixa vêm depois das coberturas fixas do plano.
                    # RC familiar opcional (fora do Total) aparece só na interface, não nos CSVs da entrega.
                    adicionais = [a for a in data["personalizacao"]["adicionais_sugeridos"]
                                  if "faixa_valor_min" in a and a["id"] != "RESPONSABILIDADE_CIVIL_FAMILIAR"]
                    detalhadas = data["coberturas"] + [{"cobertura": a["id"], **a} for a in adicionais]
                    self.assertEqual({c["cobertura"] for c in detalhadas}, set(row["coberturas_recomendadas"].split(" | ")) - {""})
                    for cobertura in detalhadas:
                        original = faixas[row["imovel_id"], cobertura["cobertura"]]
                        for campo in ("faixa_valor_min", "faixa_valor_max"):
                            self.assertEqual(cobertura[campo], float(original[campo]))

    def test_jornada_muda_total_para_pratico_e_estreita_faixa(self):
        respostas = {"obra": "NAO", "vinculo": "PROPRIETARIO_QUITADO", "area_m2": 160, "declaracao_unica": "SIM"}
        data = self.recomendar(respostas=respostas).json()
        self.assertEqual(data["status"], "RECOMENDACAO_CONFIRMADA")
        self.assertEqual(data["recomendacao"]["plano"], "PRATICO")
        self.assertEqual(data["coberturas"][0]["faixa_valor_min"], 505300)
        self.assertEqual(data["coberturas"][0]["faixa_valor_max"], 633500)

    def test_obra_estrutural_nao_oferece_plano(self):
        data = self.recomendar(respostas={"obra": "OBRA_ESTRUTURAL"}).json()
        self.assertEqual(data["status"], "INELEGIVEL")
        self.assertEqual(data["coberturas"], [])

    def test_nao_sei_sai_da_fila_sem_confirmar_o_dado(self):
        data = self.recomendar(respostas={"obra": "NAO_SEI"}).json()
        self.assertNotIn("obra", [q["id"] for q in data["proximas_perguntas"]])
        self.assertEqual(data["casa_gemea"]["alerta_obra"]["selo"], "A_CONFIRMAR")

    def test_entrada_invalida_nao_derruba_servidor(self):
        for valor in ([], {}, True, -1, 0, 0.1):
            with self.subTest(valor=valor):
                self.assertEqual(self.recomendar(respostas={"area_m2": valor}).status_code, 422)
        self.assertEqual(self.recomendar(respostas={"obra": "INVALIDO"}).status_code, 422)
        self.assertEqual(self.recomendar("INEXISTENTE").status_code, 404)
        self.assertEqual(self.client.post("/api/recomendar", json={"imovel_id": "IMO_CASO_00003_01", "versao_contrato": "2.0"}).status_code, 422)

    def test_valores_extremos_recebem_erro_de_entrada(self):
        for campo in ("area_m2", "conteudo"):
            with self.subTest(campo=campo):
                self.assertEqual(self.recomendar(respostas={campo: 1e308}).status_code, 422)

    def test_sinais_gerente_nao_expoem_perfil(self):
        data = self.client.get("/api/imoveis/IMO_CASO_00003_01/sinais").json()
        self.assertEqual(set(data), {"inconsistencias"})
        self.assertIsInstance(data["inconsistencias"], list)

    def test_api_nao_armazena_resultados_em_cache(self):
        self.assertEqual(self.recomendar().headers.get("cache-control"), "no-store")
        self.assertEqual(self.client.get("/api/imoveis").headers.get("cache-control"), "no-store")

    def test_cors_local_explicito_e_origem_externa_negada(self):
        permitida = self.client.options("/api/recomendar", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"})
        self.assertEqual(permitida.headers.get("access-control-allow-origin"), "http://localhost:5173")
        negada = self.client.options("/api/recomendar", headers={"Origin": "https://externo.invalid", "Access-Control-Request-Method": "POST"})
        self.assertNotIn("access-control-allow-origin", negada.headers)


if __name__ == "__main__":
    unittest.main()
