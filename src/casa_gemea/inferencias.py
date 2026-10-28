"""Inferências da Casa Gêmea: tipo, vínculo, uso, área, construção, conteúdo e alertas.

Cada característica inferida gera quatro colunas:
    <campo>             valor sugerido
    <campo>_selo        OBSERVADO | ESTIMADO | A_CONFIRMAR
    <campo>_confianca   ALTA | MEDIA | BAIXA
    <campo>_evidencia   texto curto com os sinais usados (rastreabilidade)

Regra dos selos: OBSERVADO quando o dado veio pronto do cadastro; ESTIMADO quando
foi inferido com confiança alta ou média; A_CONFIRMAR quando a confiança é baixa,
os sinais se contradizem ou o dado não existe.

Guardrail: nenhuma inferência usa idade ou renda (ver config.CAMPOS_PROIBIDOS).
"""

import pandas as pd

from .area import ModeloArea
from .calibracao import Calibracao
from .config import (
    A_CONFIRMAR,
    ALTA,
    BAIXA,
    ESTIMADO,
    MEDIA,
    OBRA_POSSIVEL_RELEVANTE,
    OBRA_REFORMA_MODERADA,
    OBSERVADO,
)


def _reais(valor: float) -> str:
    return "R$ " + f"{valor:,.0f}".replace(",", ".")


def _selo_inferido(confianca: str) -> str:
    return A_CONFIRMAR if confianca == BAIXA else ESTIMADO


def _aplicar(df: pd.DataFrame, campo: str, regra) -> pd.DataFrame:
    """Aplica uma regra linha a linha que devolve (valor, selo, confiança, evidência)."""
    resultado = df.apply(regra, axis=1, result_type="expand")
    resultado.columns = [campo, f"{campo}_selo", f"{campo}_confianca", f"{campo}_evidencia"]
    return df.join(resultado)


# --------------------------------------------------------------------------- tipo
def _regra_tipo(r: pd.Series):
    apto = r["possui_termo_apartamento"] == "SIM"
    casa = r["possui_termo_casa"] == "SIM"
    condominio = r["pagamento_condominio_mensal"] > 0 or r["possui_termo_condominio"] == "SIM"
    complemento = str(r["complemento"])

    if apto and casa:
        return "INDEFINIDO", A_CONFIRMAR, BAIXA, f"complemento '{complemento}' cita casa e apartamento"
    if apto:
        if condominio:
            return "APARTAMENTO", ESTIMADO, ALTA, f"complemento '{complemento}' + condomínio pago"
        return "APARTAMENTO", ESTIMADO, MEDIA, f"complemento '{complemento}', sem condomínio pago"
    if casa:
        tem_palavra_casa = "CASA" in complemento.upper()
        if condominio:
            return "CASA_EM_CONDOMINIO", ESTIMADO, ALTA, f"complemento '{complemento}' + condomínio pago"
        conf = ALTA if tem_palavra_casa else MEDIA
        return "CASA", ESTIMADO, conf, f"complemento '{complemento}', sem condomínio"
    return "INDEFINIDO", A_CONFIRMAR, BAIXA, "complemento sem termo de casa ou apartamento"


