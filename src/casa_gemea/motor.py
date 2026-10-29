"""Contrato JSON do motor: recebe respostas do cliente e devolve a recomendação atualizada.

O mesmo contrato atende todos os canais (app, gerente, SAC e agentes autônomos):
o canal envia o imóvel e as respostas coletadas até agora; o motor atualiza a Casa
Gêmea, refaz elegibilidade, plano, faixas e confiança, e devolve as próximas perguntas.
O motor não guarda estado: cada chamada traz todas as respostas já dadas.

Entrada (exemplo):
    {"versao_contrato": "1.0", "imovel_id": "IMO_CASO_00003_01",
     "respostas": {"obra": "NAO", "vinculo": "PROPRIETARIO_LOCADOR", "area_m2": 150}}

Respostas aceitas (códigos de perguntas.OPCOES; área e bens também aceitam número):
    obra                NAO | REFORMA_PEQUENA | OBRA_ESTRUTURAL
    vinculo             INQUILINO | PROPRIETARIO_FINANCIADO | PROPRIETARIO_QUITADO |
                        PROPRIETARIO_LOCADOR | IMOVEL_VAZIO
    tipo_imovel         APARTAMENTO | CASA | CASA_EM_CONDOMINIO
    ocupacao            OCUPADO | DESOCUPADO
    conteudo            MENOR | NA_FAIXA | MAIOR | NAO_SEI | valor em reais
    area_m2             NA_FAIXA | MENOR | MAIOR | NAO_SEI | área em m²
    padrao_construtivo  ECONOMICO | NORMAL | SUPERIOR | NAO_SEI
    declaracao_unica    SIM | NAO

Guardrail: entrada e saída não têm idade nem renda.
"""

import pickle

import numpy as np
import pandas as pd

from . import perguntas, personalizacao, regras
from .config import ALTA, CONFIRMADO
from .inferencias import _regra_uso
from .pipeline import executar

VERSAO_CONTRATO = "1.0"

CAMPOS_CASA = [
    "tipo_imovel", "vinculo", "uso_imovel", "area_m2", "padrao_construtivo",
    "material_parede", "alerta_obra", "conteudo",
]
FATOR_MENOR, FATOR_MAIOR = 0.7, 1.3  # "menor que a faixa" / "maior que a faixa"
# Perguntas dos adicionais (personalização): SIM confirma o interesse, NAO tira o adicional da lista.
RESPOSTAS_ADICIONAIS = {
    "equipamentos": {"SIM", "NAO", "NAO_SEI"}, "bicicleta": {"SIM", "NAO", "NAO_SEI"},
    "desocupacao": {"SIM", "NAO", "NAO_SEI"}, "mei": {"SIM", "NAO", "NAO_SEI"},
}


class RespostaInvalida(ValueError):
    pass


def _confirmar(r: pd.Series, campo: str, valor, evidencia: str) -> None:
    r[campo] = valor
    r[f"{campo}_selo"] = CONFIRMADO
    r[f"{campo}_confianca"] = ALTA
    r[f"{campo}_evidencia"] = evidencia


def _faixa_relativa(r: pd.Series, resposta: str, chaves: tuple[str, str]) -> tuple[float, float]:
    """Nova faixa (mín, máx) para respostas MENOR / NA_FAIXA / MAIOR."""
    lo, hi = r[chaves[0]], r[chaves[1]]
    return {"MENOR": (lo * FATOR_MENOR, lo), "NA_FAIXA": (lo, hi), "MAIOR": (hi, hi * FATOR_MAIOR)}[resposta]


