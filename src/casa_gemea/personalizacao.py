"""Hiperpersonalização: perfil, necessidade por cobertura, adicionais e explicação do motor.

Tudo é regra determinística e auditável. Cada decisão devolve o motivo e os dados usados
("recibo"), para o cliente ver por que está vendo aquilo e poder desligar a personalização.
Não existe rótulo de sinistro: os pesos abaixo são premissas da equipe, e o índice de
necessidade mede prioridade de conversa, não probabilidade de sinistro.

Uso dos dados do cliente: dependentes, pet, uso do app e produtos no banco servem a necessidade
de cobertura, ao canal e ao tom. Idade e renda não entram em nenhuma regra deste módulo.
"""

import numpy as np
import pandas as pd

from .regras import (
    ELEGIVEL, ELEGIVEL_CONDICIONADO, INELEGIVEL, NOME_PLANO, ORDEM_PLANOS, _arred, _reais,
)

# --------------------------------------------------------------------------- jornada
EXPRESS, GUIADA, HUMANA = "EXPRESS", "GUIADA", "HUMANA"
TOM = {
    EXPRESS: "direto e rápido: poucas palavras, um toque por decisão",
    GUIADA: "passo a passo, com exemplos do dia a dia e o motivo de cada pergunta",
    HUMANA: "acolhedor e simples, com apoio de um especialista a um toque de distância",
}


def _num(r: pd.Series, campo: str, padrao: float = 0.0) -> float:
    valor = r.get(campo, padrao)
    try:
        valor = float(valor)
    except (TypeError, ValueError):
        return padrao
    return padrao if np.isnan(valor) else valor


def tipo_de_jornada(r: pd.Series) -> tuple[str, str]:
    """EXPRESS (maturidade digital >= 70), GUIADA (35 a 69) e HUMANA (< 35)."""
    maturidade = _num(r, "indice_maturidade_digital")
    if maturidade >= 70:
        return EXPRESS, f"maturidade digital {int(maturidade)} (70 ou mais)"
    if maturidade >= 35:
        return GUIADA, f"maturidade digital {int(maturidade)} (35 a 69)"
    return HUMANA, f"maturidade digital {int(maturidade)} (abaixo de 35)"


# --------------------------------------------------------------------------- arquétipos
ARQUETIPOS = {
    "CASA_DE_TEMPORADA": ("Casa de temporada", "Imóvel que passa tempo vazio: o risco é a ausência, não o uso."),
    "LOCADOR": ("Locador", "Vive da renda do aluguel: precisa proteger o imóvel e a renda que ele gera."),
    "CASA_EM_OBRA": ("Casa em transformação", "Obra ou reforma recente: o cuidado é não perder a cobertura sem perceber."),
    "INQUILINO_COM_FAMILIA": ("Inquilino com família", "Protege o que é seu e o que pode causar a terceiros, sem pagar pelo prédio."),
    "INQUILINO": ("Inquilino", "Protege os bens e o compromisso do aluguel, não o prédio."),
    "CASA_CONECTADA": ("Casa conectada", "Muitos aparelhos e eletrônicos: o risco é elétrico e de equipamentos."),
    "FAMILIA_NA_CASA_PROPRIA": ("Família na casa própria", "Imóvel próprio com gente e pet em casa: responsabilidade e imprevistos."),
    "CASA_COM_BENS": ("Casa com bens de valor", "Bens de valor em casa: roubo, danos elétricos e conteúdo pedem atenção."),
    "LAR_ENXUTO": ("Lar enxuto", "Poucos bens de valor: o essencial bem feito, sem excesso."),
}


