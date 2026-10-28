"""Validação das faixas escondendo dados reais (base de desenvolvimento).

Para os imóveis com área cadastrada, o motor roda duas vezes:
- **real**: com a área e o padrão construtivo cadastrados;
- **escondido**: como se a área e o padrão não existissem.

Pergunta respondida: a faixa calculada sem os dados contém o valor calculado com eles?

Para não usar o próprio imóvel no treino, o modelo de área e a calibração são refeitos
em validação cruzada (5 dobras): cada imóvel é avaliado por um modelo que não o viu.
"""

import numpy as np
import pandas as pd

from . import area, regras
from .calibracao import calibrar
from .carregar import ler_base, montar_tabela_imoveis
from .inferencias import construir_casa_gemea, inferir_tipo

COBERTURAS_VALIDADAS = [
    "INCENDIO_RAIO_EXPLOSAO_FUMACA", "DANOS_POR_AGUA", "VENDAVAL_GRANIZO",
    "IMPACTO_VEICULOS_TERRESTRES", "QUEDA_AERONAVE", "QUEBRA_DE_VIDROS",
]


def _faixas(casa: pd.DataFrame, ref: regras.Referencias) -> pd.DataFrame:
    casa = casa.copy()
    casa["fracao_conteudo_do_cliente"] = casa.apply(lambda r: regras.interesse_seguravel(r)[2], axis=1)
    linhas = []
    for _, r in casa.iterrows():
        for f in regras.calcular_coberturas(r, ref):
            if f["cobertura"] in COBERTURAS_VALIDADAS:
                linhas.append({"imovel_id": r["imovel_id"], "padrao_cadastrado": r["padrao_construtivo_cadastrado"], **f})
    return pd.DataFrame(linhas)


def validar(n_folds: int = 5, semente: int = 42) -> pd.DataFrame:
    """Uma linha por imóvel × cobertura, com a faixa escondida e o valor real."""
    tabela = montar_tabela_imoveis(ler_base("desenvolvimento"))
    com_area = tabela.index[tabela["area_cadastrada_m2"] > 0]
    dobra = pd.Series(np.random.default_rng(semente).integers(0, n_folds, len(com_area)), index=com_area)

    # Referência "real": modelo e calibração completos, dados cadastrados.
    modelo_total, calib_total = area.treinar(inferir_tipo(tabela)), calibrar(tabela)
    ref_total = regras.carregar_referencias(calib_total)
    real = _faixas(construir_casa_gemea(tabela.loc[com_area], modelo_total, calib_total), ref_total)

    escondidas = []
    for k in range(n_folds):
        avaliados = dobra.index[dobra == k]
        treino = tabela.copy()
        treino.loc[avaliados, "area_cadastrada_m2"] = 0
        modelo, calib = area.treinar(inferir_tipo(treino)), calibrar(treino)

        oculto = tabela.loc[avaliados].copy()
        oculto["area_cadastrada_m2"] = 0
        oculto["padrao_construtivo_cadastrado"] = "NAO_DISPONIVEL"
        escondidas.append(_faixas(construir_casa_gemea(oculto, modelo, calib), regras.carregar_referencias(calib)))

    escondido = pd.concat(escondidas)
    m = escondido.merge(real, on=["imovel_id", "cobertura"], suffixes=("", "_real"))
    # Valor de referência: centro (geométrico) da faixa calculada com os dados reais.
    m["valor_real"] = np.sqrt(m["faixa_valor_min_real"] * m["faixa_valor_max_real"])
    m["contem"] = (m["faixa_valor_min"] <= m["valor_real"]) & (m["valor_real"] <= m["faixa_valor_max"])
    m["erro_centro"] = np.sqrt(m["faixa_valor_min"] * m["faixa_valor_max"]) / m["valor_real"] - 1
    return m[["imovel_id", "cobertura", "padrao_cadastrado_real", "faixa_valor_min", "faixa_valor_max",
              "confianca_estimativa", "valor_real", "contem", "erro_centro"]]


def resumo(v: pd.DataFrame) -> pd.DataFrame:
    """Taxa de acerto da faixa por cobertura."""
    return (
        v.groupby("cobertura")
        .agg(imoveis=("imovel_id", "size"), faixa_contem=("contem", "mean"),
             erro_mediano_centro=("erro_centro", lambda x: x.abs().median()))
        .reindex(COBERTURAS_VALIDADAS)
        .reset_index()
    )
