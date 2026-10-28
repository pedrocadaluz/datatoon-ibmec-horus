"""Monta e valida os dois templates oficiais da entrega a partir da recomendação.

Os campos dos templates são de formato livre e documentado (dicionário de dados,
natureza SAIDA_DA_EQUIPE). Convenções adotadas (também no README):
- elegivel: SIM | PENDENTE_VALIDACAO | NAO
- tipo, uso, vínculo, plano e confiança: códigos em maiúsculas, iguais aos do relatório;
- coberturas_recomendadas e perguntas_confirmacao: itens separados por " | ";
- faixas: reais inteiros, sem "R$" e sem separador de milhar.
"""

import re

import pandas as pd

from . import regras
from .config import PASTA_DADOS_EXTERNOS

COLUNAS_RESULTADO = [
    "cliente_id", "imovel_id", "elegivel", "motivo_inelegibilidade", "tipo_imovel_sugerido",
    "uso_imovel_sugerido", "tipo_vinculo_sugerido", "plano_recomendado", "coberturas_recomendadas",
    "confianca_geral", "justificativa_recomendacao", "perguntas_confirmacao", "fontes_publicas_adicionais",
]
COLUNAS_COBERTURAS = [
    "cliente_id", "imovel_id", "cobertura", "faixa_valor_min", "faixa_valor_max", "confianca_estimativa",
    "dados_utilizados", "regra_calculo_utilizada", "justificativa", "informacao_a_confirmar", "observacao",
]

ELEGIVEL_ENTREGA = {
    regras.ELEGIVEL: "SIM",
    regras.ELEGIVEL_CONDICIONADO: "PENDENTE_VALIDACAO",
    regras.INELEGIVEL: "NAO",
}

LEGIVEL = {
    "APARTAMENTO": "apartamento", "CASA": "casa", "CASA_EM_CONDOMINIO": "casa em condomínio",
    "INQUILINO": "inquilino", "PROPRIETARIO_FINANCIADO": "proprietário com financiamento",
    "PROPRIETARIO_LOCADOR": "proprietário que aluga a terceiros", "PROPRIETARIO_QUITADO": "proprietário sem financiamento",
    "MORADIA_HABITUAL": "moradia habitual", "TEMPORADA_OU_SEGUNDA_RESIDENCIA": "temporada ou segunda residência",
    "ALUGADO_A_TERCEIROS": "alugado a terceiros", "OBSERVADO": "cadastro", "ESTIMADO": "estimado",
    "A_CONFIRMAR": "a confirmar", "ECONOMICO": "econômico", "NORMAL": "normal", "SUPERIOR": "superior",
    "ALTA": "alta", "MEDIA": "média", "BAIXA": "baixa",
}
CAMPO_LEGIVEL = {
    "conteudo": "do valor dos bens", "vinculo": "do vínculo com o imóvel",
    "tipo_imovel": "do tipo do imóvel", "ocupacao": "da ocupação do imóvel",
}

FONTES_FIXAS = [
    "Condições Gerais do Seguro Residencial BB Seguros V1.6 (vigência desde 11/08/2026), Processo SUSEP 15414.606453/2020-10 "
    "(página do produto: https://www.bbseguros.com.br/seguros/seguro-residencial)",
    "Tabela CUB/m² Sinduscon-MG abr/2025, fatores de tipo e padrão "
    "(https://sinduscon-mg.org.br/wp-content/uploads/2025/05/tabela_cub_abril_2025.pdf)",
    "Monitor Mercantil, 21/07/2026, distribuição de sinistros residenciais BB Seguros "
    "(https://monitormercantil.com.br/?p=332625)",
]


def _t(valor) -> str:
    return LEGIVEL.get(valor, str(valor).lower())