def aplicar_respostas(r: pd.Series, respostas: dict) -> tuple[pd.Series, list[str]]:
    """Atualiza a Casa Gêmea com as respostas. Devolve a linha nova e os campos respondidos."""
    r = r.copy()
    respondidas = []
    validas = {campo: {cod for cod, _ in ops} for campo, ops in perguntas.OPCOES.items()}
    validas["vinculo"] = validas["vinculo"] | validas["vinculo_locador"]

    for campo, resposta in respostas.items():
        numero = isinstance(resposta, (int, float)) and not isinstance(resposta, bool)
        if campo not in validas:
            raise RespostaInvalida(f"pergunta desconhecida: {campo}")
        if not (numero and campo in ("area_m2", "conteudo")) and resposta not in validas[campo]:
            raise RespostaInvalida(f"resposta inválida para {campo}: {resposta!r}")
        if numero and resposta <= 0:
            raise RespostaInvalida(f"{campo} deve ser positivo")
        respondidas.append(campo)
        if resposta == "NAO_SEI":
            continue  # pergunta feita; a faixa continua larga e a cotação não trava

        if campo == "obra":
            nivel = {"NAO": "SEM_SINAL", "REFORMA_PEQUENA": "REFORMA_LEVE", "OBRA_ESTRUTURAL": "OBRA_ESTRUTURAL"}[resposta]
            _confirmar(r, "alerta_obra", nivel, "informado pelo cliente")
        elif campo == "declaracao_unica":
            if resposta == "SIM":
                _confirmar(r, "material_parede", "ALVENARIA", "declaração do cliente")
            r["declaracao_negada"] = resposta == "NAO"
        elif campo == "vinculo":
            vazio = resposta == "IMOVEL_VAZIO"
            _confirmar(r, "vinculo", "PROPRIETARIO_QUITADO" if vazio else resposta, "informado pelo cliente")
            r["imovel_desocupado"] = vazio
            uso = "TEMPORADA_OU_SEGUNDA_RESIDENCIA" if vazio else _regra_uso(r)[0]
            _confirmar(r, "uso_imovel", uso, "informado pelo cliente")
            if resposta != "PROPRIETARIO_LOCADOR" and r["conteudo_selo"] != CONFIRMADO:
                # A dúvida "bens podem ser do inquilino" deixa de existir.
                r["conteudo_selo"], r["conteudo_confianca"] = "ESTIMADO", "MEDIA"
        elif campo == "tipo_imovel":
            _confirmar(r, "tipo_imovel", resposta, "informado pelo cliente")
        elif campo == "ocupacao":
            r["imovel_desocupado"] = resposta == "DESOCUPADO"
            _confirmar(r, "uso_imovel", r["uso_imovel"], "ocupação informada pelo cliente")
        elif campo == "area_m2":
            lo, hi = (resposta, resposta) if numero else _faixa_relativa(r, resposta, ("area_min_m2", "area_max_m2"))
            r["area_min_m2"], r["area_max_m2"] = round(lo), round(hi)
            _confirmar(r, "area_m2", round(np.sqrt(lo * hi)), "informada pelo cliente")
        elif campo == "padrao_construtivo":
            _confirmar(r, "padrao_construtivo", resposta, "informado pelo cliente")
        elif campo == "conteudo":
            lo, hi = (resposta, resposta) if numero else _faixa_relativa(r, resposta, ("conteudo_min", "conteudo_max"))
            fator = (lo + hi) / (r["conteudo_min"] + r["conteudo_max"])  # eletrônicos acompanham os bens
            r["eletronicos_eletro_min"] *= fator
            r["eletronicos_eletro_max"] *= fator
            r["conteudo_min"], r["conteudo_max"] = round(lo, -2), round(hi, -2)
            _confirmar(r, "conteudo", int(round((lo + hi) / 2, -2)), "informado pelo cliente")
            r["conteudo_estimado"] = r["conteudo"]

    r["eh_casa"] = str(r["tipo_imovel"]).startswith("CASA")
    r["fracao_conteudo_do_cliente"] = regras.interesse_seguravel(r)[2]
    return r, respondidas


def _valor_json(v):
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        return round(float(v), 2)
    if isinstance(v, np.bool_):
        return bool(v)
    return v


