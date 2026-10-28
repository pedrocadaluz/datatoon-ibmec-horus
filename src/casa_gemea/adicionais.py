"""Personalização: coberturas adicionais facultativas sugeridas a partir da Casa Gêmea.

O produto permite incluir, com prêmio adicional, coberturas além do plano (CG 4.1:
"É facultada a contratação das Coberturas Adicionais"). O motor sugere apenas as que
têm sinal nos dados do cliente; as demais ficam disponíveis, mas não são empurradas.

- Responsabilidade Civil Familiar (CG 4.1 m): pet ou dependentes, quando o plano não é o Total.
- Equipamentos Portáteis (CG 4.1 g): eletrônicos de valor; cobre acidente (queda, quebra),
  que nenhum plano cobre. Os aparelhos são listados um a um na contratação (CG, Portáteis 1.2).
- Bicicleta (CG 4.1 b): itens de lazer de valor; vira pergunta, porque "lazer" não diz o que é.
- Desocupação Temporária (CG 4.1 f): segunda residência ou imóvel vazio; cobre períodos
  de 30 a 60 dias sem moradores, com aviso de 15 dias.

Não sugerimos Alagamento, Danos por Chuva nem Rompimento de Tubulações: os três planos já
trazem Danos por Água, que os contempla e não pode ser contratada junto com eles (CG 4.3).

Guardrail: nenhuma sugestão usa idade ou renda; pet e dependentes só indicam necessidade.
Não há preço na base, então a sugestão diz o motivo e o valor de referência, não o custo.
"""

import pandas as pd

from .regras import NOME_PLANO, _plural, _reais

# Limiares ~ quinto superior da base de teste: sugerir só onde o valor em jogo é alto.
PORTATEIS_RELEVANTE = 15_000  # R$ em eletrônicos do cliente para sugerir Portáteis
LAZER_RELEVANTE = 5_000       # R$ em itens de lazer para perguntar sobre bicicleta

NOME_ADICIONAL = {
    "RESPONSABILIDADE_CIVIL_FAMILIAR": "Responsabilidade Civil Familiar",
    "EQUIPAMENTOS_PORTATEIS": "Equipamentos Portáteis",
    "BICICLETA": "Bicicleta",
    "DESOCUPACAO_TEMPORARIA": "Desocupação Temporária do Imóvel",
}
NAO_SUGERIDOS = (
    "Alagamento, Danos por Chuva e Rompimento de Tubulações não são sugeridos: "
    "Danos por Água, presente em todos os planos, já os contempla (CG 4.3)."
)


def sugerir(r: pd.Series, plano: str, faixas: list[dict]) -> list[dict]:
    """Adicionais com sinal nos dados. Cada item: adicional, nome, motivo, faixa (ou None), cg."""
    if not plano:
        return []
    k = r["fracao_conteudo_do_cliente"]
    desocupado = r.get("imovel_desocupado", False) or r["uso_imovel"] == "TEMPORADA_OU_SEGUNDA_RESIDENCIA"
    faixa_de = {f["cobertura"]: (f["faixa_valor_min"], f["faixa_valor_max"]) for f in faixas}
    itens = []

    def add(codigo, motivo, cg, faixa=None):
        itens.append({"adicional": codigo, "nome": NOME_ADICIONAL[codigo], "motivo": motivo,
                      "faixa": faixa, "cg": cg})

    pessoas = [
        "pet" if r["possui_pet_informado"] == "SIM" else "",
        _plural(int(r["quantidade_dependentes"]), "dependente", "dependentes") if r["quantidade_dependentes"] > 0 else "",
    ]
    pessoas = " e ".join(p for p in pessoas if p)
    if plano != "TOTAL" and pessoas:
        add("RESPONSABILIDADE_CIVIL_FAMILIAR",
            f"há {pessoas} na casa; o {NOME_PLANO[plano]} não cobre danos que pessoas "
            "ou animais da casa causem a terceiros",
            "CG 4.1 m; RC Familiar 1.1", faixa_de.get("RESPONSABILIDADE_CIVIL_FAMILIAR"))

    eletronicos = round(max(r["bens_ponderado_eletronico"], r["compras_eletronicos_36m"]) * k, -2)
    if not desocupado and eletronicos >= PORTATEIS_RELEVANTE:
        minimo = r["bens_ponderado_eletronico"] * k
        add("EQUIPAMENTOS_PORTATEIS",
            f"há cerca de {_reais(eletronicos)} em eletrônicos; o {NOME_PLANO[plano]} cobre "
            + ("dano elétrico e roubo" if plano != "ESSENCIAL" else "dano elétrico")
            + ", mas não a queda ou quebra acidental de notebook, tablet e câmera",
            "CG 4.1 g; Equipamentos Portáteis 1.1",
            (round(max(minimo, 0.5 * eletronicos), -2), eletronicos))

    lazer = round(r["bens_ponderado_item_lazer"] * k, -2)
    if not desocupado and lazer >= LAZER_RELEVANTE:
        add("BICICLETA",
            f"há cerca de {_reais(lazer)} em itens de lazer; se houver bicicleta, esta cobertura protege "
            "o roubo também fora de casa",
            "CG 4.1 b; Bicicleta 1.1")

    if desocupado:
        add("DESOCUPACAO_TEMPORARIA",
            "o imóvel parece ficar vazio parte do ano; esta cobertura mantém a proteção em períodos "
            "de 30 a 60 dias sem moradores (avisando com 15 dias de antecedência)",
            "CG 4.1 f; Desocupação Temporária 1.2 a 1.4")
    return itens


def texto(itens: list[dict]) -> str:
    """Uma frase por adicional, para justificativa e relatórios."""
    partes = []
    for a in itens:
        faixa = f" (referência {_reais(a['faixa'][0])}–{_reais(a['faixa'][1])})" if a["faixa"] else ""
        partes.append(f"{a['nome']}{faixa}: {a['motivo']}")
    return "; ".join(partes)