def arquetipo(r: pd.Series) -> tuple[str, list[str]]:
    """Primeiro arquétipo que casa, com os sinais usados."""
    familia = _num(r, "quantidade_dependentes") > 0 or r.get("possui_pet_informado") == "SIM"
    eletro = _num(r, "eletronicos_eletro_max") * _num(r, "fracao_conteudo_do_cliente", 1.0)
    if r.get("imovel_desocupado", False) or r.get("uso_imovel") == "TEMPORADA_OU_SEGUNDA_RESIDENCIA":
        return "CASA_DE_TEMPORADA", ["uso do imóvel: temporada ou segunda residência"]
    if r.get("vinculo") == "PROPRIETARIO_LOCADOR":
        return "LOCADOR", ["vínculo: recebe aluguel do imóvel"]
    if r.get("alerta_obra") in ("POSSIVEL_OBRA_RELEVANTE", "REFORMA_MODERADA"):
        return "CASA_EM_OBRA", ["gasto relevante com material de construção em 24 meses"]
    if r.get("vinculo") == "INQUILINO":
        return ("INQUILINO_COM_FAMILIA", ["vínculo: inquilino", "dependentes ou pet na casa"]) if familia \
            else ("INQUILINO", ["vínculo: inquilino"])
    if eletro >= 30_000:  # percentil ~75 da base: separa quem tem muito mais aparelhos que o típico
        return "CASA_CONECTADA", [f"eletrônicos e eletrodomésticos de até {_reais(eletro)}"]
    if familia:
        return "FAMILIA_NA_CASA_PROPRIA", ["dependentes ou pet na casa"]
    if _num(r, "conteudo_estimado") * _num(r, "fracao_conteudo_do_cliente", 1.0) >= 20_000:
        return "CASA_COM_BENS", ["bens estimados em R$ 20 mil ou mais"]
    return "LAR_ENXUTO", ["poucos sinais de bens de valor ou de necessidades específicas"]


# --------------------------------------------------------------------------- necessidade
# Base de cada cobertura proporcional à frequência de sinistros da carteira residencial da BB
# Seguros (Monitor Mercantil, 21/07/2026): danos elétricos 53,3%, água 14,6%, clima 11,5%, roubo
# 2,1%. Coberturas sem dado público recebem base baixa. O índice é premissa da equipe.
BASE_NECESSIDADE = {
    "DANOS_ELETRICOS": 45, "DANOS_POR_AGUA": 30, "VENDAVAL_GRANIZO": 22, "INCENDIO_RAIO_EXPLOSAO_FUMACA": 20,
    "ROUBO_FURTO_ARROMBAMENTO": 12, "QUEBRA_DE_VIDROS": 10, "IMPACTO_VEICULOS_TERRESTRES": 8,
    "QUEDA_AERONAVE": 3, "RESPONSABILIDADE_CIVIL_FAMILIAR": 10, "PERDA_PAGAMENTO_ALUGUEL": 5,
    "DESPESAS_EMERGENCIAIS": 8,
}


def _nivel(indice: int) -> str:
    return "ALTA" if indice >= 65 else "MEDIA" if indice >= 40 else "BAIXA"


