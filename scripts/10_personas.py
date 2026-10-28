"""Etapa 10: três personas e como o motor se comporta com cada uma.

Uso (na raiz do projeto):
    python scripts/10_personas.py

Saídas:
    saidas/personas/<imovel_id>.json     jornada passo a passo (respostas e saída do motor)
    docs/11_personas.md                  comparativo das três personas

As personas são imóveis da base de teste (dados fictícios); os nomes são inventados só para a demonstração. Cada jornada responde às
perguntas que o motor escolheu, em uma ordem plausível, e mostra como plano, adicionais,
canal e tom mudam.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from casa_gemea.config import PASTA_DOCS, PASTA_SAIDAS  # noqa: E402
from casa_gemea.motor import RESPOSTAS_ADICIONAIS, Motor  # noqa: E402

PERSONAS = [
    {
        "imovel_id": "IMO_CASO_00008_01",
        "nome": "Marina",
        "resumo": "Inquilina de apartamento em Fortaleza, com 3 dependentes e pet, e usa muito o app do banco.",
        "respostas": [{"conteudo": "NA_FAIXA"}, {"declaracao_unica": "SIM"}],
    },
    {
        "imovel_id": "IMO_CASO_00016_01",
        "nome": "Rafael",
        "resumo": "Dono de casa financiada no Rio de Janeiro, com muitos eletrônicos, que acabou de gastar muito em material de construção.",
        "respostas": [{"obra": "REFORMA_PEQUENA"}, {"declaracao_unica": "SIM"}, {"equipamentos": "SIM"}],
    },
    {
        "imovel_id": "IMO_CASO_00059_01",
        "nome": "Helena",
        "resumo": "Tem um apartamento de temporada em Fortaleza, que passa meses vazio, e quase não usa o app.",
        "respostas": [{"ocupacao": "DESOCUPADO"}, {"declaracao_unica": "SIM"}, {"desocupacao": "SIM"}],
    },
]


def br(valor) -> str:
    return "R$ " + f"{valor:,.0f}".replace(",", ".")


def resumo(saida: dict) -> dict:
    """Campos que o comparativo mostra de cada passo."""
    p = saida["personalizacao"]
    incendio = next((c for c in saida["coberturas"] if c["cobertura"].startswith("INCENDIO")), None)
    return {
        "status": saida["status"],
        "elegibilidade": saida["elegibilidade"]["status"],
        "plano": saida["recomendacao"]["plano"],
        "confianca": saida["recomendacao"]["confianca_geral"],
        "semaforo": saida["canal"]["semaforo"],
        "canal": saida["canal"]["sugerido"],
        "faixa_incendio": [incendio["faixa_valor_min"], incendio["faixa_valor_max"]] if incendio else None,
        "adicionais": [a["id"] for a in p["adicionais_sugeridos"]],
        "perguntas_restantes": [q["id"] for q in saida["proximas_perguntas"]],
        "perguntas_evitadas": saida["jornada"]["perguntas_evitadas"],
    }


def rodar_jornada(motor: Motor, persona: dict) -> list[dict]:
    respostas: dict = {}
    passos = []
    for i, nova in enumerate([{}] + persona["respostas"]):
        respostas = {**respostas, **nova}
        entrada = {"versao_contrato": "1.0", "imovel_id": persona["imovel_id"], "respostas": dict(respostas)}
        saida = motor.recomendar(entrada)
        passos.append({"passo": i, "resposta_dada": nova, "entrada": entrada, "saida": saida, "resumo": resumo(saida)})
    return passos


def escrever_relatorio(jornadas: dict[str, list[dict]]) -> Path:
    linhas = [
        "# Etapa 11: três personas e o comportamento do motor",
        "",
        "_Gerado por `scripts/10_personas.py`. Dados fictícios (base de teste comum); os nomes das personas são inventados para a demonstração. Cada jornada está em `saidas/personas/`._",
        "",
        "O mesmo motor, com os mesmos dados do banco, produz recomendações, adicionais, canal e tom diferentes para cada perfil. "
        "Nenhuma regra usa idade ou renda; a personalização vem do imóvel, do vínculo, das compras, de dependentes e pet e do uso do app.",
        "",
    ]
    inicial = {p["imovel_id"]: jornadas[p["imovel_id"]][0] for p in PERSONAS}
    final = {p["imovel_id"]: jornadas[p["imovel_id"]][-1] for p in PERSONAS}

    linhas += ["## Comparativo", "", "| | " + " | ".join(f"**{p['nome']}**" for p in PERSONAS) + " |", "|---|" + "---|" * len(PERSONAS)]

    def linha(rotulo, fn):
        linhas.append(f"| {rotulo} | " + " | ".join(fn(p) for p in PERSONAS) + " |")

    linha("Imóvel", lambda p: f"`{p['imovel_id']}`")
    linha("Quem é", lambda p: p["resumo"])
    linha("Arquétipo", lambda p: final[p["imovel_id"]]["saida"]["personalizacao"]["perfil"]["rotulo"])
    linha("Jornada e tom", lambda p: f"{final[p['imovel_id']]['saida']['personalizacao']['perfil']['jornada']}: "
          f"{final[p['imovel_id']]['saida']['personalizacao']['perfil']['tom']}")
    modos = {"NOVA_APOLICE": "nova apólice", "REVISAO_DE_SEGURO": "revisão do seguro atual"}
    linha("Modo", lambda p: modos[final[p["imovel_id"]]["saida"]["personalizacao"]["perfil"]["modo"]])
    linha("Plano (início)", lambda p: inicial[p["imovel_id"]]["resumo"]["plano"].title())
    linha("Plano (fim)", lambda p: final[p["imovel_id"]]["resumo"]["plano"].title())
    linha("Canal (início)", lambda p: f"{inicial[p['imovel_id']]['resumo']['semaforo'].lower()}, {inicial[p['imovel_id']]['resumo']['canal'].lower()}")
    linha("Canal (fim)", lambda p: f"{final[p['imovel_id']]['resumo']['semaforo'].lower()}, {final[p['imovel_id']]['resumo']['canal'].lower()}")
    linha("Faixa de incêndio (fim)", lambda p: f"{br(final[p['imovel_id']]['resumo']['faixa_incendio'][0])} a {br(final[p['imovel_id']]['resumo']['faixa_incendio'][1])}")
    linha("Adicionais sugeridos", lambda p: ", ".join(final[p["imovel_id"]]["resumo"]["adicionais"]) or "nenhum")
    nucleo = lambda p: sum(1 for r in p["respostas"] for k in r if k not in RESPOSTAS_ADICIONAIS and k != "declaracao_unica")
    linha("Perguntas feitas", lambda p: f"{nucleo(p)} mais a declaração única" + (" e resposta a adicional" if any(k in RESPOSTAS_ADICIONAIS for r in p["respostas"] for k in r) else ""))
    linha("Perguntas evitadas (de 8)", lambda p: str(final[p["imovel_id"]]["resumo"]["perguntas_evitadas"]))
    linha("Assistências em destaque", lambda p: ", ".join(a["nome"] for a in final[p["imovel_id"]]["saida"]["personalizacao"]["assistencias"]["destaque"]) or "base do plano")
    prem = lambda p: (final[p["imovel_id"]]["saida"]["personalizacao"]["assistencias"]["beneficio_premium_sugerido"] or {}).get("nome", "não se aplica (plano sem benefício premium)")
    linha("Benefício premium sugerido", prem)
    linha("Notificação do app", lambda p: f"**{final[p['imovel_id']]['saida']['personalizacao']['mensagem_do_app']['titulo']}**: "
          f"{final[p['imovel_id']]['saida']['personalizacao']['mensagem_do_app']['texto']}")
    linha("Alertas", lambda p: "; ".join(a["tipo"].lower() for a in final[p["imovel_id"]]["saida"]["personalizacao"]["alertas"]) or "nenhum")

    for persona in PERSONAS:
        passos = jornadas[persona["imovel_id"]]
        linhas += ["", f"## {persona['nome']}: {passos[0]['saida']['personalizacao']['perfil']['rotulo']}", "", persona["resumo"], "",
                   "| Passo | Resposta | Plano | Elegibilidade | Canal | Faixa de incêndio | Adicionais |", "|---|---|---|---|---|---|---|"]
        for passo in passos:
            r = passo["resumo"]
            resposta = ", ".join(f"{k} = {v}" for k, v in passo["resposta_dada"].items()) or "(nenhuma)"
            faixa = f"{br(r['faixa_incendio'][0])} a {br(r['faixa_incendio'][1])}" if r["faixa_incendio"] else "-"
            linhas.append(f"| {passo['passo']} | {resposta} | {r['plano'].title()} | {r['elegibilidade'].lower()} | {r['semaforo'].lower()} | {faixa} | {', '.join(r['adicionais']) or '-'} |")
        saida = passos[-1]["saida"]
        linhas += ["", "**Por que este plano** (rastro do motor):", ""]
        plano = next(p for p in saida["explicacao"]["passos"] if p["id"] == "plano")
        for sinal in plano["sinais_pratico"] + plano["sinais_total"]:
            linhas.append(f"- {sinal['pontos']} ponto(s): {sinal['sinal']}")
        linhas += ["", "**Adicionais e por quê:**", ""]
        for a in saida["personalizacao"]["adicionais_sugeridos"]:
            faixa = f" Faixa sugerida: {br(a['faixa_valor_min'])} a {br(a['faixa_valor_max'])}." if "faixa_valor_min" in a else ""
            linhas.append(f"- **{a['nome']}** (necessidade {a['necessidade']}): {a['por_que_para_voce']}{faixa} ({a['clausula']})")
        if saida["personalizacao"]["alertas"]:
            linhas += ["", "**Alertas:**", ""] + [f"- {a['texto']}" for a in saida["personalizacao"]["alertas"]]

    linhas += ["", "## Como ler", "",
               "- **Jornada EXPRESS, GUIADA ou HUMANA:** vem da maturidade digital do cliente e muda ritmo, texto e canal, nunca o plano nem o valor.",
               "- **Adicionais:** só aparecem com sinal nos dados e viram pergunta quando falta confirmação. O índice de necessidade é premissa da equipe, não probabilidade de sinistro.",
               "- **Recibos:** cada personalização mostra os dados usados (campo `personalizacao.recibos`), e o cliente pode desligá-la."]
    caminho = PASTA_DOCS / "11_personas.md"
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return caminho


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    motor = Motor()
    pasta = PASTA_SAIDAS / "personas"
    pasta.mkdir(exist_ok=True)
    jornadas = {}
    for persona in PERSONAS:
        passos = rodar_jornada(motor, persona)
        jornadas[persona["imovel_id"]] = passos
        (pasta / f"{persona['imovel_id']}.json").write_text(
            json.dumps({"persona": persona["nome"], "resumo": persona["resumo"], "passos": passos}, ensure_ascii=False, indent=2),
            encoding="utf-8")
        r = passos[-1]["resumo"]
        print(f"✔ {persona['nome']}: {r['plano']} · {r['semaforo']} · adicionais {r['adicionais']}")
    print(f"✔ docs/{escrever_relatorio(jornadas).name}")


if __name__ == "__main__":
    main()