# ------------------------------------------------------------------------ vínculo
def _regra_vinculo(r: pd.Series):
    paga_aluguel = r["pagamento_aluguel_recorrente"] == "SIM"
    financiado = r["parcela_financiamento_imobiliario"] > 0
    recebe_aluguel = r["credito_recorrente_compativel_aluguel"] == "SIM"

    if paga_aluguel + financiado + recebe_aluguel > 1:
        return "INDEFINIDO", A_CONFIRMAR, BAIXA, "sinais contraditórios de aluguel/financiamento"
    if paga_aluguel:
        return (
            "INQUILINO", ESTIMADO, ALTA,
            f"aluguel recorrente de {_reais(r['valor_aluguel_recorrente'])}/mês",
        )
    if financiado:
        return (
            "PROPRIETARIO_FINANCIADO", ESTIMADO, ALTA,
            f"parcela de financiamento de {_reais(r['parcela_financiamento_imobiliario'])}/mês",
        )
    if recebe_aluguel:
        # Combinação: crédito regular E imóvel que não é o endereço onde o cliente mora.
        meses = int(r["quantidade_creditos_recorrentes_12m"])
        evidencia = (
            f"crédito compatível com aluguel de {_reais(r['valor_medio_credito_recorrente'])} "
            f"em {meses} dos 12 meses"
        )
        if r["endereco_principal_compativel"] == "SIM":
            return (
                "PROPRIETARIO_LOCADOR", A_CONFIRMAR, BAIXA,
                evidencia + ", mas o imóvel é o endereço principal do cliente (sinais em conflito)",
            )
        conf = MEDIA if meses >= 10 else BAIXA
        return "PROPRIETARIO_LOCADOR", _selo_inferido(conf), conf, evidencia + " e imóvel fora do endereço principal"
    if r["origem_area"] == "LAUDO_FINANCIAMENTO":
        return (
            "PROPRIETARIO_QUITADO", ESTIMADO, ALTA,
            "sem parcela atual, mas a área veio de laudo de financiamento (imóvel já financiado e quitado)",
        )
    return (
        "PROPRIETARIO_QUITADO", ESTIMADO, MEDIA,
        "sem aluguel pago, sem financiamento e sem aluguel recebido (ausência de sinais)",
    )


# ---------------------------------------------------------------------------- uso
def _regra_uso(r: pd.Series):
    principal = r["endereco_principal_compativel"] == "SIM"
    varios = r["qtd_imoveis_cliente"] > 1

    if r["vinculo"] == "PROPRIETARIO_LOCADOR":
        return "ALUGADO_A_TERCEIROS", r["vinculo_selo"], r["vinculo_confianca"], "imóvel gera crédito compatível com aluguel"
    if principal:
        if r["qtd_principais_cliente"] > 1:
            return "MORADIA_HABITUAL", ESTIMADO, MEDIA, "endereço principal, mas o cliente tem 2 endereços principais"
        return "MORADIA_HABITUAL", ESTIMADO, ALTA, "endereço compatível com o principal do cliente"
    if varios:
        return "TEMPORADA_OU_SEGUNDA_RESIDENCIA", ESTIMADO, MEDIA, "cliente tem 2 imóveis e este não é o principal"
    return "MORADIA_HABITUAL", A_CONFIRMAR, BAIXA, "único imóvel do cliente, mas não bate com o endereço principal"


# --------------------------------------------------------------------------- área
def inferir_area(df: pd.DataFrame, modelo: ModeloArea) -> pd.DataFrame:
    """Usa a área cadastrada quando existe; senão, a estimativa do modelo com faixa."""
    df = df.join(modelo.prever(df))
    tem_area = df["area_cadastrada_m2"] > 0

    df["area_m2"] = df["area_cadastrada_m2"].where(tem_area, df["area_estimada_m2"])
    df["area_min_m2"] = df["area_cadastrada_m2"].where(tem_area, df["area_estimada_min_m2"])
    df["area_max_m2"] = df["area_cadastrada_m2"].where(tem_area, df["area_estimada_max_m2"])
    df["area_m2_selo"] = tem_area.map({True: OBSERVADO, False: ESTIMADO})
    df["area_m2_confianca"] = tem_area.map({True: ALTA, False: MEDIA})
    df["area_m2_evidencia"] = df["origem_area"].where(
        tem_area, "modelo IPTU + energia + tipo + município (faixa de 80%)"
    )
    df["sinal_area_divergente"] = df["sinal_area_divergente"] & tem_area
    return df.drop(columns=["area_estimada_m2", "area_estimada_min_m2", "area_estimada_max_m2"])


