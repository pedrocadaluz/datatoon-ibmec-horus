"""Perguntas que mudam o resultado: análise de impacto de cada campo incerto.

Para cada campo que não é certo (selo diferente de OBSERVADO ou confiança não ALTA),
o motor simula as respostas plausíveis e refaz a recomendação:

- se alguma resposta **muda o plano**, a pergunta é obrigatória;
- se a resposta **estreita a faixa de incêndio** (maior LMI) em pelo menos
  LIMIAR_ESTREITAMENTO, a pergunta é recomendada, enquanto a faixa for mais larga
  que FAIXA_ACEITAVEL;
- nos demais casos a pergunta não é feita (regra de parada).

A confiança geral passa a medir o que importa para o cliente: a chance de o plano
mudar depois das perguntas. Campo incerto que não muda nada não baixa a confiança.
"""

import numpy as np
import pandas as pd

from . import regras
from .config import A_CONFIRMAR, ALTA, BAIXA, CONFIRMADO, MEDIA, OBSERVADO
from .inferencias import _regra_uso

# Fração da largura da faixa de incêndio (escala log) que a resposta precisa remover.
LIMIAR_ESTREITAMENTO = 0.25
# Faixa já aceitável: máximo até 30% acima do mínimo. Daí em diante, só se pergunta o
# que muda elegibilidade ou plano (sem isto, a regra relativa nunca pararia).
FAIXA_ACEITAVEL = 1.30


ALTERNATIVAS_TIPO = {
    "APARTAMENTO": ["CASA"],
    "CASA": ["APARTAMENTO"],
    "CASA_EM_CONDOMINIO": ["APARTAMENTO"],
    "INDEFINIDO": ["APARTAMENTO", "CASA"],
}


def _reais(valor: float) -> str:
    return "R$ " + f"{valor:,.0f}".replace(",", ".")


def _com(r: pd.Series, **mudancas) -> pd.Series:
    """Cópia da linha com campos trocados e o interesse no conteúdo recalculado."""
    novo = r.copy()
    for campo, valor in mudancas.items():
        novo[campo] = valor
    novo["eh_casa"] = str(novo["tipo_imovel"]).startswith("CASA")
    novo["fracao_conteudo_do_cliente"] = regras.interesse_seguravel(novo)[2]
    return novo


def _largura_incendio(r: pd.Series, ref: regras.Referencias) -> float:
    incendio = regras.calcular_coberturas(r, ref)[0]
    return float(np.log(incendio["faixa_valor_max"] / incendio["faixa_valor_min"]))


# --------------------------------------------------------------- cenários por campo
def _cenarios_plano(r: pd.Series) -> list[tuple[str, pd.Series]]:
    """(campo, linha alternativa) para os campos que podem mudar o plano."""
    cenarios = []
    if r["conteudo_min"] != r["conteudo_max"]:
        cenarios.append(("conteudo", _com(r, conteudo_estimado=r["conteudo_min"],
                                          eletronicos_eletro_max=r["eletronicos_eletro_min"])))
        cenarios.append(("conteudo", _com(r, conteudo_estimado=r["conteudo_max"])))

    if r["vinculo"] == "PROPRIETARIO_LOCADOR" and r["vinculo_confianca"] != ALTA:
        # O crédito pode não ser aluguel: o cliente seria proprietário sem renda do imóvel.
        alt = _com(r, vinculo="PROPRIETARIO_QUITADO")
        alt["uso_imovel"] = _regra_uso(alt)[0]
        cenarios.append(("vinculo", alt))
    elif r["vinculo"] == "INDEFINIDO":
        for v in ["INQUILINO", "PROPRIETARIO_FINANCIADO", "PROPRIETARIO_LOCADOR"]:
            cenarios.append(("vinculo", _com(r, vinculo=v)))

    if r["tipo_imovel_confianca"] != ALTA:
        for t in ALTERNATIVAS_TIPO.get(r["tipo_imovel"], []):
            cenarios.append(("tipo_imovel", _com(r, tipo_imovel=t)))

    if r["uso_imovel"] == "TEMPORADA_OU_SEGUNDA_RESIDENCIA":
        cenarios.append(("ocupacao", _com(r, imovel_desocupado=True)))
    return cenarios