def necessidades(r: pd.Series, plano: str, coberturas_do_plano: list[str]) -> list[dict]:
    """Índice 0 a 100 por cobertura, com os fatores que o compõem."""
    fr = _num(r, "fracao_conteudo_do_cliente", 1.0)
    eletro = _num(r, "eletronicos_eletro_max") * fr
    conteudo = _num(r, "conteudo_estimado") * fr
    casa = bool(r.get("eh_casa", False))
    desocupado = bool(r.get("imovel_desocupado", False)) or r.get("uso_imovel") == "TEMPORADA_OU_SEGUNDA_RESIDENCIA"
    agua = _num(r, "agua_media_mensal_6m")
    dependentes = int(_num(r, "quantidade_dependentes"))
    pet = r.get("possui_pet_informado") == "SIM"
    vinculo = r.get("vinculo")

    fatores = {c: [(base, "frequência de sinistros da carteira (base)")] for c, base in BASE_NECESSIDADE.items()}

    def somar(cobertura, pontos, texto):
        if pontos:
            fatores[cobertura].append((pontos, texto))

    if eletro >= 20_000:
        somar("DANOS_ELETRICOS", 45, f"aparelhos de até {_reais(eletro)}")
    elif eletro >= 10_000:
        somar("DANOS_ELETRICOS", 30, f"aparelhos de até {_reais(eletro)}")
    elif eletro >= 5_000:
        somar("DANOS_ELETRICOS", 15, f"aparelhos de até {_reais(eletro)}")
    if _num(r, "energia_media_mensal_6m") / max(_num(r, "area_m2", 1), 1) >= 2.5:
        somar("DANOS_ELETRICOS", 8, "consumo de energia alto para o tamanho do imóvel")

    if agua >= 200:
        somar("DANOS_POR_AGUA", 20, f"consumo de água de {_reais(agua)}/mês (mais pontos hidráulicos em uso)")
    elif agua >= 120:
        somar("DANOS_POR_AGUA", 10, f"consumo de água de {_reais(agua)}/mês")
    if conteudo >= 20_000:
        somar("DANOS_POR_AGUA", 15, "bens de valor expostos a vazamento")

    if casa:
        somar("VENDAVAL_GRANIZO", 25, "casa: telhado e esquadrias expostos")
        somar("IMPACTO_VEICULOS_TERRESTRES", 20, "casa: muro, portão e fachada voltados para a rua")
        somar("QUEBRA_DE_VIDROS", 10, "casa: mais janelas e portas de vidro")
    if r.get("sinal_vidros"):
        somar("QUEBRA_DE_VIDROS", 35, f"gasto de {_reais(_num(r, 'gastos_vidracaria_24m'))} com vidraçaria em 24 meses")

    somar("INCENDIO_RAIO_EXPLOSAO_FUMACA", 30 if conteudo >= 20_000 else 15 if conteudo >= 10_000 else 0, "valor do imóvel e dos bens")
    if r.get("alerta_obra") in ("POSSIVEL_OBRA_RELEVANTE", "REFORMA_MODERADA"):
        somar("INCENDIO_RAIO_EXPLOSAO_FUMACA", 10, "obra recente aumenta o risco")

    if desocupado:
        somar("ROUBO_FURTO_ARROMBAMENTO", -12, "imóvel vazio por períodos: roubo não é coberto (CG, Roubo 2.1 c)")
    else:
        somar("ROUBO_FURTO_ARROMBAMENTO", 35 if conteudo >= 20_000 else 20 if conteudo >= 10_000 else 0, f"bens de até {_reais(conteudo)}")
        if casa:
            somar("ROUBO_FURTO_ARROMBAMENTO", 15, "casa: mais acessos expostos a arrombamento")

    if pet:
        somar("RESPONSABILIDADE_CIVIL_FAMILIAR", 30, "pet em casa")
    if dependentes:
        somar("RESPONSABILIDADE_CIVIL_FAMILIAR", min(15 * dependentes, 40), f"{dependentes} dependente(s) em casa")
        somar("DESPESAS_EMERGENCIAIS", min(8 * dependentes, 24), "mais pessoas para abrigar em caso de interdição")
    if vinculo == "INQUILINO":
        somar("PERDA_PAGAMENTO_ALUGUEL", 65, "paga aluguel: se o imóvel ficar inabitável, a dívida continua")
    elif vinculo == "PROPRIETARIO_LOCADOR":
        somar("PERDA_PAGAMENTO_ALUGUEL", 65, "recebe aluguel: a renda para após um sinistro")
    elif vinculo == "PROPRIETARIO_FINANCIADO":
        somar("PERDA_PAGAMENTO_ALUGUEL", 10, "parcela de financiamento continua em caso de sinistro")

    saida = []
    for cobertura, itens in fatores.items():
        indice = int(min(100, max(0, sum(p for p, _ in itens))))
        saida.append({
            "cobertura": cobertura,
            "indice": indice,
            "nivel": _nivel(indice),
            "no_plano_recomendado": cobertura in coberturas_do_plano,
            "fatores": [{"pontos": p, "fator": t} for p, t in itens if t != "frequência de sinistros da carteira (base)"],
        })
    return sorted(saida, key=lambda x: -x["indice"])