# --------------------------------------------------------------------- construção
# IPTU por m² em relação à mediana da cidade. Na base de desenvolvimento, imóveis
# cadastrados como SUPERIOR têm mediana 1,32 e ECONOMICO 0,82 (NORMAL 0,98).
# Validação: quando aponta SUPERIOR acerta 55% (frequência real 18%); ECONOMICO 37%
# (frequência real 19%). É um indício, não uma classificação: confiança BAIXA, e nas
# faixas só desloca o custo entre NORMAL e o padrão indicado.
PADRAO_SUPERIOR_RAZAO_IPTU = 1.25
PADRAO_ECONOMICO_RAZAO_IPTU = 0.85


def classificar_padrao_por_iptu(razao: float) -> str:
    if razao >= PADRAO_SUPERIOR_RAZAO_IPTU:
        return "SUPERIOR"
    if razao <= PADRAO_ECONOMICO_RAZAO_IPTU:
        return "ECONOMICO"
    return "NORMAL"


def inferir_padrao(df: pd.DataFrame, calibracao: Calibracao) -> pd.DataFrame:
    """Padrão cadastrado; se faltar, estimado pelo IPTU por m² (só com área real).

    Com área estimada o IPTU não é usado, porque a própria área já saiu do IPTU
    (o raciocínio seria circular).
    """
    mediana = df["municipio_real"].map(calibracao.iptu_m2_mediana)
    df["razao_iptu_m2_cidade"] = (df["pagamento_iptu_anual"] / df["area_m2"]) / mediana

    def regra(r: pd.Series):
        if r["padrao_construtivo_cadastrado"] != "NAO_DISPONIVEL":
            return r["padrao_construtivo_cadastrado"], OBSERVADO, ALTA, "cadastro"
        if r["area_m2_selo"] == OBSERVADO:
            padrao = classificar_padrao_por_iptu(r["razao_iptu_m2_cidade"])
            return (
                padrao, ESTIMADO, BAIXA,
                f"indício pelo IPTU por m² = {r['razao_iptu_m2_cidade']:.2f}× a mediana de {r['municipio_real']}",
            )
        return "NORMAL", A_CONFIRMAR, BAIXA, "não cadastrado e área estimada; NORMAL adotado como referência"

    return _aplicar(df, "padrao_construtivo", regra)


def _regra_parede(r: pd.Series):
    if r["material_parede_externa_cadastrado"] != "NAO_DISPONIVEL":
        return r["material_parede_externa_cadastrado"], OBSERVADO, ALTA, "cadastro"
    return "NAO_INFORMADO", A_CONFIRMAR, BAIXA, "material da parede externa não cadastrado"


NIVEIS_OBRA = ["SEM_SINAL", "REFORMA_LEVE", "REFORMA_MODERADA", "POSSIVEL_OBRA_RELEVANTE"]


def _regra_obra(r: pd.Series):
    """Combina material de construção, vidraçaria e vínculo.

    - material ≥ 30 mil, ou ≥ 10 mil junto com vidraçaria → possível obra relevante;
    - inquilino desce um nível: raramente faz obra estrutural em imóvel de terceiros.
    """
    gasto = r["gastos_material_construcao_24m"]
    vidros = r["gastos_vidracaria_24m"]
    if gasto == 0:
        return "SEM_SINAL", ESTIMADO, MEDIA, "nenhum gasto com material de construção em 24 meses"

    evidencia = f"{_reais(gasto)} em material de construção em 24 meses"
    if gasto >= OBRA_POSSIVEL_RELEVANTE:
        nivel = 3
    elif gasto >= OBRA_REFORMA_MODERADA:
        nivel = 2
        if vidros > 0:
            nivel = 3
            evidencia += f" + {_reais(vidros)} em vidraçaria"
    else:
        nivel = 1
    if r["vinculo"] == "INQUILINO" and nivel > 1:
        nivel -= 1
        evidencia += " (inquilino: nível reduzido)"

    if nivel >= 2:
        return NIVEIS_OBRA[nivel], A_CONFIRMAR, BAIXA, evidencia
    return NIVEIS_OBRA[nivel], ESTIMADO, MEDIA, evidencia


