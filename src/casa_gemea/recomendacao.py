"""Recomendação completa por imóvel: junta regras do seguro, análise de impacto e personalização."""

import pandas as pd

from . import perguntas, personalizacao, regras
from .config import BAIXA


def _texto_adicionais(adicionais: list[dict]) -> str:
    """Adicionais em uma frase cada; os sem faixa dizem por que não têm linha no detalhamento."""
    partes = []
    for ad in adicionais:
        sem_faixa = "" if "faixa_valor_min" in ad else             " Sem linha de faixa: não tem limite próprio ou depende de declaração do cliente."
        partes.append(f"{ad['nome']} ({ad['clausula']}): {ad['por_que_para_voce']}{sem_faixa}")
    return " ".join(partes)


def _texto_assistencias(r: pd.Series, plano: str) -> str:
    if not plano:
        return ""
    assist = personalizacao.assistencias(r, plano)
    texto = ", ".join(personalizacao.PACOTES_ASSISTENCIA[plano])
    if assist["destaque"]:
        texto += "; em destaque para este cliente: " + "; ".join(f"{d['nome']}, {d['por_que']}" for d in assist["destaque"])
    return texto


def recomendar(casa: pd.DataFrame, ref: regras.Referencias, catalogo: pd.DataFrame):
    """Aplica todas as regras. Devolve (uma linha por imóvel, uma linha por cobertura)."""
    coberturas_do_plano = catalogo.groupby("plano")["cobertura_fixa"].apply(list).to_dict()
    casa = casa.copy()
    casa["fracao_conteudo_do_cliente"] = casa.apply(lambda r: regras.interesse_seguravel(r)[2], axis=1)

    linhas, coberturas = [], []
    for _, r in casa.iterrows():
        elegibilidade, motivo = regras.avaliar_elegibilidade(r)
        pontuacao = regras.pontuar_plano(r)
        plano = pontuacao["plano_recomendado"] if elegibilidade != regras.INELEGIVEL else ""
        nao_abaixo, nao_acima = regras.comparar_planos(r, pontuacao) if plano else ("", "")
        impacto = perguntas.analisar(r, ref, elegibilidade)
        cor, canal = regras.semaforo(r, elegibilidade, impacto["confianca_geral"])

        faixas = regras.calcular_coberturas(r, ref) if plano else []
        do_plano = [f for f in faixas if f["cobertura"] in coberturas_do_plano.get(plano, [])]
        for f in do_plano:
            coberturas.append({"cliente_id": r["cliente_id"], "imovel_id": r["imovel_id"], **f})

        # Adicionais opcionais (CG 4.1): os dimensionáveis ganham linha própria no detalhamento.
        adicionais = personalizacao.adicionais(r, plano, elegibilidade)
        for ad in adicionais:
            if "faixa_valor_min" in ad:
                coberturas.append({
                    "cliente_id": r["cliente_id"], "imovel_id": r["imovel_id"], "cobertura": ad["id"],
                    "faixa_valor_min": ad["faixa_valor_min"], "faixa_valor_max": ad["faixa_valor_max"],
                    "confianca_estimativa": BAIXA,  # faixa por premissa; itens confirmados na contratação
                    "dados_utilizados": ad["dados_usados"],
                    "regra_calculo_utilizada": ad["regra_da_faixa"],
                    "justificativa": f"Cobertura adicional opcional, paga à parte ({ad['clausula']}). {ad['por_que_para_voce']}",
                    "informacao_a_confirmar": ad["pergunta"] or "",
                    "observacao": ad["cuidado"],
                })

        linhas.append({
            "cliente_id": r["cliente_id"],
            "imovel_id": r["imovel_id"],
            "elegivel": elegibilidade,
            "motivo_inelegibilidade": motivo,
            "plano_recomendado": plano,
            "coberturas_recomendadas": "|".join([f["cobertura"] for f in do_plano]
                                                + [ad["id"] for ad in adicionais if "faixa_valor_min" in ad]),
            "adicionais_sugeridos": _texto_adicionais(adicionais),
            "assistencias_do_plano": _texto_assistencias(r, plano),
            "confianca_geral": impacto["confianca_geral"],
            "pontos_pratico": pontuacao["pontos_pratico"],
            "pontos_total": pontuacao["pontos_total"],
            "motivos_plano": "; ".join(
                {"TOTAL": pontuacao["motivos_total"] + pontuacao["motivos_pratico"],
                 "PRATICO": pontuacao["motivos_pratico"]}.get(plano, [])
            ),
            "por_que_nao_plano_abaixo": nao_abaixo,
            "por_que_nao_plano_acima": nao_acima,
            "campos_que_mudam_plano": impacto["campos_que_mudam_plano"],
            "qtd_perguntas": impacto["qtd_perguntas"],
            "qtd_perguntas_evitadas": regras.CAMPOS_FORMULARIO_TRADICIONAL - impacto["qtd_perguntas"],
            "perguntas_confirmacao": perguntas.texto_perguntas(impacto["perguntas"]),
            "semaforo": cor,
            "canal_sugerido": canal,
        })
    return pd.DataFrame(linhas), pd.DataFrame(coberturas)
