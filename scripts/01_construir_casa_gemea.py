"""Etapa 01 — Constrói a Casa Gêmea das duas bases e gera o relatório da etapa.

Uso (na raiz do projeto):
    python scripts/01_construir_casa_gemea.py

Saídas:
    saidas/casa_gemea_desenvolvimento.csv
    saidas/casa_gemea_teste.csv
    docs/01_casa_gemea.md
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from casa_gemea import area  # noqa: E402
from casa_gemea.carregar import ler_base, montar_tabela_imoveis  # noqa: E402
from casa_gemea.config import ENCODING, PASTA_DOCS, PASTA_SAIDAS  # noqa: E402
from casa_gemea.inferencias import (  # noqa: E402
    COLUNAS_CASA_GEMEA,
    construir_casa_gemea,
    inferir_tipo,
)

CAMPOS_RELATORIO = [
    ("tipo_imovel", "Tipo de imóvel"),
    ("vinculo", "Vínculo com o imóvel"),
    ("uso_imovel", "Uso do imóvel"),
    ("area_m2_selo", "Origem da área"),
    ("padrao_construtivo_selo", "Padrão construtivo"),
    ("material_parede", "Material da parede externa"),
    ("alerta_obra", "Sinal de obra"),
    ("conteudo_confianca", "Confiança no valor do conteúdo"),
]


def br(valor: float, casas: int = 0) -> str:
    """Formata número no padrão brasileiro (1.234,5)."""
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def tabela_md(contagem: pd.DataFrame) -> str:
    linhas = ["| " + " | ".join(contagem.columns) + " |", "|" + "---|" * len(contagem.columns)]
    celula = lambda v: br(v, 1) if isinstance(v, float) else str(v)
    linhas += ["| " + " | ".join(celula(v) for v in row) + " |" for row in contagem.itertuples(index=False)]
    return "\n".join(linhas)


def distribuicao(casas: dict[str, pd.DataFrame], campo: str) -> pd.DataFrame:
    partes = []
    for nome, df in casas.items():
        partes.append(df[campo].value_counts().rename(f"{nome} (n)"))
        partes.append((df[campo].value_counts(normalize=True) * 100).round(1).rename(f"{nome} (%)"))
    tabela = pd.concat(partes, axis=1).fillna(0)
    for col in tabela.columns:
        tabela[col] = tabela[col].astype(int) if col.endswith("(n)") else tabela[col]
    return tabela.rename_axis("valor").reset_index()


def escrever_relatorio(casas: dict[str, pd.DataFrame], modelo: area.ModeloArea) -> Path:
    m = modelo.metricas
    dev = casas["desenvolvimento"]
    nomes_coef = ["intercepto", "log(IPTU anual)", "log(energia mensal)", "é casa"] + [
        f"município: {x}" for x in modelo.municipios[1:]
    ]
    coefs = pd.DataFrame({"variável": nomes_coef, "coeficiente": modelo.coeficientes.round(3).astype(float)})

    partes = [
        "# Etapa 01 — Casa Gêmea",
        f"_Gerado por `scripts/01_construir_casa_gemea.py` em {date.today():%d/%m/%Y}._",
        "",
        "A Casa Gêmea é a cópia virtual de cada imóvel, montada só com os sinais disponíveis. "
        "Cada informação recebe um **selo** (`OBSERVADO`, `ESTIMADO` ou `A_CONFIRMAR`), uma "
        "**confiança** (`ALTA`, `MEDIA`, `BAIXA`) e a **evidência** usada.",
        "",
        "| Base | Imóveis | Clientes |",
        "|---|---|---|",
        *[f"| {n} | {len(df)} | {df['cliente_id'].nunique()} |" for n, df in casas.items()],
        "",
        "## Como cada campo foi inferido",
        "",
        "| Campo | Sinais usados | Regra |",
        "|---|---|---|",
        "| Tipo de imóvel | complemento, termos apartamento/casa/condomínio, condomínio pago | Apartamento ou casa pelo complemento; casa + condomínio = casa em condomínio. Apartamento sem condomínio pago tem confiança média. |",
        "| Vínculo | aluguel pago, parcela de financiamento, crédito compatível com aluguel | Inquilino > financiado > locador > quitado (ausência de sinais). Sinais simultâneos = a confirmar. |",
        "| Uso | endereço principal, nº de imóveis do cliente, vínculo | Principal = moradia habitual; 2º imóvel não principal = temporada/segunda residência; locador = alugado a terceiros. |",
        "| Área | área cadastrada; senão IPTU, energia, tipo, município | Modelo log-linear (detalhes abaixo) com faixa de 80%. |",
        "| Padrão construtivo | cadastro | Ausente → `NORMAL` como referência, a confirmar. |",
        "| Parede externa | cadastro | Ausente → a confirmar (requisito de elegibilidade). |",
        "| Sinal de obra | gasto com material de construção em 24 meses | 0 / < 10 mil (leve) / < 30 mil (moderada) / ≥ 30 mil (possível obra relevante). |",
        "| Conteúdo | bens vinculados e compras de 36 meses | Mín = bens ponderados pela probabilidade; máx = maior entre bens cadastrados e compras. |",
        "",
        "**Não usados em nenhuma inferência:** idade, renda, origem e confiança da renda.",
        "",
        "## Modelo de área",
        "",
        "`log(área) = b0 + b1·log(IPTU) + b2·log(energia) + b3·[casa] + efeito do município`",
        "",
        "Treinado nos imóveis com área real da base de desenvolvimento e avaliado com validação cruzada de 5 dobras.",
        "",
        "| Métrica | Valor |",
        "|---|---|",
        f"| Imóveis com área real (treino) | {m['imoveis_treino']} |",
        f"| Erro médio absoluto | {br(m['erro_medio_absoluto_m2'], 1)} m² |",
        f"| Erro percentual mediano | {br(m['erro_percentual_mediano'] * 100, 1)}% |",
        f"| R² (escala log) | {br(m['r2_log'], 2)} |",
        f"| Faixa de 80% contém a área real | {br(m['cobertura_faixa_80'] * 100, 1)}% dos casos |",
        f"| Largura da faixa em relação à estimativa | {m['largura_relativa_faixa']} |",
        "",
        "Variáveis testadas e descartadas: condomínio (correlação 0,02 com a área), renda (0,01) e "
        "padrão construtivo (área mediana igual entre padrões).",
        "",
        "<details><summary>Coeficientes</summary>",
        "",
        tabela_md(coefs),
        "",
        "</details>",
        "",
        "## Resultado por campo",
    ]
    for campo, titulo in CAMPOS_RELATORIO:
        partes += ["", f"### {titulo}", "", tabela_md(distribuicao(casas, campo))]

    partes += [
        "",
        "## Campos a confirmar por imóvel",
        "",
        tabela_md(distribuicao(casas, "qtd_campos_a_confirmar").sort_values("valor")),
        "",
        "## Valores de referência (base de desenvolvimento)",
        "",
        "| Medida | Mediana | P90 |",
        "|---|---|---|",
        *[
            f"| {rotulo} | {br(dev[c].median())} | {br(dev[c].quantile(0.9))} |"
            for c, rotulo in [
                ("area_m2", "Área (m²)"),
                ("conteudo_min", "Conteúdo mínimo (R$)"),
                ("conteudo_max", "Conteúdo máximo (R$)"),
                ("eletronicos_eletro_max", "Eletrônicos + eletrodomésticos, máx (R$)"),
            ]
        ],
        "",
        "## Limitações",
        "",
        "- Tipo, vínculo e uso são **sugestões** a partir de sinais indiretos; não substituem a declaração do cliente.",
        "- \"Proprietário quitado\" é inferido pela **ausência** de sinais e pode incluir imóvel cedido ou de familiar.",
        "- Não é possível distinguir sobrado de casa térrea, nem identificar imóvel rural, tombado ou uso MEI com os dados recebidos.",
        "- A estimativa de área só vale para os 10 municípios da base; outra cidade exige recalibrar o modelo.",
        "- O conteúdo pode estar subestimado (bens não comprados via banco) ou superestimado (compras que não ficaram no imóvel).",
    ]

    caminho = PASTA_DOCS / "01_casa_gemea.md"
    caminho.write_text("\n".join(partes) + "\n", encoding="utf-8")
    return caminho


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # acentos no terminal do Windows
    PASTA_SAIDAS.mkdir(exist_ok=True)
    PASTA_DOCS.mkdir(exist_ok=True)

    tabelas = {nome: montar_tabela_imoveis(ler_base(nome)) for nome in ("desenvolvimento", "teste")}

    # O tipo do imóvel entra no modelo de área, então é inferido antes do treino.
    modelo = area.treinar(inferir_tipo(tabelas["desenvolvimento"]))

    casas = {}
    for nome, tabela in tabelas.items():
        casas[nome] = construir_casa_gemea(tabela, modelo)
        destino = PASTA_SAIDAS / f"casa_gemea_{nome}.csv"
        casas[nome][COLUNAS_CASA_GEMEA].to_csv(destino, index=False, encoding=ENCODING)
        print(f"✔ {destino.relative_to(destino.parents[1])}: {len(casas[nome])} imóveis")

    relatorio = escrever_relatorio(casas, modelo)
    print(f"✔ {relatorio.relative_to(relatorio.parents[1])}")
    print("\nModelo de área:", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in modelo.metricas.items()})


if __name__ == "__main__":
    main()