# ----------------------------------------------------------------------- conteúdo
FRACAO_COMPRAS_NO_IMOVEL = 0.5

def inferir_conteudo(df: pd.DataFrame) -> pd.DataFrame:
    """Faixa do valor dos bens dentro do imóvel.

    Mínimo: o maior entre os bens ponderados pela probabilidade de estarem neste
    imóvel e metade das compras de bens duráveis em 36 meses (parte das compras
    sofre depreciação ou fica em outro lugar).
    Máximo: o maior entre a soma cadastrada dos bens e as compras em 36 meses
    (as duas fontes se sobrepõem, por isso não são somadas).
    """
    compras = (
        df["compras_moveis_36m"] + df["compras_eletrodomesticos_36m"] + df["compras_eletronicos_36m"]
    )
    df["conteudo_min"] = pd.concat(
        [df["bens_valor_ponderado"], FRACAO_COMPRAS_NO_IMOVEL * compras], axis=1
    ).max(axis=1).round(-2)
    df["conteudo_max"] = pd.concat([df["bens_valor_cadastrado"], compras], axis=1).max(axis=1).round(-2)
    df["conteudo_estimado"] = ((df["conteudo_min"] + df["conteudo_max"]) / 2).round(-2).astype(int)

    # Eletrônicos + eletrodomésticos: base de Danos Elétricos e de parte do Roubo.
    eletro_bens = df.get("bens_ponderado_eletronico", 0) + df.get("bens_ponderado_eletrodomestico", 0)
    eletro_compras = df["compras_eletronicos_36m"] + df["compras_eletrodomesticos_36m"]
    df["eletronicos_eletro_min"] = pd.concat(
        [eletro_bens, FRACAO_COMPRAS_NO_IMOVEL * eletro_compras], axis=1
    ).max(axis=1).round(-2)
    df["eletronicos_eletro_max"] = pd.concat([eletro_bens, eletro_compras], axis=1).max(axis=1).round(-2)

    vinculo_fraco = df["bens_qtd_vinculo_baixo"] / df["qtd_bens"].clip(lower=1)
    locador = df["vinculo"] == "PROPRIETARIO_LOCADOR"
    df["conteudo_confianca"] = MEDIA
    df.loc[vinculo_fraco > 0.5, "conteudo_confianca"] = BAIXA
    df.loc[locador, "conteudo_confianca"] = BAIXA
    df["conteudo_selo"] = df["conteudo_confianca"].map({MEDIA: ESTIMADO, BAIXA: A_CONFIRMAR})
    df["conteudo_evidencia"] = (
        df["qtd_bens"].astype(int).astype(str) + " bem(ns) vinculado(s) + compras de 36 meses"
    ).where(~locador, "imóvel alugado a terceiros: bens podem ser do inquilino")
    return df


# ------------------------------------------------------------ sinais de necessidade
def inferir_necessidades(df: pd.DataFrame) -> pd.DataFrame:
    """Sinais que indicam necessidade de coberturas específicas (não indicam risco)."""
    df["sinal_vidros"] = df["gastos_vidracaria_24m"] > 0
    df["sinal_responsabilidade_civil"] = (df["quantidade_dependentes"] > 0) | (
        df["possui_pet_informado"] == "SIM"
    )
    df["sinal_endereco_nao_principal"] = df["endereco_principal_compativel"] == "NAO"
    df["sinal_multiplos_imoveis"] = df["qtd_imoveis_cliente"] > 1
    return df


