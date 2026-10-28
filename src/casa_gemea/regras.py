"""Regras do seguro: elegibilidade, escolha do plano, faixas das coberturas, confiança e canal.

Fontes das regras:
- Guia dos Times, seção 9 (elegibilidade, planos e coberturas fixas);
- Condições Gerais do Seguro Residencial BB Seguros, Processo SUSEP 15414.606453/2020-10,
  versão 1.3 (citadas como "CG" e o número do item);
- CUB/m² dos Sinduscons (custo de reconstrução).

Princípio das faixas: o seguro é contratado a Primeiro Risco Absoluto (CG 15.1), ou seja,
a seguradora paga até o Limite Máximo de Indenização (LMI) de cada cobertura, sem rateio.
A faixa sugerida é o intervalo de LMI que cobre a perda plausível de cada evento, calculado
a partir da Casa Gêmea. Quanto maior a incerteza dos dados, mais larga a faixa.

Guardrail: nenhuma regra usa idade ou renda.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .calibracao import Calibracao
from .config import A_CONFIRMAR, ALTA, BAIXA, CONFIRMADO, ESTIMADO, MEDIA, OBSERVADO, PASTA_DADOS_EXTERNOS

ORDEM_PLANOS = ["ESSENCIAL", "PRATICO", "TOTAL"]
# Campos que um formulário tradicional perguntaria e que a Casa Gêmea já preenche com dados do banco:
# tipo, vínculo, uso, área, padrão, parede, obra e conteúdo (a declaração única fica de fora das duas contas).
CAMPOS_FORMULARIO_TRADICIONAL = 8
NOME_PLANO = {"ESSENCIAL": "Essencial", "PRATICO": "Prático", "TOTAL": "Total"}

ELEGIVEL = "ELEGIVEL"
ELEGIVEL_CONDICIONADO = "ELEGIVEL_CONDICIONADO"
INELEGIVEL = "INELEGIVEL"

# Materiais de parede que o guia manda validar ("predominância de material combustível").
MATERIAIS_COMBUSTIVEIS = {"MADEIRA", "TAIPA", "PAU_A_PIQUE", "PLASTICO", "LONA", "MISTO_MADEIRA"}


# ------------------------------------------------------------------ referências
@dataclass
class Referencias:
    cub_r8n: dict[str, float]          # R$/m² por UF
    fator_padrao: dict[tuple, float]   # (grupo, padrão) → fator sobre o R8-N
    calibracao: Calibracao


def carregar_referencias(calibracao: Calibracao) -> Referencias:
    cub = pd.read_csv(PASTA_DADOS_EXTERNOS / "cub_r8n_por_uf.csv")
    fatores = pd.read_csv(PASTA_DADOS_EXTERNOS / "fatores_cub_padrao.csv")
    return Referencias(
        cub_r8n=dict(zip(cub["uf"], cub["cub_r8n_reais_m2"])),
        fator_padrao={(g, p): f for g, p, f in zip(fatores["grupo"], fatores["padrao"], fatores["fator_sobre_r8n"])},
        calibracao=calibracao,
    )


def _reais(valor: float) -> str:
    return "R$ " + f"{valor:,.0f}".replace(",", ".")


def _arred(valor: float, piso: int = 500) -> int:
    return int(max(piso, round(valor, -2)))


# --------------------------------------------------------------- elegibilidade
def avaliar_elegibilidade(r: pd.Series) -> tuple[str, str]:
    """Devolve (status, motivo). O guia pede validar antes de recomendar (seção 9.1)."""
    if r["situacao_imovel_cadastral"] != "REGULAR":
        return INELEGIVEL, f"Situação cadastral '{r['situacao_imovel_cadastral']}': imóvel sem condição regular de habitabilidade (guia 9.1)."
    if r["material_parede"] in MATERIAIS_COMBUSTIVEIS:
        return INELEGIVEL, f"Paredes externas de {r['material_parede'].lower()}: predominância de material combustível (guia 9.1)."
    if r["alerta_obra"] == "OBRA_ESTRUTURAL":
        return INELEGIVEL, "Cliente confirmou obra estrutural ou ampliação em andamento: imóveis em reforma ou construção estão fora da cobertura (CG 7.1 w/x). Pode ser contratado ao fim da obra."
    if r.get("declaracao_negada", False):
        return ELEGIVEL_CONDICIONADO, "Cliente não confirmou a declaração de elegibilidade (área urbana, alvenaria, sem obra estrutural, não tombado): validar com o gerente."
    if r["tipo_imovel"] == "INDEFINIDO":
        return ELEGIVEL_CONDICIONADO, "Tipo de imóvel não identificado; confirmar se é casa, apartamento ou sobrado."
    if r["alerta_obra"] == "POSSIVEL_OBRA_RELEVANTE":
        return (
            ELEGIVEL_CONDICIONADO,
            f"Pendente de validação: possível obra relevante ({r['alerta_obra_evidencia']}). "
            "Imóveis em reforma ou construção estão fora da cobertura (CG 7.1 w/x).",
        )
    return ELEGIVEL, ""


# ----------------------------------------------------------------------- plano
# Limiares calibrados na base de desenvolvimento (ver docs/02_regras_seguro.md).
CONTEUDO_RELEVANTE = 20_000
CONTEUDO_MODERADO = 10_000
ELETRO_RELEVANTE = 15_000


def _plural(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def pontuar_plano(r: pd.Series) -> dict:
    """Soma sinais que pedem coberturas do Prático e do Total. Nenhum sinal decide sozinho.

    Imóvel que fica desocupado por longos períodos não tem cobertura de roubo (CG, Roubo
    2.1 c), então bens e acessos deixam de pontuar para o Prático; só vidros continuam.
    """
    pratico, total = [], []
    conteudo = r["conteudo_estimado"] * r["fracao_conteudo_do_cliente"]
    roubo_util = not r.get("imovel_desocupado", False)

    if roubo_util and conteudo >= CONTEUDO_RELEVANTE:
        pratico.append((2, f"bens estimados em {_reais(r['conteudo_min'])} a {_reais(r['conteudo_max'])}"))
    elif roubo_util and conteudo >= CONTEUDO_MODERADO:
        pratico.append((1, f"bens estimados em {_reais(r['conteudo_min'])} a {_reais(r['conteudo_max'])}"))
    if roubo_util and r["eletronicos_eletro_max"] * r["fracao_conteudo_do_cliente"] >= ELETRO_RELEVANTE:
        pratico.append((1, f"eletrônicos e eletrodomésticos de até {_reais(r['eletronicos_eletro_max'])}"))
    if r["sinal_vidros"]:
        pratico.append((1, f"gasto de {_reais(r['gastos_vidracaria_24m'])} com vidraçaria em 24 meses"))
    if roubo_util and r["eh_casa"]:
        pratico.append((1, "casa: mais portas e janelas expostas a arrombamento"))

    if r["vinculo"] == "INQUILINO":
        total.append((2, f"paga aluguel de {_reais(r['valor_aluguel_recorrente'])}: se o imóvel ficar inabitável, continua devendo o aluguel"))
    if r["vinculo"] == "PROPRIETARIO_LOCADOR":
        total.append((2, f"recebe cerca de {_reais(r['valor_medio_credito_recorrente'])}/mês de aluguel: renda que pararia após um sinistro"))
    if r["possui_pet_informado"] == "SIM":
        total.append((1, "tem pet: danos a terceiros causados pelo animal"))
    if r["quantidade_dependentes"] > 0:
        dependentes = _plural(int(r["quantidade_dependentes"]), "dependente", "dependentes")
        total.append((1, f"{dependentes}: danos a terceiros e despesas de hospedagem da família"))

    pontos_p = sum(p for p, _ in pratico)
    pontos_t = sum(p for p, _ in total)
    if pontos_t >= 3 or (pontos_t >= 2 and pontos_p >= 1):
        plano = "TOTAL"
    elif pontos_p >= 2:
        plano = "PRATICO"
    else:
        plano = "ESSENCIAL"
    return {
        "plano_recomendado": plano,
        "pontos_pratico": pontos_p,
        "pontos_total": pontos_t,
        "motivos_pratico": [m for _, m in pratico],
        "motivos_total": [m for _, m in total],
        "sinais_pratico": pratico,
        "sinais_total": total,
    }


# --------------------------------------------------------------- interesse segurável
def interesse_seguravel(r: pd.Series) -> tuple[float, float, float, str]:
    """Quanto do prédio e do conteúdo é do cliente: (prédio mín, prédio máx, conteúdo, regra)."""
    vinculo, tipo = r["vinculo"], r["tipo_imovel"]
    if vinculo == "INQUILINO":
        return 0.03, 0.10, 1.0, "inquilino: prédio é do proprietário (CG 10); só benfeitorias, de 3% a 10%"
    if tipo == "APARTAMENTO":
        return 0.10, 0.30, 1.0, "apartamento: estrutura coberta pelo seguro do condomínio (CG 5.3 e 15.2.1); partes privativas de 10% a 30%"
    conteudo = 0.2 if vinculo == "PROPRIETARIO_LOCADOR" else 1.0
    if vinculo == "PROPRIETARIO_FINANCIADO":
        return 0.50, 1.0, conteudo, "financiado: se houver seguro habitacional obrigatório, o residencial atua primeiro no conteúdo e complementa a estrutura (CG 15.2.1)"
    if tipo == "CASA_EM_CONDOMINIO":
        return 0.80, 1.0, conteudo, "casa em condomínio: estrutura própria; áreas comuns no seguro do condomínio"
    regra = "casa própria: estrutura inteira"
    if vinculo == "PROPRIETARIO_LOCADOR":
        regra += "; bens no imóvel são do inquilino (bens de terceiros não cobertos, CG 6.1 r), até 20%"
    return 1.0, 1.0, conteudo, regra


def custo_reconstrucao(r: pd.Series, ref: Referencias) -> tuple[float, float, str]:
    """Área × CUB da UF × fator do tipo e do padrão (Sinduscon)."""
    grupo = "CASA" if r["eh_casa"] else "APARTAMENTO"
    cub = ref.cub_r8n[r["uf_real"]]
    normal = ref.fator_padrao[(grupo, "NORMAL")]
    if r["padrao_construtivo_selo"] == A_CONFIRMAR:
        # Padrão desconhecido: entre o meio do econômico-normal e o meio do normal-superior.
        f_min = (ref.fator_padrao[(grupo, "ECONOMICO")] + normal) / 2
        f_max = (ref.fator_padrao[(grupo, "SUPERIOR")] + normal) / 2
    elif r["padrao_construtivo_selo"] == ESTIMADO:
        # Indício pelo IPTU: faixa entre o NORMAL e o padrão indicado.
        indicado = ref.fator_padrao[(grupo, r["padrao_construtivo"])]
        f_min, f_max = min(normal, indicado), max(normal, indicado)
    else:
        f_min = f_max = ref.fator_padrao[(grupo, r["padrao_construtivo"])]
    fator = f"{f_min:.2f}".replace(".", ",") + ("" if f_min == f_max else "–" + f"{f_max:.2f}".replace(".", ","))
    area = f"{int(r['area_m2'])} m²" + ("" if r["area_min_m2"] == r["area_max_m2"] else f" ({int(r['area_min_m2'])}–{int(r['area_max_m2'])})")
    texto = f"{area} × CUB {r['uf_real']} {_reais(cub)}/m² × fator {fator}"
    # Valor central e incertezas na escala log (meia-largura de cada fonte).
    central = r["area_m2"] * cub * np.sqrt(f_min * f_max)
    incertezas = [np.log(r["area_max_m2"] / r["area_min_m2"]) / 2, np.log(f_max / f_min) / 2]
    return central, incertezas, texto


def faixa_combinada(central: float, incertezas: list[float]) -> tuple[float, float]:
    """Combina incertezas independentes pela raiz da soma dos quadrados (escala log).

    Multiplicar todos os extremos (menor área × menor padrão × ...) supõe que tudo
    dá errado ao mesmo tempo; a soma quadrática dá uma faixa realista.
    """
    w = float(np.sqrt(sum(x * x for x in incertezas)))
    return central * np.exp(-w), central * np.exp(w)


# ---------------------------------------------------------------------- confiança
def _confianca(confiancas: list[str]) -> str:
    """Média da incerteza dos dados de entrada (ALTA = 0, MEDIA = 1, BAIXA = 2).

    Média até 0,5 → ALTA; até 1,2 → MEDIA; acima → BAIXA.
    """
    media = sum({ALTA: 0, MEDIA: 1, BAIXA: 2}[c] for c in confiancas) / len(confiancas)
    return ALTA if media <= 0.5 else MEDIA if media <= 1.2 else BAIXA


# -------------------------------------------------------------------------- faixas
# Perda máxima plausível de cada evento, como fração do valor em risco (premissas da
# equipe, documentadas em docs/02_regras_seguro.md). A largura da faixa vem só da
# incerteza dos dados; estes percentuais são testados na análise de sensibilidade.
AGUA_PREDIO, AGUA_CONTEUDO = 0.10, 0.30
VENDAVAL_PREDIO_CASA, VENDAVAL_PREDIO_APTO, VENDAVAL_CONTEUDO = 0.20, 0.03, 0.10
IMPACTO_CASA, IMPACTO_APTO = 0.10, 0.03
AERONAVE = 0.20
ELETRICOS = 0.50
ROUBO = 0.50
VIDROS_M2_MIN, VIDROS_M2_MAX = 40, 60


def calcular_coberturas(r: pd.Series, ref: Referencias) -> list[dict]:
    """Faixa (mín/máx em R$) de cada uma das 11 coberturas do catálogo."""
    s_min, s_max, k, regra_interesse = interesse_seguravel(r)
    rec_central, incertezas, regra_rec = custo_reconstrucao(r, ref)
    if s_min > 0:
        central = rec_central * np.sqrt(s_min * s_max)
        predio_min, predio_max = faixa_combinada(central, incertezas + [np.log(s_max / s_min) / 2])
    else:  # inquilino: só benfeitorias, de zero a s_max
        rec_min, rec_max = faixa_combinada(rec_central, incertezas)
        predio_min, predio_max = rec_min * s_min, rec_max * s_max
    cont_min, cont_max = r["conteudo_min"] * k, r["conteudo_max"] * k
    eletro_min, eletro_max = r["eletronicos_eletro_min"] * k, r["eletronicos_eletro_max"] * k
    casa = r["eh_casa"]
    vend = VENDAVAL_PREDIO_CASA if casa else VENDAVAL_PREDIO_APTO
    impacto = IMPACTO_CASA if casa else IMPACTO_APTO

    campos = ["tipo_imovel", "vinculo", "uso_imovel", "area_m2", "padrao_construtivo", "conteudo"]
    s = {c: r[f"{c}_selo"] for c in campos}
    cf = {c: r[f"{c}_confianca"] for c in campos}
    sel_predio = [cf["tipo_imovel"], cf["vinculo"], cf["area_m2"], cf["padrao_construtivo"]]
    sel_conteudo = [cf["conteudo"]]

    texto_predio = f"prédio {_reais(predio_min)}–{_reais(predio_max)} ({regra_rec}; {regra_interesse})"
    texto_conteudo = f"conteúdo {_reais(cont_min)}–{_reais(cont_max)}"
    dados_predio = "área, tipo, padrão construtivo, UF (CUB), vínculo"
    dados_conteudo = "bens vinculados ao imóvel, compras de 36 meses, vínculo"

    def item(cobertura, vmin, vmax, selos, dados, regra, justificativa, confirmar, obs=""):
        vmin, vmax = _arred(vmin), _arred(vmax)
        if vmin == vmax:  # o arredondamento colapsou a faixa: abre um degrau para continuar sendo faixa
            vmax = vmin + 500
        return {
            "cobertura": cobertura,
            "faixa_valor_min": min(vmin, vmax),
            "faixa_valor_max": max(vmin, vmax),
            "confianca_estimativa": selos if isinstance(selos, str) else _confianca(selos),
            "dados_utilizados": dados,
            "regra_calculo_utilizada": regra,
            "justificativa": justificativa,
            "informacao_a_confirmar": confirmar or "nenhuma: a faixa usa só dados de cadastro ou transações observadas",
            "observacao": obs,
        }

    confirmar_area = "área construída" if s["area_m2"] not in (OBSERVADO, CONFIRMADO) else ""
    confirmar_padrao = "padrão de acabamento" if cf["padrao_construtivo"] != ALTA else ""
    confirmar_predio = "; ".join(x for x in [confirmar_area, confirmar_padrao] if x)
    # Bens nunca são observados: sempre há faixa entre bens cadastrados e compras.
    confirmar_bens = "valor aproximado dos bens no imóvel" if r["conteudo_min"] != r["conteudo_max"] else ""

    itens = [
        item(
            "INCENDIO_RAIO_EXPLOSAO_FUMACA", predio_min + cont_min, predio_max + cont_max,
            sel_predio + sel_conteudo, f"{dados_predio}; {dados_conteudo}",
            "prédio (área × CUB × fator de padrão × interesse no prédio) + conteúdo",
            f"Perda total possível: {texto_predio} + {texto_conteudo}.",
            "; ".join(x for x in [confirmar_predio, confirmar_bens] if x),
        ),
        item(
            "DANOS_POR_AGUA", AGUA_PREDIO * predio_min + AGUA_CONTEUDO * cont_min,
            AGUA_PREDIO * predio_max + AGUA_CONTEUDO * cont_max,
            sel_predio + sel_conteudo, f"{dados_predio}; {dados_conteudo}",
            f"{AGUA_PREDIO:.0%} do prédio + {AGUA_CONTEUDO:.0%} do conteúdo",
            "Vazamento, chuva pelo telhado ou rompimento de tubulação atingem acabamentos e parte dos bens, raramente tudo. "
            "É a 2ª causa de sinistro na carteira residencial da BB Seguros (14,6%).",
            "; ".join(x for x in [confirmar_predio, confirmar_bens] if x),
        ),
        item(
            "VENDAVAL_GRANIZO", vend * predio_min + VENDAVAL_CONTEUDO * cont_min,
            vend * predio_max + VENDAVAL_CONTEUDO * cont_max,
            sel_predio + sel_conteudo, f"{dados_predio}; {dados_conteudo}",
            f"{vend:.0%} do prédio + {VENDAVAL_CONTEUDO:.0%} do conteúdo",
            ("Casa: telhado e esquadrias expostos." if casa else
             "Apartamento: risco concentrado em janelas e sacada; cobertura e fachada são do condomínio.")
            + " Eventos climáticos são 11,5% dos sinistros da carteira residencial da BB Seguros.",
            "; ".join(x for x in [confirmar_predio, confirmar_bens] if x),
        ),
        item(
            "IMPACTO_VEICULOS_TERRESTRES", impacto * predio_min, impacto * predio_max,
            sel_predio, dados_predio,
            f"{impacto:.0%} do prédio",
            "Casa com frente para a rua: muro, portão e fachada." if casa else "Apartamento: impacto atinge sobretudo áreas do condomínio.",
            confirmar_predio,
        ),
        item(
            "QUEDA_AERONAVE", AERONAVE * (predio_min + cont_min), AERONAVE * (predio_max + cont_max),
            sel_predio + sel_conteudo, f"{dados_predio}; {dados_conteudo}",
            f"{AERONAVE:.0%} de (prédio + conteúdo)",
            "Evento raro, mas de grande dano; a faixa acompanha o valor em risco.",
            "; ".join(x for x in [confirmar_predio, confirmar_bens] if x),
            "Percentual de referência adotado pela equipe; não consta nas Condições Gerais.",
        ),
        item(
            "DANOS_ELETRICOS", ELETRICOS * eletro_min, ELETRICOS * eletro_max,
            sel_conteudo + [cf["vinculo"]], "eletrônicos e eletrodomésticos (bens vinculados + compras de 36 meses), vínculo",
            f"{ELETRICOS:.0%} do valor de eletrônicos e eletrodomésticos",
            f"Um pico de energia costuma queimar parte dos aparelhos; base de {_reais(eletro_min)} a {_reais(eletro_max)}.",
            confirmar_bens,
            "Danos elétricos foram 53,3% dos sinistros da carteira residencial da BB Seguros entre jan/2023 e mai/2026 (Monitor Mercantil, 21/07/2026).",
        ),
        item(
            "ROUBO_FURTO_ARROMBAMENTO", ROUBO * cont_min, ROUBO * cont_max,
            sel_conteudo + [cf["vinculo"]], dados_conteudo,
            f"{ROUBO:.0%} do conteúdo",
            f"Num arrombamento são levados sobretudo bens portáteis; {texto_conteudo}. Celulares, joias e dinheiro não são cobertos (CG 6.1).",
            "; ".join(x for x in [confirmar_bens, "se o imóvel fica desocupado por longos períodos" if r["uso_imovel"] != "MORADIA_HABITUAL" else ""] if x),
            "Residência desocupada não tem cobertura de roubo (CG, Roubo 2.1 c) e, após 30 dias, nenhum evento é coberto, salvo imóvel de veraneio declarado (CG 7.1 y)." if r["uso_imovel"] != "MORADIA_HABITUAL" else "",
        ),
    ]

    vidros_max = max(VIDROS_M2_MAX * r["area_max_m2"], 1.5 * r["gastos_vidracaria_24m"])
    itens.append(item(
        "QUEBRA_DE_VIDROS", VIDROS_M2_MIN * r["area_min_m2"], vidros_max,
        [cf["area_m2"]], "área, gasto com vidraçaria em 24 meses",
        f"R$ {VIDROS_M2_MIN} a R$ {VIDROS_M2_MAX} por m² de área (janelas, box, espelhos, tampos); máximo ≥ 1,5× o gasto recente com vidraçaria",
        "Vidros e espelhos crescem com o tamanho do imóvel." + (f" Houve {_reais(r['gastos_vidracaria_24m'])} de vidraçaria em 24 meses." if r["sinal_vidros"] else ""),
        confirmar_area,
        "Valor por m² é premissa da equipe.",
    ))

    # Base R$ 20–50 mil; sobe com pet e com cada dependente (até 3). Premissa da equipe.
    pet = r["possui_pet_informado"] == "SIM"
    dependentes = min(int(r["quantidade_dependentes"]), 3)
    rc_min = 20_000 + 10_000 * pet + 5_000 * dependentes
    rc_max = 50_000 + 30_000 * pet + 10_000 * dependentes
    itens.append(item(
        "RESPONSABILIDADE_CIVIL_FAMILIAR", rc_min, rc_max, BAIXA,
        "dependentes e pet declarados (somente como necessidade, não como risco)",
        "faixa de referência: R$ 20–50 mil, mais R$ 10–30 mil com pet e R$ 5–10 mil por dependente (até 3)",
        "Danos a terceiros não dependem do valor do imóvel; a faixa sobe quando há mais pessoas ou animais que podem causá-los (CG, RC Familiar 1.1 b e c).",
        "se há pets, crianças ou atividades de risco (ex.: piscina)",
        "Faixa de referência da equipe, sem base estatística na base de dados.",
    ))

    # Perda ou pagamento de aluguel: até 6 meses, aluguel mensal ≤ LMI/6 (CG, Perda de Aluguel 1.2 e 1.3).
    cal = ref.calibracao
    if r["vinculo"] == "INQUILINO":
        aluguel_min = aluguel_max = r["valor_aluguel_recorrente"]
        base_aluguel, sel_aluguel = f"aluguel pago de {_reais(aluguel_min)}/mês", [cf["vinculo"]]
    elif r["vinculo"] == "PROPRIETARIO_LOCADOR":
        aluguel_min = aluguel_max = r["valor_medio_credito_recorrente"]
        base_aluguel, sel_aluguel = f"aluguel recebido de cerca de {_reais(aluguel_min)}/mês", [cf["vinculo"], MEDIA]
    else:
        p25, p75 = cal.aluguel_m2_p25[r["municipio_real"]], cal.aluguel_m2_p75[r["municipio_real"]]
        central_m2 = r["area_m2"] * np.sqrt(p25 * p75)
        aluguel_min, aluguel_max = faixa_combinada(
            central_m2, [np.log(r["area_max_m2"] / r["area_min_m2"]) / 2, np.log(p75 / p25) / 2]
        )
        base_aluguel = f"moradia temporária estimada em {_reais(aluguel_min)}–{_reais(aluguel_max)}/mês (aluguel por m² de inquilinos de {r['municipio_real']})"
        sel_aluguel = [MEDIA, cf["area_m2"], cf["vinculo"]]
    itens.append(item(
        "PERDA_PAGAMENTO_ALUGUEL", 3 * aluguel_min, 6 * aluguel_max, sel_aluguel,
        "vínculo, aluguel pago ou recebido; para proprietário morador, área × aluguel por m² da cidade",
        "3 a 6 meses de aluguel (CG: até 6 meses, aluguel mensal ≤ LMI/6)",
        f"Base: {base_aluguel}.",
        "valor do aluguel" if r["vinculo"] == "PROPRIETARIO_LOCADOR"
        else confirmar_area if r["vinculo"] != "INQUILINO" else "",
        "Imóvel desocupado não tem esta cobertura (CG, Perda de Aluguel 3.1 a)." if r["uso_imovel"] == "TEMPORADA_OU_SEGUNDA_RESIDENCIA" else "",
    ))

    # Despesas emergenciais: 10% do LMI nas primeiras 48h + 3% por dia, até 30 dias (CG 1.3).
    pessoas = 1 + int(r["quantidade_dependentes"])
    itens.append(item(
        "DESPESAS_EMERGENCIAIS", pessoas * 150 / 0.03, (pessoas + 1) * 300 / 0.03, MEDIA,
        "tamanho do domicílio (titular + dependentes declarados)",
        "LMI tal que 3% ao dia paguem R$ 150–300 por pessoa (hospedagem, alimentação, transporte)",
        f"Domicílio de {pessoas} a {pessoas + 1} pessoa(s); a CG paga 3% do LMI por dia de desocupação.",
        "quantas pessoas moram no imóvel",
        "Diárias por pessoa são premissa da equipe.",
    ))
    return itens


# ------------------------------------------------------------- comparação de planos
def comparar_planos(r: pd.Series, pontuacao: dict) -> tuple[str, str]:
    """Textos: por que não o plano abaixo e por que não o de cima (lacuna de cobertura)."""
    plano = pontuacao["plano_recomendado"]
    mp, mt = pontuacao["motivos_pratico"], pontuacao["motivos_total"]
    nao_abaixo, nao_acima = "", ""

    quem = [x for x in [
        "tem pet" if r["possui_pet_informado"] == "SIM" else "",
        "tem " + _plural(int(r["quantidade_dependentes"]), "dependente", "dependentes") if r["quantidade_dependentes"] > 0 else "",
    ] if x]
    alternativa_rc = (
        f" Como o cliente {' e '.join(quem)}, o Total vale a pena se ele quiser proteção contra danos a terceiros."
        if quem else ""
    )
    if plano == "ESSENCIAL":
        nao_abaixo = "É o plano de entrada."
        if r.get("imovel_desocupado", False):
            motivo_baixo = "o imóvel fica desocupado por longos períodos, e nesse caso o roubo não é coberto (CG, Roubo 2.1 c); após 30 dias nenhum evento é coberto, salvo veraneio declarado (CG 7.1 y)"
        else:
            motivo_baixo = "os sinais de bens de valor são baixos" + (f" ({'; '.join(mp)})" if mp else "")
        nao_acima = f"O Prático acrescenta roubo e quebra de vidros, mas {motivo_baixo}." + alternativa_rc
    elif plano == "PRATICO":
        nao_abaixo = "O Essencial não cobre roubo nem quebra de vidros, que protegem os bens e os acessos citados acima."
        faltam = []
        if r["vinculo"] not in ("INQUILINO", "PROPRIETARIO_LOCADOR"):
            # O proprietário morador também é coberto (reembolso de moradia temporária,
            # CG Perda de Aluguel 1.1.1 b), mas só se o imóvel ficar inabitável.
            faltam.append(
                "o cliente não paga nem recebe aluguel: a cobertura de aluguel só pagaria uma moradia "
                "temporária se o imóvel ficasse inabitável, sem perda de renda"
            )
        if not quem:
            faltam.append("sem dependentes ou pet informados, a RC familiar fica restrita a danos do próprio imóvel a vizinhos")
        nao_acima = (
            "O Total acrescenta aluguel, RC familiar e despesas emergenciais, mas "
            + "; ".join(faltam or ["os sinais para essas coberturas são fracos"])
            + ". São proteções úteis, mas não prioritárias para este perfil." + alternativa_rc
        )
    else:
        nao_abaixo = "O Prático não cobre aluguel, RC familiar nem despesas emergenciais, que respondem aos sinais citados acima."
        # Em reais: quanto de aluguel o Prático deixaria descoberto (3 a 6 meses, CG Perda de Aluguel 1.2).
        mensal = {"INQUILINO": r["valor_aluguel_recorrente"],
                  "PROPRIETARIO_LOCADOR": r["valor_medio_credito_recorrente"]}.get(r["vinculo"], 0)
        if mensal and mensal > 0:
            verbo = "paga" if r["vinculo"] == "INQUILINO" else "recebe"
            nao_abaixo += (
                f" Em reais: o cliente {verbo} cerca de {_reais(mensal)}/mês de aluguel, então até "
                f"{_reais(3 * mensal)} a {_reais(6 * mensal)} ficariam sem proteção se o imóvel ficasse inabitável."
            )
        nao_acima = "É o plano mais completo."
    return nao_abaixo, nao_acima


# ---------------------------------------------------------------------- canal
def semaforo(r: pd.Series, elegibilidade: str, confianca: str) -> tuple[str, str]:
    """Cor e canal. Dados de app servem só para o canal, nunca para risco ou plano."""
    if elegibilidade != ELEGIVEL or r["vinculo_selo"] == A_CONFIRMAR or r["alerta_obra_selo"] == A_CONFIRMAR:
        return "VERMELHO", "GERENTE"
    usa_app = r["usuario_app"] == "SIM"
    if confianca == ALTA:
        return "VERDE", "ONE_CLICK_BUY" if usa_app else "ATENDIMENTO_ASSISTIDO"
    return "AMARELO", "APP_COM_CONFIRMACAO" if usa_app else "ATENDIMENTO_ASSISTIDO"