class Motor:
    """Carrega o pipeline uma vez e responde chamadas do contrato JSON."""

    def __init__(self, base: str = "teste"):
        res = executar(com_regras=False)
        self.referencias = res.referencias
        self.casas = res.casas[base].set_index("imovel_id", drop=False)
        self.catalogo = res.bases[base]["catalogo_coberturas_fixas_planos"]
        self.coberturas_do_plano = self.catalogo.groupby("plano")["cobertura_fixa"].apply(list).to_dict()

    @classmethod
    def de_instantaneo(cls, caminho) -> "Motor":
        """Sobe o motor sem as bases originais, a partir de scripts/11_gerar_instantaneo_deploy.py."""
        from .calibracao import Calibracao
        with open(caminho, "rb") as f:
            pacote = pickle.load(f)  # arquivo gerado pelo próprio projeto e versionado no repositório
        motor = cls.__new__(cls)
        motor.referencias = regras.carregar_referencias(Calibracao(**pacote["calibracao"]))
        motor.casas = pacote["casas"]
        motor.catalogo = pacote["catalogo"]
        motor.coberturas_do_plano = motor.catalogo.groupby("plano")["cobertura_fixa"].apply(list).to_dict()
        return motor

    def recomendar(self, entrada: dict) -> dict:
        imovel_id = entrada.get("imovel_id")
        if imovel_id not in self.casas.index:
            return {"versao_contrato": VERSAO_CONTRATO, "erro": f"imóvel não encontrado: {imovel_id}"}
        respostas = dict(entrada.get("respostas", {}))
        adicionais_resp = {c: respostas.pop(c) for c in list(respostas) if c in RESPOSTAS_ADICIONAIS}
        try:
            for campo, resposta in adicionais_resp.items():
                if resposta not in RESPOSTAS_ADICIONAIS[campo]:
                    raise RespostaInvalida(f"resposta inválida para {campo}: {resposta!r}")
            r, respondidas = aplicar_respostas(self.casas.loc[imovel_id], respostas)
        except RespostaInvalida as e:
            return {"versao_contrato": VERSAO_CONTRATO, "imovel_id": imovel_id, "erro": str(e)}

        elegibilidade, motivo = regras.avaliar_elegibilidade(r)
        pontuacao = regras.pontuar_plano(r)
        plano = pontuacao["plano_recomendado"] if elegibilidade != regras.INELEGIVEL else ""
        nao_abaixo, nao_acima = regras.comparar_planos(r, pontuacao) if plano else ("", "")
        impacto = perguntas.analisar(r, self.referencias, elegibilidade, frozenset(respondidas))
        cor, canal = regras.semaforo(r, elegibilidade, impacto["confianca_geral"])
        todas = regras.calcular_coberturas(r, self.referencias)
        faixas = [f for f in todas if f["cobertura"] in self.coberturas_do_plano.get(plano, [])] if plano else []

        proximas = impacto["perguntas"] if elegibilidade != regras.INELEGIVEL else []
        if "declaracao_unica" not in respondidas and elegibilidade != regras.INELEGIVEL:
            proximas = proximas + [{"campo": "declaracao_unica", "impacto": "elegibilidade",
                                    "pergunta": perguntas.enunciado("declaracao_unica", r),
                                    "motivo": perguntas.MOTIVO["declaracao_unica"]}]

        if elegibilidade == regras.INELEGIVEL:
            status = "INELEGIVEL"
        elif cor == "VERMELHO":
            status = "ENCAMINHAR_GERENTE"
        elif not proximas:
            status = "RECOMENDACAO_CONFIRMADA"
        else:
            status = "RECOMENDACAO_INICIAL"

        motivos = {"TOTAL": pontuacao["motivos_total"] + pontuacao["motivos_pratico"],
                   "PRATICO": pontuacao["motivos_pratico"]}.get(plano, [])
        pendentes = [p for p in proximas if p["campo"] != "declaracao_unica"]
        feitas = [c for c in respondidas if c != "declaracao_unica"]
        necessarias = min(len(feitas) + len(pendentes), regras.CAMPOS_FORMULARIO_TRADICIONAL)
        evitadas = regras.CAMPOS_FORMULARIO_TRADICIONAL - necessarias
        resumo = "; ".join(motivos[:2]) if motivos else "poucos sinais de necessidade além da proteção básica"
        curta = f"{regras.NOME_PLANO[plano]}: {resumo}." if plano else "Imóvel não elegível sem validação."
        pers = personalizacao.analisar(r, plano, elegibilidade, self.coberturas_do_plano.get(plano, []), adicionais_resp, todas)
        explica = personalizacao.explicacao(r, elegibilidade, motivo, pontuacao, impacto, cor, canal, plano, nao_abaixo, nao_acima)
        return {
            "versao_contrato": VERSAO_CONTRATO,
            "imovel_id": imovel_id,
            "cliente_id": r["cliente_id"],
            "status": status,
            "elegibilidade": {"status": elegibilidade, "motivo": motivo},
            "casa_gemea": {
                campo: {"valor": _valor_json(r["conteudo_estimado" if campo == "conteudo" else campo]),
                        "selo": r[f"{campo}_selo"],
                        "confianca": r[f"{campo}_confianca"], "evidencia": r[f"{campo}_evidencia"]}
                for campo in CAMPOS_CASA
            } | {"area_faixa_m2": [_valor_json(r["area_min_m2"]), _valor_json(r["area_max_m2"])],
                 "conteudo_faixa": [_valor_json(r["conteudo_min"]), _valor_json(r["conteudo_max"])]},
            "recomendacao": {
                "plano": plano,
                "justificativa_curta": curta,
                "confianca_geral": impacto["confianca_geral"],
                "por_que_este_plano": motivos,
                "por_que_nao_plano_abaixo": nao_abaixo,
                "por_que_nao_plano_acima": nao_acima,
                "campos_que_podem_mudar_o_plano": [c for c in impacto["campos_que_mudam_plano"].split("|") if c],
            },
            "coberturas": [
                {"cobertura": f["cobertura"], "faixa_valor_min": f["faixa_valor_min"], "faixa_valor_max": f["faixa_valor_max"],
                 "confianca": f["confianca_estimativa"], "regra": f["regra_calculo_utilizada"],
                 "justificativa": f["justificativa"], "a_confirmar": f["informacao_a_confirmar"], "observacao": f["observacao"]}
                for f in faixas
            ],
            "proximas_perguntas": [
                {"id": p["campo"], "pergunta": perguntas.enunciado(p["campo"], r),
                 "opcoes": [{"valor": v, "rotulo": t} for v, t in perguntas.OPCOES[perguntas.chave_opcoes(p["campo"], r)]],
                 "aceita_numero": p["campo"] in ("area_m2", "conteudo"),
                 "impacto": p["impacto"], "motivo": p["motivo"]}
                for p in proximas
            ],
            "jornada": {
                "campos_formulario_tradicional": regras.CAMPOS_FORMULARIO_TRADICIONAL,
                "perguntas_necessarias": necessarias,
                "perguntas_evitadas": evitadas,
                "percentual_evitado": round(100 * evitadas / regras.CAMPOS_FORMULARIO_TRADICIONAL),
            },
            "canal": {"semaforo": cor, "sugerido": canal},
            "comparacao_planos": personalizacao.comparacao_planos(r, pontuacao, plano, todas, self.coberturas_do_plano, pers["necessidades"]),
            "personalizacao": pers,
            "explicacao": explica,
            "respostas_aplicadas": respondidas + list(adicionais_resp),
        }