def _fontes_por_uf() -> dict[str, str]:
    cub = pd.read_csv(PASTA_DADOS_EXTERNOS / "cub_r8n_por_uf.csv")
    fontes = {}
    for _, c in cub.iterrows():
        cub_txt = f"CUB R8-N {c['uf']} {c['mes_referencia']} ({c['fonte_original']}, consultado em {c['url_consulta']})"
        fontes[c["uf"]] = " | ".join([FONTES_FIXAS[0], cub_txt, *FONTES_FIXAS[1:]])
    return fontes


def _resumo_casa(c: pd.Series) -> str:
    area = f"{int(c['area_m2'])} m² ({_t(c['area_m2_selo'])})"
    if c["area_m2_selo"] != "OBSERVADO":
        area = f"{int(c['area_m2'])} m² (estimada pelo IPTU e pela energia: {int(c['area_min_m2'])}–{int(c['area_max_m2'])} m²)"
    return (
        f"Casa Gêmea: {_t(c['tipo_imovel'])} ({_t(c['tipo_imovel_selo'])}), {_t(c['vinculo'])} "
        f"[{_t(c['vinculo_selo'])}: {c['vinculo_evidencia']}], {_t(c['uso_imovel'])}; área {area}; "
        f"padrão {_t(c['padrao_construtivo'])} ({_t(c['padrao_construtivo_selo'])})."
    )


def _justificativa(r: pd.Series, c: pd.Series) -> str:
    plano = r["plano_recomendado"]
    if not plano:
        return f"Sem plano: {r['motivo_inelegibilidade']}"
    nome = regras.NOME_PLANO[plano]
    i = regras.ORDEM_PLANOS.index(plano)
    partes = [f"Recomendação inicial com os dados do banco: plano {nome}, confiança {_t(r['confianca_geral'])}."]
    if r["elegivel"] != regras.ELEGIVEL:
        partes.append(f"Elegibilidade pendente: {r['motivo_inelegibilidade']}")
    partes.append(_resumo_casa(c))
    partes.append(f"Por que o {nome}: " + (r["motivos_plano"] or "proteção básica; poucos sinais de bens de valor ou de necessidade de aluguel e RC") + ".")
    if i > 0:
        partes.append(f"Por que não o {regras.NOME_PLANO[regras.ORDEM_PLANOS[i - 1]]}: {r['por_que_nao_plano_abaixo']}")
    if i < len(regras.ORDEM_PLANOS) - 1:
        partes.append(f"Por que não o {regras.NOME_PLANO[regras.ORDEM_PLANOS[i + 1]]}: {r['por_que_nao_plano_acima']}")
    campos = [CAMPO_LEGIVEL[x] for x in str(r["campos_que_mudam_plano"]).split("|") if x in CAMPO_LEGIVEL]
    if campos:
        partes.append(f"O plano pode mudar conforme a confirmação {' e '.join(campos)}.")
    else:
        partes.append("Nenhuma resposta plausível muda o plano; as perguntas só ajustam as faixas.")
    return " ".join(partes)


