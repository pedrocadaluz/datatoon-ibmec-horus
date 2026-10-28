"""Etapa 03 — Preenche os dois templates oficiais para a base de teste e valida o formato.

Uso (na raiz do projeto):
    python scripts/03_gerar_entrega.py

Saídas:
    entrega/template_resultado_times.csv     uma linha por imóvel (138)
    entrega/template_coberturas_times.csv    uma linha por cobertura fixa do plano e por adicional aplicável
    docs/03_entrega.md                              convenções, testes e exemplos
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from casa_gemea import entrega  # noqa: E402
from casa_gemea.config import BASES, ENCODING, PASTA_DOCS, RAIZ  # noqa: E402
from casa_gemea.pipeline import executar  # noqa: E402

PASTA_ENTREGA = RAIZ / "entrega"


def br(valor: float, casas: int = 0) -> str:
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def tabela_md(df: pd.DataFrame) -> str:
    linhas = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    linhas += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(linhas)


def contagem(serie: pd.Series, unidade: str = "imóveis") -> str:
    n = serie.value_counts()
    return tabela_md(pd.DataFrame({"valor": n.index, unidade: n.values, "%": [br(100 * v / n.sum(), 1) for v in n.values]}))


def exemplo(resultado: pd.DataFrame, coberturas: pd.DataFrame, imovel_id: str) -> list[str]:
    r = resultado.set_index("imovel_id").loc[imovel_id]
    c = coberturas[coberturas["imovel_id"] == imovel_id][["cobertura", "faixa_valor_min", "faixa_valor_max", "confianca_estimativa"]]
    c = c.assign(faixa_valor_min=c["faixa_valor_min"].map(br), faixa_valor_max=c["faixa_valor_max"].map(br))
    c.columns = ["Cobertura", "Mín (R$)", "Máx (R$)", "Confiança"]
    perguntas = [f"   {p.strip()}" for p in r["perguntas_confirmacao"].split(" | ")]
    return [
        f"### {imovel_id} — {r['plano_recomendado']} · confiança {r['confianca_geral']} · elegível: {r['elegivel']}",
        "",
        f"**Justificativa:** {r['justificativa_recomendacao']}",
        "",
        "**Perguntas de confirmação:**",
        "",
        *[f"-{p}" for p in perguntas],
        "",
        tabela_md(c),
        "",
    ]


def escrever_relatorio(resultado: pd.DataFrame, coberturas: pd.DataFrame, testes: pd.DataFrame) -> Path:
    exemplos = []
    for conf in ["ALTA", "MEDIA", "BAIXA"]:
        exemplos.append(resultado.loc[resultado["confianca_geral"] == conf, "imovel_id"].iloc[0])
    qtd_perguntas = resultado["perguntas_confirmacao"].str.count(r" \| ")  # itens − 1 = sem a declaração

    p = [
        "# Etapa 03 — Entrega dos templates",
        f"_Gerado por `scripts/03_gerar_entrega.py` em {date.today():%d/%m/%Y}._",
        "",
        "Arquivos em `entrega/`, com o mesmo nome, colunas e ordem de linhas dos templates oficiais da base Teste Comum.",
        "",
        "| Arquivo | Linhas |",
        "|---|---|",
        f"| `template_resultado_times.csv` | {len(resultado)} imóveis |",
        f"| `template_coberturas_times.csv` | {len(coberturas)} coberturas |",
        "",
        "## Testes de formato e coerência",
        "",
        tabela_md(testes.assign(ok=testes["ok"].map({True: "✅", False: "❌"}))),
        "",
        "## Convenções dos campos",
        "",
        "Os campos dos templates são de formato livre e documentado (dicionário de dados).",
        "",
        "| Campo | Valores |",
        "|---|---|",
        "| `elegivel` | `SIM` · `PENDENTE_VALIDACAO` (plano provisório; vai ao gerente) · `NAO` |",
        "| `motivo_inelegibilidade` | Vazio quando `SIM`; senão, o motivo e a cláusula |",
        "| `tipo_imovel_sugerido` | `APARTAMENTO` · `CASA` · `CASA_EM_CONDOMINIO` · `INDEFINIDO` |",
        "| `uso_imovel_sugerido` | `MORADIA_HABITUAL` · `TEMPORADA_OU_SEGUNDA_RESIDENCIA` · `ALUGADO_A_TERCEIROS` |",
        "| `tipo_vinculo_sugerido` | `INQUILINO` · `PROPRIETARIO_FINANCIADO` · `PROPRIETARIO_QUITADO` (sem financiamento ativo) · `PROPRIETARIO_LOCADOR` |",
        "| `plano_recomendado` | `ESSENCIAL` · `PRATICO` · `TOTAL` (nomes do catálogo) |",
        "| `coberturas_recomendadas` | Coberturas fixas do plano e adicionais aplicáveis com faixa (`EQUIPAMENTOS_PORTATEIS`, `BICICLETA`), separadas por ` \\| ` |",
        "| `confianca_geral` | `ALTA` (nenhuma resposta plausível muda o plano) · `MEDIA` (um campo pode mudar) · `BAIXA` (dois ou mais, ou elegibilidade pendente) |",
        "| `justificativa_recomendacao` | Recomendação inicial → Casa Gêmea com selos → por que este plano → por que não o de baixo → por que não o de cima → o que pode mudar o plano |",
        "| `perguntas_confirmacao` | Perguntas fechadas em ordem de impacto, com opções e o porquê, separadas por ` \\| `; a última é sempre a declaração única de elegibilidade |",
        "| `fontes_publicas_adicionais` | Condições Gerais BB, CUB da UF do imóvel, fatores Sinduscon-MG e dado de sinistros, com link |",
        "| `faixa_valor_min` / `faixa_valor_max` | Reais inteiros, sem \"R$\" e sem separador de milhar |",
        "| `confianca_estimativa` | `ALTA` · `MEDIA` · `BAIXA` (confiança dos dados que a faixa usa) |",
        "",
        "A recomendação é **inicial**: usa só os dados que o banco já tem. As perguntas confirmam ou ajustam o plano e estreitam as faixas.",
        "",
        "## Resumo",
        "",
        "### Elegibilidade",
        "",
        contagem(resultado["elegivel"]),
        "",
        "### Plano",
        "",
        contagem(resultado["plano_recomendado"]),
        "",
        "### Confiança geral",
        "",
        contagem(resultado["confianca_geral"]),
        "",
        "### Perguntas por imóvel (sem contar a declaração única)",
        "",
        contagem(qtd_perguntas),
        "",
        "### Confiança das faixas",
        "",
        contagem(coberturas["confianca_estimativa"], "coberturas"),
        "",
        "## Exemplos (um por nível de confiança)",
        "",
    ]
    for imovel_id in exemplos:
        p += exemplo(resultado, coberturas, imovel_id)

    caminho = PASTA_DOCS / "03_entrega.md"
    caminho.write_text("\n".join(p) + "\n", encoding="utf-8")
    return caminho


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    PASTA_ENTREGA.mkdir(parents=True, exist_ok=True)

    res = executar()
    template_res = pd.read_csv(BASES["teste"] / "template_resultado_times.csv", encoding=ENCODING)
    template_cob = pd.read_csv(BASES["teste"] / "template_coberturas_times.csv", encoding=ENCODING)
    catalogo = res.bases["teste"]["catalogo_coberturas_fixas_planos"]

    resultado = entrega.montar_resultado(res.recomendacoes["teste"], res.casas["teste"], template_res)
    coberturas = entrega.montar_coberturas(res.coberturas["teste"], template_res)
    assert list(coberturas.columns) == list(template_cob.columns), "colunas diferentes do template de coberturas"

    testes = entrega.validar(resultado, coberturas, template_res, catalogo)
    resultado.to_csv(PASTA_ENTREGA / "template_resultado_times.csv", index=False, encoding=ENCODING)
    coberturas.to_csv(PASTA_ENTREGA / "template_coberturas_times.csv", index=False, encoding=ENCODING)
    print(f"✔ entrega/template_resultado_times.csv: {len(resultado)} linhas")
    print(f"✔ entrega/template_coberturas_times.csv: {len(coberturas)} linhas")

    relatorio = escrever_relatorio(resultado, coberturas, testes)
    print(f"✔ docs/{relatorio.name}")
    for t in testes.itertuples():
        print(("✔" if t.ok else "✘"), t.teste)
    if not testes["ok"].all():
        sys.exit("Há testes de formato falhando: a entrega não está pronta.")


if __name__ == "__main__":
    main()
