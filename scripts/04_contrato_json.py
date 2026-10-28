"""Etapa 04 — Contrato JSON do motor: jornada de exemplo ou chamada avulsa.

Uso (na raiz do projeto):
    python scripts/04_contrato_json.py                 # jornada de exemplo + documentação
    python scripts/04_contrato_json.py entrada.json    # responde uma chamada (saída no terminal)

Saídas da jornada de exemplo:
    saidas/contrato/jornada_<imovel>_passo<N>_{entrada,saida}.json
    docs/04_contrato_json.md
"""

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from casa_gemea.config import PASTA_DOCS, PASTA_SAIDAS  # noqa: E402
from casa_gemea.motor import VERSAO_CONTRATO, Motor  # noqa: E402

PASTA_CONTRATO = PASTA_SAIDAS / "contrato"

# Jornada de exemplo: locador com sinal de reforma (CASO_00003), respondendo em ordem de impacto.
IMOVEL_EXEMPLO = "IMO_CASO_00003_01"
JORNADA = [
    {},
    {"obra": "NAO"},
    {"obra": "NAO", "vinculo": "PROPRIETARIO_QUITADO"},
    {"obra": "NAO", "vinculo": "PROPRIETARIO_QUITADO", "area_m2": 160, "declaracao_unica": "SIM"},
]


def br(valor: float) -> str:
    return f"{valor:,.0f}".replace(",", ".")


def resumo_passo(n: int, entrada: dict, saida: dict) -> list[str]:
    incendio = next((c for c in saida["coberturas"] if c["cobertura"].startswith("INCENDIO")), None)
    faixa = f"R$ {br(incendio['faixa_valor_min'])} – {br(incendio['faixa_valor_max'])}" if incendio else "—"
    perguntas = ", ".join(p["id"] for p in saida["proximas_perguntas"]) or "nenhuma"
    return [
        f"| {n} | {', '.join(f'{k}={v}' for k, v in entrada['respostas'].items()) or '(nenhuma)'} "
        f"| {saida['recomendacao']['plano']} | {saida['recomendacao']['confianca_geral']} "
        f"| {faixa} | {saida['canal']['semaforo']} | {saida['status']} | {perguntas} |"
    ]