def montar_resultado(rec: pd.DataFrame, casa: pd.DataFrame, template: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por imóvel, na ordem do template oficial."""
    fontes = _fontes_por_uf()
    casa = casa.set_index("imovel_id")
    rec = rec.set_index("imovel_id")
    linhas = []
    for imovel_id in template["imovel_id"]:
        r, c = rec.loc[imovel_id], casa.loc[imovel_id]
        linhas.append({
            "cliente_id": r["cliente_id"],
            "imovel_id": imovel_id,
            "elegivel": ELEGIVEL_ENTREGA[r["elegivel"]],
            "motivo_inelegibilidade": r["motivo_inelegibilidade"] if isinstance(r["motivo_inelegibilidade"], str) else "",
            "tipo_imovel_sugerido": c["tipo_imovel"],
            "uso_imovel_sugerido": c["uso_imovel"],
            "tipo_vinculo_sugerido": c["vinculo"],
            "plano_recomendado": r["plano_recomendado"],
            "coberturas_recomendadas": r["coberturas_recomendadas"].replace("|", " | "),
            "confianca_geral": r["confianca_geral"],
            "justificativa_recomendacao": _justificativa(r, c),
            "perguntas_confirmacao": r["perguntas_confirmacao"],
            "fontes_publicas_adicionais": fontes[c["uf_real"]],
        })
    return pd.DataFrame(linhas, columns=COLUNAS_RESULTADO).fillna("")


def montar_coberturas(cob: pd.DataFrame, template: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por cobertura, imóveis na ordem do template e coberturas na ordem do catálogo."""
    ordem_imovel = {imovel: i for i, imovel in enumerate(template["imovel_id"])}
    cob = cob.copy()
    cob["_ordem"] = cob["imovel_id"].map(ordem_imovel)
    cob = cob.sort_values("_ordem", kind="stable")
    for col in ["faixa_valor_min", "faixa_valor_max"]:
        cob[col] = cob[col].astype(int)
    return cob[COLUNAS_COBERTURAS].fillna("").reset_index(drop=True)


def validar(resultado: pd.DataFrame, coberturas: pd.DataFrame, template: pd.DataFrame,
            catalogo: pd.DataFrame) -> pd.DataFrame:
    """Testes de formato e coerência da entrega. Cada linha: teste, ok, detalhe."""
    do_plano = catalogo.groupby("plano")["cobertura_fixa"].apply(set).to_dict()
    por_imovel = coberturas.groupby("imovel_id")["cobertura"].apply(set)
    obrigatorias = [c for c in COLUNAS_RESULTADO if c != "motivo_inelegibilidade"]
    texto = resultado.select_dtypes("object").to_numpy().ravel().tolist() + \
        coberturas.select_dtypes("object").to_numpy().ravel().tolist()

    testes = [
        ("Mesmas colunas e ordem do template de resultado", list(resultado.columns) == list(template.columns), ""),
        ("Todos os imóveis do template, na mesma ordem",
         resultado["imovel_id"].tolist() == template["imovel_id"].tolist(), f"{len(resultado)} imóveis"),
        ("cliente_id igual ao do template", (resultado["cliente_id"].values == template["cliente_id"].values).all(), ""),
        ("Campos obrigatórios preenchidos", (resultado[obrigatorias] != "").all().all(), ""),
        ("Motivo preenchido quando não é elegível sem ressalvas",
         (resultado.loc[resultado["elegivel"] != "SIM", "motivo_inelegibilidade"] != "").all(), ""),
        ("Coberturas de cada imóvel = coberturas fixas do plano no catálogo",
         all(por_imovel.get(r.imovel_id, set()) == do_plano.get(r.plano_recomendado, set())
             for r in resultado.itertuples()), f"{len(coberturas)} linhas de cobertura"),
        ("Nomes de cobertura iguais ao catálogo", coberturas["cobertura"].isin(catalogo["cobertura_fixa"]).all(), ""),
        ("Sem cobertura duplicada por imóvel", not coberturas.duplicated(["imovel_id", "cobertura"]).any(), ""),
        ("Faixas são números inteiros positivos",
         bool((coberturas[["faixa_valor_min", "faixa_valor_max"]] > 0).all().all())
         and all(pd.api.types.is_integer_dtype(coberturas[c]) for c in ["faixa_valor_min", "faixa_valor_max"]), ""),
        ("Mínimo ≤ máximo em todas as faixas", (coberturas["faixa_valor_min"] <= coberturas["faixa_valor_max"]).all(), ""),
        ("Toda cobertura tem confiança, dados, regra e justificativa",
         (coberturas[["confianca_estimativa", "dados_utilizados", "regra_calculo_utilizada", "justificativa"]] != "").all().all(), ""),
        ("Nenhum texto com quebra de linha", not any("\n" in str(x) or "\r" in str(x) for x in texto), ""),
        ("Nenhum texto cita idade ou renda do cliente",
         not any(re.search(r"\bidade\b|renda mensal|renda do cliente", str(x).lower()) for x in texto), ""),
    ]
    return pd.DataFrame(testes, columns=["teste", "ok", "detalhe"])