# --------------------------------------------------------------------------- adicionais
# Fonte: Condições Gerais V1.6 (4.1) e catálogo em saidas/catalogo_adicionais.csv.
def _adicional(id_, nome, necessidade, por_que, clausula, usa, pergunta=None, faixa=None, base_faixa="", cuidado=""):
    saida = {
        "id": id_, "nome": nome, "necessidade": int(min(100, necessidade)), "nivel": _nivel(int(necessidade)),
        "por_que_para_voce": por_que, "clausula": clausula, "dados_usados": usa,
        "pergunta": pergunta, "cuidado": cuidado,
    }
    if faixa:
        saida["faixa_valor_min"], saida["faixa_valor_max"] = faixa
        saida["regra_da_faixa"] = base_faixa
    return saida


NOME_PLANO_ADICIONAL = {"ESSENCIAL": "Essencial", "PRATICO": "Prático"}


def adicionais(r: pd.Series, plano: str, elegibilidade: str, respostas: dict | None = None,
               faixas: list[dict] | None = None) -> list[dict]:
    """Até 3 coberturas adicionais com sinal nos dados, em ordem de necessidade.

    `faixas` são as coberturas já calculadas pelas regras; a faixa de RC Familiar vem delas.
    """
    respostas = respostas or {}
    if not plano or elegibilidade == INELEGIVEL:
        return []
    fr = _num(r, "fracao_conteudo_do_cliente", 1.0)
    portateis = (_num(r, "bens_ponderado_eletronico") + _num(r, "compras_eletronicos_36m")) / 2 * fr
    compras_recentes = (_num(r, "compras_eletronicos_36m") + _num(r, "compras_eletrodomesticos_36m") + _num(r, "compras_moveis_36m")) * fr
    lazer = _num(r, "bens_ponderado_item_lazer") * fr
    desocupado = bool(r.get("imovel_desocupado", False)) or r.get("uso_imovel") == "TEMPORADA_OU_SEGUNDA_RESIDENCIA"
    saida = []

    # RC Familiar como opcional: só fora do Total, e pet/dependentes indicam necessidade, nunca risco.
    dependentes = int(_num(r, "quantidade_dependentes"))
    pet = r.get("possui_pet_informado") == "SIM"
    if plano != "TOTAL" and (pet or dependentes > 0):
        na_casa = " e ".join(x for x in ["pet" if pet else "", f"{dependentes} dependente{'s' if dependentes > 1 else ''}" if dependentes else ""] if x)
        rc = next((f for f in (faixas or []) if f["cobertura"] == "RESPONSABILIDADE_CIVIL_FAMILIAR"), None)
        saida.append(_adicional(
            "RESPONSABILIDADE_CIVIL_FAMILIAR", "Responsabilidade civil familiar",
            45 + (20 if pet else 0) + min(25, 10 * dependentes),
            f"Você tem {na_casa} em casa. O plano {NOME_PLANO_ADICIONAL[plano]} não cobre danos que pessoas ou animais da casa causem a terceiros; esta cobertura sim.",
            "CG V1.6, item 4.1 m e RC Familiar 1.1", "pet informado e quantidade de dependentes (só indicam necessidade, não risco)",
            None, (rc["faixa_valor_min"], rc["faixa_valor_max"]) if rc else None,
            "mesma faixa de limite calculada para a responsabilidade civil familiar do plano Total (referência, não preço)",
            "A cobertura é ligada ao imóvel segurado."))
    if respostas.get("equipamentos") != "NAO" and portateis >= 4_000:
        faixa = (_arred(0.25 * portateis, 500), _arred(0.60 * portateis, 500))
        saida.append(_adicional(
            "EQUIPAMENTOS_PORTATEIS", "Equipamentos portáteis", 40 + min(40, portateis / 500),
            f"Você comprou cerca de {_reais(portateis)} em eletrônicos. Danos elétricos não cobrem queda nem dano mecânico de "
            "notebook, tablet ou câmera; esta cobertura sim, dentro de casa.",
            "CG V1.6, item 4.1 g", "compras de eletrônicos em 36 meses e bens cadastrados do tipo eletrônico",
            "Você tem notebook, tablet ou câmera que gostaria de proteger contra queda e roubo?",
            faixa, "25% a 60% do valor de eletrônicos observado (premissa; os itens precisam ser listados na contratação)",
            "Celulares não são cobertos (CG 6.1); queda em líquido é exclusão da cobertura."))
    if compras_recentes >= 15_000:
        saida.append(_adicional(
            "INDENIZACAO_VALOR_DE_NOVO", "Indenização a valor de novo", 35 + min(35, compras_recentes / 1500),
            f"Você renovou cerca de {_reais(compras_recentes)} em eletrônicos, eletrodomésticos e móveis nos últimos 36 meses. "
            "Sem esta opção, a indenização desconta a depreciação (tabela da CG).",
            "CG V1.6, itens 24.2 e 25.1", "compras de eletrônicos, eletrodomésticos e móveis em 36 meses",
            None, None, "", "Não tem limite próprio: muda a base de pagamento do conteúdo."))
    if desocupado and respostas.get("desocupacao") != "NAO":
        saida.append(_adicional(
            "DESOCUPACAO_TEMPORARIA", "Desocupação temporária", 75,
            "O imóvel fica sem moradores por períodos. Sem esta extensão, roubo e aluguel não são cobertos com o imóvel vazio, "
            "e acima de 30 dias seguidos nenhum evento é coberto (a menos que seja veraneio declarado).",
            "CG V1.6, item 4.1 f e exclusão 7.1 y", "uso do imóvel (temporada ou segunda residência) ou desocupação informada",
            "O imóvel costuma ficar mais de 30 dias seguidos sem ninguém?", None, "",
            "Precisa ser avisada com antecedência (15 dias) e vale de 30 a 60 dias."))
    if lazer >= 5_000 and respostas.get("bicicleta") != "NAO":
        faixa = (_arred(0.30 * lazer, 500), _arred(0.60 * lazer, 500))
        saida.append(_adicional(
            "BICICLETA", "Bicicleta", 30 + min(30, lazer / 800),
            f"Você tem cerca de {_reais(lazer)} em itens de lazer. Se parte for bicicleta, esta cobertura protege contra roubo e "
            "furto com arrombamento, inclusive fora de casa em alguns casos.",
            "CG V1.6, item 4.1 b", "bens cadastrados do tipo item de lazer",
            "Você tem alguma bicicleta de valor?", faixa,
            "30% a 60% do valor de itens de lazer (premissa; a bicicleta precisa ser identificada na apólice)",
            "Bicicletário e garagem comuns não são cobertos."))
    if respostas.get("mei") is None and not desocupado and r.get("uso_imovel") == "MORADIA_HABITUAL" and portateis >= 8_000:
        saida.append(_adicional(
            "ATIVIDADE_PROFISSIONAL_MEI", "Atividade profissional (MEI)", 35,
            "Há equipamentos de valor em casa. Se você trabalha de casa como MEI, os bens da atividade só são cobertos com esta "
            "extensão declarada.",
            "CG V1.6, item 5.6", "equipamentos eletrônicos em casa (apenas indício; só vale se o cliente confirmar)",
            "Você trabalha em casa como MEI, com equipamentos da atividade?", None, "",
            "Sem declaração, bens da atividade profissional não são cobertos."))
    return sorted(saida, key=lambda x: -x["necessidade"])[:3]