def _cenarios_faixa(r: pd.Series) -> list[tuple[str, pd.Series]]:
    """(campo, linha com o campo confirmado) para os campos que alargam a faixa."""
    cenarios = []
    if r["area_m2_selo"] not in (OBSERVADO, CONFIRMADO):
        cenarios.append(("area_m2", _com(r, area_min_m2=r["area_m2"], area_max_m2=r["area_m2"])))
    if r["padrao_construtivo_confianca"] != ALTA:
        cenarios.append(("padrao_construtivo", _com(r, padrao_construtivo="NORMAL",
                                                    padrao_construtivo_selo=OBSERVADO)))
    if r["conteudo_min"] != r["conteudo_max"]:
        meio = r["conteudo_estimado"]
        cenarios.append(("conteudo", _com(r, conteudo_min=meio, conteudo_max=meio)))
    return cenarios


# ------------------------------------------------------------------ texto das perguntas
# Opções fechadas de cada pergunta: (código da resposta no contrato JSON, rótulo exibido).
OPCOES = {
    "obra": [("NAO", "Não"), ("REFORMA_PEQUENA", "Reforma pequena, como pintura ou piso"),
             ("OBRA_ESTRUTURAL", "Obra estrutural ou ampliação")],
    "vinculo_locador": [("PROPRIETARIO_LOCADOR", "Sim, está alugado"), ("PROPRIETARIO_QUITADO", "Não, eu moro nele"),
                        ("IMOVEL_VAZIO", "Não, está vazio")],
    "vinculo": [("INQUILINO", "Moro de aluguel"), ("PROPRIETARIO_FINANCIADO", "É meu e financiado"),
                ("PROPRIETARIO_QUITADO", "É meu e quitado"), ("PROPRIETARIO_LOCADOR", "É meu e alugo para outra pessoa")],
    "tipo_imovel": [("APARTAMENTO", "Apartamento"), ("CASA", "Casa"), ("CASA_EM_CONDOMINIO", "Casa em condomínio fechado")],
    "ocupacao": [("DESOCUPADO", "Sim"), ("OCUPADO", "Não, sempre tem alguém morando")],
    "conteudo": [("MENOR", "Menos que isso"), ("NA_FAIXA", "Nessa faixa"), ("MAIOR", "Mais que isso"), ("NAO_SEI", "Não sei")],
    "area_m2": [("NA_FAIXA", "Sim"), ("MENOR", "Menor"), ("MAIOR", "Maior"), ("NAO_SEI", "Não sei")],
    "padrao_construtivo": [("ECONOMICO", "Simples"), ("NORMAL", "Médio"), ("SUPERIOR", "Alto padrão"), ("NAO_SEI", "Não sei")],
    "declaracao_unica": [("SIM", "Sim"), ("NAO", "Não — o atendimento segue com o gerente")],
}


def chave_opcoes(campo: str, r: pd.Series) -> str:
    return "vinculo_locador" if campo == "vinculo" and r["vinculo"] == "PROPRIETARIO_LOCADOR" else campo


def enunciado(campo: str, r: pd.Series) -> str:
    if campo == "obra":
        return "Há obra ou reforma em andamento no imóvel?"
    if campo == "vinculo":
        if r["vinculo"] == "PROPRIETARIO_LOCADOR":
            return (f"Este imóvel está alugado para outra pessoa? Identificamos um crédito mensal de cerca de "
                    f"{_reais(r['valor_medio_credito_recorrente'])}.")
        return "Qual a sua relação com o imóvel?"
    if campo == "tipo_imovel":
        return "O imóvel é:"
    if campo == "ocupacao":
        return "O imóvel fica vazio por longos períodos, como uma casa usada só nas férias?"
    if campo == "conteudo":
        return (f"Somando móveis, eletrônicos e eletrodomésticos, quanto valem os bens neste imóvel? Estimamos entre "
                f"{_reais(r['conteudo_min'])} e {_reais(r['conteudo_max'])}.")
    if campo == "area_m2":
        return f"A área construída do imóvel fica entre {int(r['area_min_m2'])} e {int(r['area_max_m2'])} m²?"
    if campo == "padrao_construtivo":
        return "Como é o acabamento do imóvel?"
    if campo == "declaracao_unica":
        return ("Confirmo que o imóvel fica em área urbana, tem paredes de alvenaria, não está em obra "
                "estrutural e não é tombado.")
    raise ValueError(campo)