def escrever_doc(passos: list[tuple[dict, dict]]) -> Path:
    entrada_ex, saida_ex = passos[0]
    saida_curta = dict(saida_ex, coberturas=saida_ex["coberturas"][:2] + [{"...": "uma entrada por cobertura do plano"}])
    p = [
        "# Etapa 04 — Contrato JSON do motor",
        f"_Gerado por `scripts/04_contrato_json.py` em {date.today():%d/%m/%Y}. Versão do contrato: {VERSAO_CONTRATO}._",
        "",
        "Um único contrato atende **app, gerente, SAC e agentes autônomos**. O canal envia o imóvel e as respostas "
        "coletadas até agora; o motor atualiza a Casa Gêmea (respostas viram selo `CONFIRMADO`), refaz elegibilidade, "
        "plano, faixas e confiança, e devolve as **próximas perguntas** em ordem de impacto. O motor não guarda estado: "
        "cada chamada traz todas as respostas já dadas, o que facilita auditoria e reprocessamento.",
        "",
        "```",
        "canal ──► { imovel_id, respostas } ──► motor ──► { casa_gemea, recomendacao, coberturas, proximas_perguntas, canal }",
        "  ▲                                                                                  │",
        "  └──────────────────── cliente responde a próxima pergunta ◄───────────────────────┘",
        "```",
        "",
        "## Entrada",
        "",
        "| Campo | Tipo | Descrição |",
        "|---|---|---|",
        "| `versao_contrato` | texto | `\"1.0\"` |",
        "| `imovel_id` | texto | Imóvel da base (ex.: `IMO_CASO_00003_01`) |",
        "| `respostas` | objeto | Pergunta → resposta. Vazio na primeira chamada. |",
        "",
        "| Pergunta (`id`) | Respostas aceitas |",
        "|---|---|",
        "| `obra` | `NAO` · `REFORMA_PEQUENA` · `OBRA_ESTRUTURAL` (→ inelegível até o fim da obra, CG 7.1) |",
        "| `vinculo` | `INQUILINO` · `PROPRIETARIO_FINANCIADO` · `PROPRIETARIO_QUITADO` · `PROPRIETARIO_LOCADOR` · `IMOVEL_VAZIO` |",
        "| `tipo_imovel` | `APARTAMENTO` · `CASA` · `CASA_EM_CONDOMINIO` |",
        "| `ocupacao` | `OCUPADO` · `DESOCUPADO` (→ sem cobertura de roubo, CG Roubo 2.1 c) |",
        "| `conteudo` | `MENOR` · `NA_FAIXA` · `MAIOR` · `NAO_SEI` · ou valor em reais |",
        "| `area_m2` | `NA_FAIXA` · `MENOR` · `MAIOR` · `NAO_SEI` · ou área em m² |",
        "| `padrao_construtivo` | `ECONOMICO` · `NORMAL` · `SUPERIOR` · `NAO_SEI` |",
        "| `declaracao_unica` | `SIM` · `NAO` (→ elegibilidade pendente, vai ao gerente) |",
        "",
        "`NAO_SEI` é sempre aceito: a pergunta sai da lista, a faixa continua larga e a cotação não trava. "
        "Resposta inválida devolve `{\"erro\": ...}` sem alterar nada.",
        "",
        "## Saída",
        "",
        "| Campo | Descrição |",
        "|---|---|",
        "| `status` | `RECOMENDACAO_INICIAL` (há perguntas) · `RECOMENDACAO_CONFIRMADA` (nada mais a perguntar) · `ENCAMINHAR_GERENTE` · `INELEGIVEL` |",
        "| `elegibilidade` | `status` (ELEGIVEL, ELEGIVEL_CONDICIONADO, INELEGIVEL) e `motivo` |",
        "| `casa_gemea` | Cada campo com `valor`, `selo` (OBSERVADO, ESTIMADO, A_CONFIRMAR, CONFIRMADO), `confianca` e `evidencia`; faixas de área e bens |",
        "| `recomendacao` | Plano, confiança geral, por que este plano, por que não o de baixo e o de cima, campos que ainda podem mudar o plano |",
        "| `coberturas` | Faixa mínima e máxima (LMI), confiança, regra, justificativa, o que confirmar e observação |",
        "| `proximas_perguntas` | Em ordem de impacto: `id`, `pergunta`, `opcoes` (valor + rótulo), `aceita_numero`, `impacto`, `motivo` |",
        "| `canal` | Semáforo e canal sugerido |",
        "",
        "Cada canal usa os mesmos campos de outro jeito: o **app** mostra `opcoes` como botões; o **gerente** vê também "
        "`motivo` e `impacto` de cada pergunta; o **SAC** lê `pergunta` e `opcoes` em voz alta; um **agente** chama o "
        "motor em laço até `status` ≠ `RECOMENDACAO_INICIAL`.",
        "",
        "## Jornada de exemplo",
        "",
        f"Imóvel `{IMOVEL_EXEMPLO}`: casa, possível locador (crédito mensal de aluguel) e sinal de reforma. "
        "Arquivos completos em `saidas/contrato/`.",
        "",
        "| Passo | Respostas enviadas | Plano | Confiança | Faixa de incêndio | Semáforo | Status | Próximas perguntas |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for n, (entrada, saida) in enumerate(passos):
        p += resumo_passo(n, entrada, saida)
    p += [
        "",
        "## Exemplo de chamada (passo 0)",
        "",
        "Entrada:",
        "",
        "```json",
        json.dumps(entrada_ex, ensure_ascii=False, indent=2),
        "```",
        "",
        "Saída (coberturas resumidas):",
        "",
        "```json",
        json.dumps(saida_curta, ensure_ascii=False, indent=2),
        "```",
    ]
    caminho = PASTA_DOCS / "04_contrato_json.md"
    caminho.write_text("\n".join(p) + "\n", encoding="utf-8")
    return caminho


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    motor = Motor()

    if len(sys.argv) > 1:
        entrada = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        print(json.dumps(motor.recomendar(entrada), ensure_ascii=False, indent=2))
        return

    PASTA_CONTRATO.mkdir(parents=True, exist_ok=True)
    passos = []
    for n, respostas in enumerate(JORNADA):
        entrada = {"versao_contrato": VERSAO_CONTRATO, "imovel_id": IMOVEL_EXEMPLO, "respostas": respostas}
        saida = motor.recomendar(entrada)
        for tipo, conteudo in (("entrada", entrada), ("saida", saida)):
            destino = PASTA_CONTRATO / f"jornada_{IMOVEL_EXEMPLO}_passo{n}_{tipo}.json"
            destino.write_text(json.dumps(conteudo, ensure_ascii=False, indent=2), encoding="utf-8")
        passos.append((entrada, saida))
        r = saida["recomendacao"]
        print(f"passo {n}: {saida['status']:<24} plano={r['plano']:<9} confiança={r['confianca_geral']:<5} "
              f"semáforo={saida['canal']['semaforo']:<8} perguntas={[p['id'] for p in saida['proximas_perguntas']]}")
    print(f"✔ docs/{escrever_doc(passos).name}")


if __name__ == "__main__":
    main()