# --------------------------------------------------------------------------- assistências
def assistencias(r: pd.Series, plano: str) -> dict:
    """Assistência em destaque entre as do plano; benefício premium só no Total."""
    pacotes = {
        "ESSENCIAL": ["Casa em Apuros"],
        "PRATICO": ["Casa em Apuros", "Casa Funcionando", "Casa Limpa"],
        "TOTAL": ["Casa em Apuros", "Casa Funcionando", "Casa Arrumada", "Casa Limpa", "Casa sem Insetos e Pragas", "Casa Segura"],
    }
    do_plano = pacotes.get(plano, [])
    fr = _num(r, "fracao_conteudo_do_cliente", 1.0)
    eletro = _num(r, "eletronicos_eletro_max") * fr
    candidatos = []
    if eletro >= 10_000:
        candidatos.append(("Casa Funcionando", f"conserta eletrodoméstico, ar-condicionado e TV; você tem até {_reais(eletro)} em aparelhos"))
    if r.get("eh_casa", False):
        candidatos.append(("Casa Limpa", "limpeza de calhas e caixa d'água evita infiltração (que a cobertura não paga)"))
    if r.get("possui_pet_informado") == "SIM":
        candidatos.append(("Casa sem Insetos e Pragas", "desinsetização com orientação para a presença de animais"))
    if _num(r, "quantidade_dependentes") > 0:
        candidatos.append(("Casa Segura", "tela de proteção, película em box e check-up residencial para a família"))
    if r.get("uso_imovel") == "TEMPORADA_OU_SEGUNDA_RESIDENCIA" or r.get("imovel_desocupado", False):
        candidatos.append(("Casa Segura", "fechadura eletrônica e olho mágico para um imóvel que fica vazio"))
    if _num(r, "compras_moveis_36m") >= 8_000:
        candidatos.append(("Casa Arrumada", "montagem e instalação dos móveis e itens que você tem comprado"))
    destaques, ausentes = [], []
    for nome, motivo in candidatos:
        if nome in do_plano and nome not in [d["nome"] for d in destaques]:
            destaques.append({"nome": nome, "por_que": motivo})
        elif nome not in do_plano and nome not in [a["nome"] for a in ausentes]:
            ausentes.append({"nome": nome, "por_que": motivo})
    premium = None
    if plano == "TOTAL":
        if r.get("uso_imovel") == "TEMPORADA_OU_SEGUNDA_RESIDENCIA" or r.get("imovel_desocupado", False):
            premium = ("Fechadura eletrônica", "o imóvel fica vazio por períodos")
        elif eletro >= 15_000 or _num(r, "indice_maturidade_digital") >= 70:
            premium = ("Assistente virtual", "muitos aparelhos e rotina digital")
        elif _num(r, "compras_moveis_36m") >= 8_000 or r.get("alerta_obra") != "SEM_SINAL":
            premium = ("Decoração online", "móveis ou reforma recentes")
        else:
            premium = ("Assistente virtual", "benefício de uso mais geral")
    return {
        "base": "Casa em Apuros" if do_plano else "",
        "destaque": destaques[:2],
        "so_em_plano_maior": ausentes[:1],
        "beneficio_premium_sugerido": {"nome": premium[0], "por_que": premium[1]} if premium else None,
    }