def _texto_pergunta(campo: str, r: pd.Series) -> str:
    rotulos = " / ".join(rotulo for _, rotulo in OPCOES[chave_opcoes(campo, r)])
    return f"{enunciado(campo, r)} ({rotulos})"


MOTIVO = {
    "obra": "define a elegibilidade: imóvel em reforma ou construção fica fora da cobertura (CG 7.1 x/y)",
    "vinculo": "muda o plano: quem recebe aluguel precisa da cobertura de perda de aluguel",
    "tipo_imovel": "muda o plano e a faixa: casa tem mais acessos expostos e estrutura própria",
    "ocupacao": "muda o plano: imóvel desocupado não tem cobertura de roubo (CG, Roubo 2.1 c)",
    "conteudo": "valor dos bens define a necessidade de cobertura de roubo e a faixa de incêndio",
    "area_m2": "área define o custo de reconstrução",
    "padrao_construtivo": "acabamento define o custo de reconstrução por m²",
    "declaracao_unica": "substitui as perguntas de elegibilidade que os dados não respondem (CG 11.1.2: declaração inexata faz perder o direito)",
}


# ---------------------------------------------------------------------------- análise
def analisar(r: pd.Series, ref: regras.Referencias, elegibilidade: str,
             respondidas: frozenset = frozenset()) -> dict:
    """Perguntas em ordem de impacto e confiança geral do imóvel.

    `respondidas`: campos que o cliente já respondeu (inclusive "não sei"); não são
    simulados de novo nem perguntados outra vez.
    """
    plano_base = regras.pontuar_plano(r)["plano_recomendado"]

    muda_plano: dict[str, set] = {}
    for campo, alt in _cenarios_plano(r):
        if campo in respondidas:
            continue
        plano_alt = regras.pontuar_plano(alt)["plano_recomendado"]
        if plano_alt != plano_base:
            muda_plano.setdefault(campo, set()).add(plano_alt)

    largura = _largura_incendio(r, ref)
    estreita = {}
    for campo, alt in (_cenarios_faixa(r) if largura > np.log(FAIXA_ACEITAVEL) else []):
        if campo in respondidas:
            continue
        ganho = 1 - _largura_incendio(alt, ref) / largura if largura > 0 else 0.0
        if ganho >= LIMIAR_ESTREITAMENTO:
            estreita[campo] = max(ganho, estreita.get(campo, 0.0))

    perguntas = []
    if r["alerta_obra_selo"] == A_CONFIRMAR and "obra" not in respondidas:
        perguntas.append({"campo": "obra", "impacto": "elegibilidade", "peso": 3.0})
    for campo, planos in muda_plano.items():
        alternativas = ", ".join(regras.NOME_PLANO[p] for p in regras.ORDEM_PLANOS if p in planos)
        perguntas.append({"campo": campo, "impacto": f"pode mudar o plano para {alternativas}",
                          "peso": 2.0 + estreita.pop(campo, 0.0)})
    for campo, ganho in estreita.items():
        perguntas.append({"campo": campo, "impacto": f"estreita a faixa de incêndio em {ganho:.0%}", "peso": ganho})
    perguntas.sort(key=lambda p: -p["peso"])
    for p in perguntas:
        p["pergunta"] = _texto_pergunta(p["campo"], r)
        p["motivo"] = MOTIVO[p["campo"]]

    if elegibilidade != regras.ELEGIVEL or r["alerta_obra_selo"] == A_CONFIRMAR or len(muda_plano) >= 2:
        confianca = BAIXA
    elif len(muda_plano) == 1:
        confianca = MEDIA
    else:
        confianca = ALTA

    return {
        "confianca_geral": confianca,
        "campos_que_mudam_plano": "|".join(muda_plano),
        "qtd_perguntas": len(perguntas),
        "perguntas": perguntas,
    }


def texto_perguntas(perguntas: list[dict]) -> str:
    """Lista numerada para o template: pergunta, opções e o porquê; declaração no fim."""
    itens = [f"{i}) {p['pergunta']} [por quê: {p['motivo']}]" for i, p in enumerate(perguntas, 1)]
    itens.append(f"{len(perguntas) + 1}) {_texto_pergunta('declaracao_unica', None)}")
    return " | ".join(itens)
