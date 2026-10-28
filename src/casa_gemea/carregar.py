"""Leitura das tabelas recebidas e montagem da tabela base (uma linha por imóvel)."""

import pandas as pd

from .config import BASES, ENCODING

TABELAS = [
    "clientes",
    "enderecos_imoveis",
    "sinais_imobiliarios",
    "bens_compras",
    "territorio",
    "catalogo_coberturas_fixas_planos",
    "template_resultado_times",
    "template_coberturas_times",
]


def ler_base(nome: str) -> dict[str, pd.DataFrame]:
    """Lê todas as tabelas de uma base ('desenvolvimento' ou 'teste')."""
    pasta = BASES[nome]
    return {t: pd.read_csv(pasta / f"{t}.csv", encoding=ENCODING) for t in TABELAS}


def resumir_bens(bens: pd.DataFrame) -> pd.DataFrame:
    """Agrega os bens por imóvel: valor cadastrado e ponderado, total e por tipo."""
    bens = bens.rename(columns={"imovel_id_referencia": "imovel_id"})

    total = bens.groupby("imovel_id").agg(
        qtd_bens=("bem_id", "count"),
        bens_valor_cadastrado=("valor_cadastrado", "sum"),
        bens_valor_ponderado=("valor_bem_ponderado_referencia", "sum"),
        bens_qtd_vinculo_baixo=("nivel_confianca_vinculo", lambda s: (s == "BAIXA").sum()),
    )

    por_tipo = (
        bens.pivot_table(
            index="imovel_id",
            columns="tipo_bem",
            values="valor_bem_ponderado_referencia",
            aggfunc="sum",
            fill_value=0,
        )
        .add_prefix("bens_ponderado_")
        .rename(columns=str.lower)
    )
    return total.join(por_tipo).fillna(0).reset_index()


def montar_tabela_imoveis(base: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Junta cliente, endereço, sinais, território e bens em uma linha por imóvel."""
    territorio = base["territorio"][
        ["territorio_id", "latitude_aproximada", "longitude_aproximada"]
    ]
    tabela = (
        base["enderecos_imoveis"]
        .merge(base["sinais_imobiliarios"], on=["cliente_id", "imovel_id"], how="left")
        .merge(base["clientes"], on="cliente_id", how="left")
        .merge(territorio, on="territorio_id", how="left")
        .merge(resumir_bens(base["bens_compras"]), on="imovel_id", how="left")
    )

    tabela["qtd_imoveis_cliente"] = tabela.groupby("cliente_id")["imovel_id"].transform("count")
    tabela["qtd_principais_cliente"] = tabela.groupby("cliente_id")[
        "endereco_principal_compativel"
    ].transform(lambda s: (s == "SIM").sum())

    # Ordem igual à do template de resultado, para facilitar o preenchimento.
    ordem = base["template_resultado_times"][["cliente_id", "imovel_id"]]
    return ordem.merge(tabela, on=["cliente_id", "imovel_id"], how="left")