# --------------------------------------------------------------------------- perfil e recibos
def perfil(r: pd.Series) -> dict:
    codigo, sinais = arquetipo(r)
    jornada, motivo_jornada = tipo_de_jornada(r)
    revisao = r.get("possui_seguro_residencial") == "SIM"
    produtos = int(_num(r, "qtd_produtos_seguridade"))
    rotulo, descricao = ARQUETIPOS[codigo]
    return {
        "arquetipo": codigo, "rotulo": rotulo, "descricao": descricao, "sinais": sinais,
        "jornada": jornada, "jornada_motivo": motivo_jornada, "tom": TOM[jornada],
        "modo": "REVISAO_DE_SEGURO" if revisao else "NOVA_APOLICE",
        "relacionamento_seguridade": produtos,
    }


def mensagem_do_app(p: dict, plano: str, adic: list[dict], alertas: list[dict], r: pd.Series) -> dict:
    """Notificação que o app do banco mostraria. Só sinais do imóvel e da necessidade."""
    if alertas and alertas[0]["tipo"] == "OBRA":
        titulo, texto = "Reforma na sua casa?", "Notamos um gasto alto com material de construção. Antes de seguir, veja o que muda na sua cobertura."
    elif p["modo"] == "REVISAO_DE_SEGURO":
        titulo = "Vamos revisar o seguro da sua casa"
        texto = (f"Olhamos a sua casa e vimos {len(adic)} ponto(s) que podem estar sem proteção." if adic
                 else "Olhamos a sua casa e o seu plano atual parece adequado. Quer conferir?")
    elif adic:
        titulo = "Um seguro feito para a sua casa"
        texto = adic[0]["por_que_para_voce"].split(". ")[0] + "."
    else:
        titulo = "Um seguro feito para a sua casa"
        texto = f"Montamos uma sugestão ({NOME_PLANO.get(plano, plano)}) com o que o banco já sabe do seu imóvel."
    return {"titulo": titulo, "texto": texto, "tom": p["tom"]}