# ------------------------------------------------------------- coerência entre sinais
def detectar_inconsistencias(df: pd.DataFrame) -> pd.DataFrame:
    """Sinais que se contradizem: baixam a confiança e viram pergunta."""
    regras = {
        "área cadastrada diverge do IPTU e da energia": df["sinal_area_divergente"],
        "recebe aluguel, mas o imóvel é o endereço principal": (
            (df["vinculo"] == "PROPRIETARIO_LOCADOR") & (df["endereco_principal_compativel"] == "SIM")
        ),
        "apartamento sem condomínio pago": (
            (df["tipo_imovel"] == "APARTAMENTO") & (df["pagamento_condominio_mensal"] == 0)
        ),
    }
    df["inconsistencias"] = ""
    for texto, mascara in regras.items():
        df.loc[mascara, "inconsistencias"] += texto + "; "
    df["inconsistencias"] = df["inconsistencias"].str.rstrip("; ")
    df["qtd_inconsistencias"] = sum(m.astype(int) for m in regras.values())
    return df


# ------------------------------------------------------------------------ pipeline
def inferir_tipo(tabela: pd.DataFrame) -> pd.DataFrame:
    """Tipo do imóvel. Separado porque também é entrada do modelo de área."""
    df = _aplicar(tabela, "tipo_imovel", _regra_tipo)
    df["eh_casa"] = df["tipo_imovel"].str.startswith("CASA")
    return df


def construir_casa_gemea(
    tabela: pd.DataFrame, modelo_area: ModeloArea, calibracao: Calibracao
) -> pd.DataFrame:
    """Executa todas as inferências na ordem de dependência."""
    df = inferir_tipo(tabela)
    df = _aplicar(df, "vinculo", _regra_vinculo)
    df = _aplicar(df, "uso_imovel", _regra_uso)
    df = inferir_area(df, modelo_area)
    df = inferir_padrao(df, calibracao)
    df = _aplicar(df, "material_parede", _regra_parede)
    df = _aplicar(df, "alerta_obra", _regra_obra)
    df = inferir_conteudo(df)
    df = inferir_necessidades(df)
    df = detectar_inconsistencias(df)

    selos = [c for c in df.columns if c.endswith("_selo")]
    df["qtd_campos_a_confirmar"] = (df[selos] == A_CONFIRMAR).sum(axis=1)
    return df


# Colunas da Casa Gêmea exportadas para o CSV, na ordem de leitura.
COLUNAS_CASA_GEMEA = [
    "cliente_id", "imovel_id", "municipio_real", "uf_real", "codigo_ibge_municipio",
    "tipo_imovel", "tipo_imovel_selo", "tipo_imovel_confianca", "tipo_imovel_evidencia",
    "vinculo", "vinculo_selo", "vinculo_confianca", "vinculo_evidencia",
    "uso_imovel", "uso_imovel_selo", "uso_imovel_confianca", "uso_imovel_evidencia",
    "area_m2", "area_min_m2", "area_max_m2", "area_m2_selo", "area_m2_confianca", "area_m2_evidencia",
    "padrao_construtivo", "padrao_construtivo_selo", "padrao_construtivo_confianca", "padrao_construtivo_evidencia",
    "material_parede", "material_parede_selo", "material_parede_confianca", "material_parede_evidencia",
    "alerta_obra", "alerta_obra_selo", "alerta_obra_confianca", "alerta_obra_evidencia",
    "conteudo_estimado", "conteudo_min", "conteudo_max", "conteudo_selo", "conteudo_confianca", "conteudo_evidencia",
    "eletronicos_eletro_min", "eletronicos_eletro_max",
    "valor_aluguel_recorrente", "parcela_financiamento_imobiliario", "pagamento_condominio_mensal",
    "sinal_vidros", "sinal_responsabilidade_civil", "sinal_endereco_nao_principal", "sinal_multiplos_imoveis",
    "sinal_area_divergente", "inconsistencias", "qtd_inconsistencias",
    "qtd_campos_a_confirmar",
]