def alertas_do_cliente(r: pd.Series, elegibilidade: str) -> list[dict]:
    saida = []
    if r.get("alerta_obra") == "POSSIVEL_OBRA_RELEVANTE" or elegibilidade == ELEGIVEL_CONDICIONADO and "obra" in str(r.get("alerta_obra", "")).lower():
        saida.append({"tipo": "OBRA", "texto": "Obra ou reforma relevante pode deixar o imóvel fora da cobertura (CG V1.6, 7.1 w/x). Confirme antes de contratar."})
    if r.get("uso_imovel") == "TEMPORADA_OU_SEGUNDA_RESIDENCIA" or r.get("imovel_desocupado", False):
        saida.append({"tipo": "DESOCUPACAO", "texto": "Imóvel vazio por mais de 30 dias seguidos perde as coberturas, salvo veraneio declarado (CG V1.6, 7.1 y)."})
    if r.get("vinculo") == "PROPRIETARIO_LOCADOR":
        saida.append({"tipo": "BENS_DE_TERCEIROS", "texto": "Bens do inquilino não são cobertos (CG V1.6, 6.1 r): o conteúdo considerado é reduzido."})
    return saida


RECIBOS = [
    ("compras de eletrônicos e eletrodomésticos (36 meses)", "equipamentos portáteis, danos elétricos e assistência Casa Funcionando"),
    ("bens cadastrados do tipo item de lazer", "cobertura de bicicleta"),
    ("consumo de água e energia", "danos por água e danos elétricos"),
    ("vínculo com o imóvel (aluguel, financiamento, crédito)", "plano, aluguel e quanto do prédio é seu"),
    ("dependentes e pet informados", "responsabilidade civil, despesas emergenciais e assistências"),
    ("uso do imóvel e ocupação", "roubo, desocupação temporária e fechadura eletrônica"),
    ("maturidade digital e uso do app", "canal, tom e ritmo da conversa (nunca plano nem preço)"),
    ("seguro residencial já contratado", "modo de revisão em vez de nova apólice"),
]


def analisar(r: pd.Series, plano: str, elegibilidade: str, coberturas_do_plano: list[str],
             respostas_adicionais: dict | None = None, faixas: list[dict] | None = None) -> dict:
    """Bloco `personalizacao` do contrato JSON."""
    p = perfil(r)
    alertas = alertas_do_cliente(r, elegibilidade)
    adic = adicionais(r, plano, elegibilidade, respostas_adicionais, faixas)
    return {
        "perfil": p,
        "necessidades": necessidades(r, plano, coberturas_do_plano),
        "adicionais_sugeridos": adic,
        "assistencias": assistencias(r, plano),
        "alertas": alertas,
        "mensagem_do_app": mensagem_do_app(p, plano, adic, alertas, r),
        "recibos": [{"dado": d, "usado_para": u} for d, u in RECIBOS],
        "premissas": [
            "Índice de necessidade: base proporcional à frequência de sinistros da carteira (Monitor Mercantil, 21/07/2026) mais "
            "sinais do imóvel; é premissa da equipe, não probabilidade de sinistro.",
            "Faixas dos adicionais são percentuais de bens observados (premissa), sem dado de sinistro por imóvel.",
            "Esta versão não usa idade nem renda do cliente em nenhuma regra de personalização.",
        ],
    }


# --------------------------------------------------------------------------- explicação
def explicacao(r: pd.Series, elegibilidade: str, motivo: str, pontuacao: dict, impacto: dict,
               cor: str, canal: str, plano: str, nao_abaixo: str, nao_acima: str) -> dict:
    """Rastro do motor, passo a passo, para a tela "Como o motor pensou"."""
    checagens = [
        {"regra": "Situação cadastral regular", "ok": r.get("situacao_imovel_cadastral") == "REGULAR", "base": "Guia 9.1"},
        {"regra": "Paredes sem predomínio de material combustível", "ok": r.get("material_parede") not in
         {"MADEIRA", "TAIPA", "PAU_A_PIQUE", "PLASTICO", "LONA", "MISTO_MADEIRA"}, "base": "Guia 9.1",
         "estado": r.get("material_parede_selo")},
        {"regra": "Sem obra estrutural em andamento", "ok": r.get("alerta_obra") not in ("OBRA_ESTRUTURAL",),
         "pendente": r.get("alerta_obra") == "POSSIVEL_OBRA_RELEVANTE", "base": "CG V1.6, 7.1 w/x",
         "estado": r.get("alerta_obra_selo")},
        {"regra": "Tipo de imóvel identificado", "ok": r.get("tipo_imovel") != "INDEFINIDO", "base": "Guia 9.1"},
    ]
    sinais_p = [{"pontos": p, "sinal": s} for p, s in pontuacao.get("sinais_pratico", [])]
    sinais_t = [{"pontos": p, "sinal": s} for p, s in pontuacao.get("sinais_total", [])]
    return {
        "passos": [
            {"id": "elegibilidade", "titulo": "Este imóvel pode ser segurado?", "resultado": elegibilidade, "motivo": motivo,
             "checagens": checagens},
            {"id": "casa_gemea", "titulo": "O que o banco já sabe da sua casa",
             "texto": "Cada dado vem com selo (observado, estimado, a confirmar), confiança e evidência."},
            {"id": "plano", "titulo": "Qual plano faz sentido?", "resultado": NOME_PLANO.get(plano, plano),
             "pontos_pratico": pontuacao["pontos_pratico"], "pontos_total": pontuacao["pontos_total"],
             "sinais_pratico": sinais_p, "sinais_total": sinais_t,
             "regra": "Total se pontos do Total >= 3, ou >= 2 com ao menos 1 ponto do Prático; senão Prático se pontos do Prático >= 2; "
                      "senão Essencial. Nenhum sinal decide sozinho.",
             "por_que_nao_o_de_baixo": nao_abaixo, "por_que_nao_o_de_cima": nao_acima},
            {"id": "faixas", "titulo": "Quanto de cobertura",
             "texto": "Cada faixa é o limite máximo de indenização sugerido (não é preço). A largura mostra a incerteza dos dados."},
            {"id": "perguntas", "titulo": "O que ainda pode mudar o resultado",
             "campos_que_mudam_o_plano": [c for c in str(impacto.get("campos_que_mudam_plano", "")).split("|") if c],
             "texto": "Só perguntamos o que mudaria o plano, a elegibilidade ou estreitaria a faixa. Se nada mudaria, paramos."},
            {"id": "canal", "titulo": "Como seguir", "semaforo": cor, "canal": canal},
        ],
        "limites_do_motor": [
            "Percentuais de perda por evento e pesos do plano são premissas da equipe (sem dado de sinistro por imóvel).",
            "Faixa de reconstrução calibrada em cerca de 90% (teste cego da área: erro mediano de 13% no desenvolvimento e 16% no teste).",
            "O motor decide e calcula com regras; IA generativa, quando usada, só redige texto.",
        ],
    }
