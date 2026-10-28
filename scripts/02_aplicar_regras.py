"""Etapa 02 — Aplica as regras do seguro sobre a Casa Gêmea e gera o relatório da etapa.

Uso (na raiz do projeto):
    python scripts/02_aplicar_regras.py

Saídas:
    saidas/recomendacao_{desenvolvimento,teste}.csv   uma linha por imóvel
    saidas/coberturas_{desenvolvimento,teste}.csv     uma linha por cobertura
    saidas/parametros_calibrados.csv                  IPTU e aluguel por m² por cidade
    saidas/validacao_faixas.csv                       faixas com dados escondidos × valor real
    docs/02_regras_seguro.md
"""

import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from casa_gemea import perguntas, regras, validacao  # noqa: E402
from casa_gemea.config import ENCODING, PASTA_DOCS, PASTA_SAIDAS  # noqa: E402
from casa_gemea.pipeline import executar  # noqa: E402


def br(valor: float, casas: int = 0) -> str:
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def tabela_md(df: pd.DataFrame) -> str:
    celula = lambda v: br(v, 1) if isinstance(v, float) else str(v)
    linhas = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    linhas += ["| " + " | ".join(celula(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(linhas)


def percentual(serie: pd.Series) -> pd.DataFrame:
    n = serie.value_counts()
    return pd.DataFrame({"valor": n.index, "imóveis": n.values, "%": (100 * n.values / n.sum()).round(1)})


# ------------------------------------------------------------------- estabilidade
def estabilidade_plano(casa: pd.DataFrame, base: pd.Series) -> pd.DataFrame:
    """Quantos planos mudam se os limiares de bens variarem ±20%."""
    casa = casa.copy()
    casa["fracao_conteudo_do_cliente"] = casa.apply(lambda r: regras.interesse_seguravel(r)[2], axis=1)
    originais = (regras.CONTEUDO_RELEVANTE, regras.CONTEUDO_MODERADO, regras.ELETRO_RELEVANTE)
    linhas = []
    for fator in (0.8, 1.2):
        regras.CONTEUDO_RELEVANTE, regras.CONTEUDO_MODERADO, regras.ELETRO_RELEVANTE = (v * fator for v in originais)
        novo = casa.apply(lambda r: regras.pontuar_plano(r)["plano_recomendado"], axis=1)
        linhas.append({
            "cenário": f"limiares de bens {fator - 1:+.0%}",
            "planos que mudam": int((novo != base.values).sum()),
            "% da base": round(100 * (novo != base.values).mean(), 1),
        })
    regras.CONTEUDO_RELEVANTE, regras.CONTEUDO_MODERADO, regras.ELETRO_RELEVANTE = originais
    return pd.DataFrame(linhas)


# --------------------------------------------------------------------- casos
def escolher_casos(casa: pd.DataFrame, rec: pd.DataFrame) -> pd.DataFrame:
    """Um caso por combinação relevante (plano × vínculo × semáforo), até 10."""
    m = casa.merge(rec, on=["cliente_id", "imovel_id"])
    m = m.sort_values(["plano_recomendado", "vinculo", "semaforo", "imovel_id"])
    escolhidos = m.drop_duplicates(["plano_recomendado", "vinculo"])
    extras = m[(m["elegivel"] != regras.ELEGIVEL) | (m["qtd_inconsistencias"] > 0)].head(3)
    return pd.concat([escolhidos, extras]).drop_duplicates("imovel_id").head(10)


LEGIVEL = {
    "APARTAMENTO": "apartamento", "CASA": "casa", "CASA_EM_CONDOMINIO": "casa em condomínio",
    "INQUILINO": "inquilino", "PROPRIETARIO_FINANCIADO": "proprietário com financiamento",
    "PROPRIETARIO_LOCADOR": "proprietário que aluga a terceiros", "PROPRIETARIO_QUITADO": "proprietário quitado",
    "MORADIA_HABITUAL": "moradia habitual", "TEMPORADA_OU_SEGUNDA_RESIDENCIA": "temporada ou segunda residência",
    "ALUGADO_A_TERCEIROS": "alugado a terceiros", "OBSERVADO": "observado", "ESTIMADO": "estimado",
    "A_CONFIRMAR": "a confirmar", "ECONOMICO": "econômico", "NORMAL": "normal", "SUPERIOR": "superior",
}


def card_caso(r: pd.Series, cob: pd.DataFrame) -> list[str]:
    t = lambda v: LEGIVEL.get(v, str(v).lower())
    linhas = [
        f"#### {r['imovel_id']} — {regras.NOME_PLANO.get(r['plano_recomendado'], 'sem plano')} ({r['semaforo'].lower()})",
        "",
        f"- **Casa Gêmea:** {t(r['tipo_imovel'])} em {r['municipio_real']}/{r['uf_real']}, "
        f"{t(r['vinculo'])}, {t(r['uso_imovel'])}; área {int(r['area_m2'])} m² ({t(r['area_m2_selo'])}); "
        f"padrão {t(r['padrao_construtivo'])} ({t(r['padrao_construtivo_selo'])}).",
        f"- **Elegibilidade:** {r['elegivel']}" + (f" — {r['motivo_inelegibilidade']}" if r["motivo_inelegibilidade"] else ""),
        f"- **Por que este plano:** {r['motivos_plano'] or 'poucos sinais de necessidade além da proteção básica'}.",
        f"- **Por que não o de baixo:** {r['por_que_nao_plano_abaixo']}",
        f"- **Por que não o de cima:** {r['por_que_nao_plano_acima']}",
        f"- **Confiança geral:** {r['confianca_geral']} · **canal:** {r['canal_sugerido']}"
        + (f" · **conflitos:** {r['inconsistencias']}" if r["inconsistencias"] else ""),
        "",
    ]
    c = cob[cob["imovel_id"] == r["imovel_id"]][["cobertura", "faixa_valor_min", "faixa_valor_max", "confianca_estimativa"]]
    if len(c):
        c = c.assign(faixa_valor_min=c["faixa_valor_min"].map(br), faixa_valor_max=c["faixa_valor_max"].map(br))
        c.columns = ["Cobertura", "Mín (R$)", "Máx (R$)", "Confiança"]
        linhas += [tabela_md(c), ""]
    return linhas


# ------------------------------------------------------------------- relatório
def escrever_relatorio(res, tempo: float, val: pd.DataFrame) -> Path:
    casa_t, rec_t, cob_t = res.casas["teste"], res.recomendacoes["teste"], res.coberturas["teste"]
    rec_d = res.recomendacoes["desenvolvimento"]
    m_t = casa_t.merge(rec_t, on=["cliente_id", "imovel_id"])

    plano_vinculo = pd.crosstab(m_t["vinculo"], m_t["plano_recomendado"]).reset_index()
    faixas = (
        cob_t.assign(razao=cob_t["faixa_valor_max"] / cob_t["faixa_valor_min"])
        .groupby("cobertura")
        .agg(mediana_min=("faixa_valor_min", "median"), mediana_max=("faixa_valor_max", "median"),
             razao_max_min=("razao", "median"), linhas=("cobertura", "size"))
        .reset_index()
    )
    faixas["mediana_min"] = faixas["mediana_min"].map(br)
    faixas["mediana_max"] = faixas["mediana_max"].map(br)
    faixas.columns = ["Cobertura", "Mín mediano (R$)", "Máx mediano (R$)", "Máx/mín mediano", "Linhas"]

    cub = pd.DataFrame(
        [(uf, br(v, 2)) for uf, v in sorted(res.referencias.cub_r8n.items())], columns=["UF", "CUB R8-N (R$/m²)"]
    )
    calib = res.calibracao.tabela()

    p = [
        "# Etapa 02 — Regras do seguro",
        f"_Gerado por `scripts/02_aplicar_regras.py` em {date.today():%d/%m/%Y}. Tempo de execução: {br(tempo, 1)} s para {len(rec_d) + len(rec_t)} imóveis._",
        "",
        f"Na base de teste, **{len(rec_t)} de {len(rec_t)} imóveis** receberam elegibilidade, plano, "
        f"{len(cob_t)} linhas de cobertura com faixa em reais, confiança, justificativa e comparação com os planos vizinhos.",
        "",
        "## Fontes",
        "",
        "| Fonte | Uso |",
        "|---|---|",
        "| Guia dos Times, seção 9 | Elegibilidade, planos e coberturas fixas |",
        "| [Condições Gerais do Seguro Residencial BB Seguros, Processo SUSEP 15414.606453/2020-10, V1.6 (vigência desde 11/08/2026)](https://www.bbseguros.com.br/seguros/seguro-residencial) | Exclusões, bens não cobertos, Primeiro Risco Absoluto, regras de aluguel e despesas emergenciais (citadas como \"CG\") |",
        "| CUB R8-N por UF (Sinduscons, ago–set/2026) | Custo de reconstrução por m² (`dados_externos/cub_r8n_por_uf.csv`) |",
        "| Tabela CUB Sinduscon-MG (abr/2025) | Fatores de tipo e padrão (`dados_externos/fatores_cub_padrao.csv`) |",
        "| [Monitor Mercantil, 21/07/2026](https://monitormercantil.com.br/?p=332625) | Distribuição de sinistros da carteira residencial BB Seguros |",
        "",
        "Detalhes de cada fonte em `docs/fontes_externas.md`.",
        "",
        "## 1. Elegibilidade",
        "",
        "Aplicada antes de recomendar (guia, seção 2).",
        "",
        "| Resultado | Quando | Base |",
        "|---|---|---|",
        "| INELEGIVEL | Situação cadastral diferente de REGULAR; parede de material combustível | Guia 9.1 |",
        "| ELEGIVEL_CONDICIONADO | Possível obra relevante (material de construção ≥ R$ 30 mil, ou ≥ R$ 10 mil + vidraçaria); tipo não identificado | Guia 9.1; CG 7.1 w/x excluem imóveis em reforma ou construção |",
        "| ELEGIVEL | Demais casos, sujeitos à declaração do cliente (área urbana, alvenaria, sem obra estrutural, não tombado) | CG 11, alínea a, e 12.2: declaração inexata faz perder o direito |",
        "",
        tabela_md(percentual(rec_t["elegivel"])),
        "",
        "## 2. Interesse segurável (quanto do imóvel é do cliente)",
        "",
        "| Situação | Prédio | Conteúdo | Base |",
        "|---|---|---|---|",
        "| Inquilino | 3% a 10% (benfeitorias) | 100% | CG 10: beneficiário é o proprietário |",
        "| Apartamento (proprietário) | 10% a 30% (partes privativas) | 100% | CG 5.3 e 15.2.1: estrutura no seguro do condomínio |",
        "| Casa financiada | 50% a 100% | 100% | CG 15.2.1: com seguro habitacional, o residencial atua primeiro no conteúdo e complementa a estrutura |",
        "| Casa em condomínio | 80% a 100% | 100% | Estrutura própria; áreas comuns no seguro do condomínio |",
        "| Casa própria | 100% | 100% | — |",
        "| Locador | conforme o tipo | até 20% | CG 6.1 r: bens de terceiros não são cobertos |",
        "",
        "## 3. Escolha do plano",
        "",
        "Pontuação por sinais; nenhum sinal decide sozinho. Idade e renda não entram.",
        "",
        "| Sinal | Pontos | Puxa para |",
        "|---|---|---|",
        f"| Bens do cliente ≥ R$ {br(regras.CONTEUDO_RELEVANTE)} (≥ R$ {br(regras.CONTEUDO_MODERADO)}) | 2 (1) | Prático |",
        f"| Eletrônicos e eletrodomésticos ≥ R$ {br(regras.ELETRO_RELEVANTE)} | 1 | Prático |",
        "| Gasto com vidraçaria em 24 meses | 1 | Prático |",
        "| Casa (mais acessos expostos) | 1 | Prático |",
        "| Paga aluguel (inquilino) | 2 | Total |",
        "| Recebe aluguel (locador) | 2 | Total |",
        "| Pet | 1 | Total |",
        "| Dependentes | 1 | Total |",
        "",
        "**Decisão:** Total se pontos do Total ≥ 3, ou ≥ 2 com pelo menos 1 ponto do Prático; senão Prático se pontos do Prático ≥ 2; senão Essencial.",
        "",
        "### Resultado na base de teste",
        "",
        tabela_md(percentual(rec_t["plano_recomendado"])),
        "",
        tabela_md(plano_vinculo),
        "",
        "Inquilinos e locadores vão ao Total porque a cobertura de aluguel protege diretamente o que eles pagam ou recebem (CG, Perda de Aluguel 1.1).",
        "",
        "### Estabilidade",
        "",
        tabela_md(estabilidade_plano(casa_t, rec_t["plano_recomendado"])),
        "",
        "## 4. Faixas de cada cobertura",
        "",
        "O seguro é a **Primeiro Risco Absoluto** (CG 15.1): paga até o LMI de cada cobertura, sem rateio. A faixa sugerida é o LMI que cobre a perda plausível do evento.",
        "",
        "| Cobertura | Fórmula | Origem |",
        "|---|---|---|",
        "| Incêndio, raio, explosão e fumaça | prédio + conteúdo | Perda total possível |",
        f"| Danos por água | {regras.AGUA_PREDIO:.0%} do prédio + {regras.AGUA_CONTEUDO:.0%} do conteúdo | Premissa |",
        f"| Vendaval e granizo | casa {regras.VENDAVAL_PREDIO_CASA:.0%} / apto {regras.VENDAVAL_PREDIO_APTO:.0%} do prédio + {regras.VENDAVAL_CONTEUDO:.0%} do conteúdo | Premissa |",
        f"| Impacto de veículos | casa {regras.IMPACTO_CASA:.0%} / apto {regras.IMPACTO_APTO:.0%} do prédio | Premissa |",
        f"| Queda de aeronave | {regras.AERONAVE:.0%} de prédio + conteúdo | Premissa |",
        f"| Danos elétricos | {regras.ELETRICOS:.0%} de eletrônicos e eletrodomésticos | Premissa |",
        f"| Roubo e furto mediante arrombamento | {regras.ROUBO:.0%} do conteúdo | Premissa |",
        f"| Quebra de vidros | R$ {regras.VIDROS_M2_MIN} a R$ {regras.VIDROS_M2_MAX}/m² de área; máx ≥ 1,5× gasto com vidraçaria | Premissa |",
        "| Responsabilidade civil familiar | R$ 20–50 mil, mais R$ 10–30 mil com pet e R$ 5–10 mil por dependente (até 3) | Referência da equipe |",
        "| Perda ou pagamento de aluguel | 3 a 6 meses do aluguel pago/recebido; proprietário morador: área × aluguel por m² da cidade | CG: até 6 meses, aluguel ≤ LMI/6 |",
        "| Despesas emergenciais | LMI em que 3% ao dia pagam R$ 150–300 por pessoa | CG: 10% nas 48h + 3%/dia |",
        "",
        "**Prédio** = área × CUB R8-N da UF × fator de tipo e padrão × interesse segurável. Casa usa o projeto R-1 (1,21× o R8-N); padrão desconhecido vai do meio econômico-normal ao meio normal-superior.",
        "",
        "**Largura da faixa.** As incertezas (área, padrão, interesse) são combinadas pela raiz da soma dos quadrados em escala log. Multiplicar todos os extremos suporia que tudo dá errado ao mesmo tempo e gerava faixas de até 3×.",
        "",
        tabela_md(faixas),
        "",
        "<details><summary>CUB R8-N usado por UF</summary>",
        "",
        tabela_md(cub),
        "",
        "Goiás usa o valor do DF: o Sinduscon-GO publica como principal a categoria R16-A.",
        "",
        "</details>",
        "",
        "<details><summary>Parâmetros calibrados na base de desenvolvimento</summary>",
        "",
        tabela_md(calib),
        "",
        "IPTU por m² vem de imóveis com área real; aluguel por m² vem de inquilinos com área real.",
        "",
        "</details>",
        "",
        "## 5. Confiança e canal",
        "",
        "- **Confiança de cada cobertura:** média da confiança dos dados que ela usa (alta = 0, média = 1, baixa = 2). Até 0,5 é alta, até 1,2 é média, acima é baixa.",
        "- **Confiança geral:** mede a chance de o plano mudar depois das perguntas (ver seção 6). Alta: nenhuma resposta plausível muda o plano. Média: um campo pode mudar o plano. Baixa: dois ou mais campos podem mudar o plano, ou a elegibilidade depende de confirmação.",
        "- **Semáforo:** vermelho se condicionado, vínculo a confirmar ou obra a confirmar (vai ao gerente); verde com confiança alta; amarelo nos demais.",
        "- **Canal:** verde + usuário de app = One Click Buy. Dados de app só escolhem o canal, nunca o plano.",
        "",
        tabela_md(percentual(rec_t["semaforo"])),
        "",
        tabela_md(percentual(rec_t["canal_sugerido"])),
        "",
        "## 6. Perguntas que mudam o resultado",
        "",
        "Para cada campo incerto, o motor simula as respostas plausíveis e refaz a recomendação (`src/casa_gemea/perguntas.py`).",
        "",
        "| Campo | Respostas simuladas | Efeito medido |",
        "|---|---|---|",
        "| Obra | — | define a elegibilidade (sempre perguntada se houver sinal) |",
        "| Vínculo | locador → proprietário sem renda do imóvel | plano |",
        "| Tipo | apartamento ↔ casa (quando a confiança não é alta) | plano |",
        "| Ocupação | segunda residência desocupada por longos períodos (sem cobertura de roubo) | plano |",
        "| Bens | valor no mínimo e no máximo da faixa | plano e faixa |",
        "| Área | área confirmada no valor estimado | faixa |",
        "| Padrão | padrão confirmado | faixa |",
        "",
        f"**Regra de parada:** pergunta-se só o que muda o plano, define a elegibilidade ou estreita a faixa de incêndio em pelo menos {perguntas.LIMIAR_ESTREITAMENTO:.0%}, enquanto a faixa tiver máximo mais de {perguntas.FAIXA_ACEITAVEL - 1:.0%} acima do mínimo. Ordem: elegibilidade → plano → faixa. No fim, uma **declaração única** (área urbana, alvenaria, sem obra estrutural, não tombado) substitui várias perguntas de elegibilidade.",
        "",
        "Perguntas por imóvel (base de teste, sem contar a declaração):",
        "",
        tabela_md(percentual(rec_t["qtd_perguntas"])),
        "",
        "Campos que podem mudar o plano (base de desenvolvimento, imóveis):",
        "",
        tabela_md(percentual(rec_d["campos_que_mudam_plano"].replace("", pd.NA).dropna().str.split("|").explode())),
        "",
        "## 7. Validação das faixas escondendo dados reais",
        "",
        f"Nos {val['imovel_id'].nunique()} imóveis da base de desenvolvimento com área cadastrada, o motor foi rodado escondendo a área e o padrão "
        "construtivo, com o modelo de área retreinado em validação cruzada (5 dobras: nenhum imóvel é avaliado por um modelo que o viu). "
        "Valor real = centro da faixa calculada com os dados cadastrados (`src/casa_gemea/validacao.py`).",
        "",
        tabela_md(validacao.resumo(val).assign(
            faixa_contem=lambda d: (100 * d["faixa_contem"]).round(1),
            erro_mediano_centro=lambda d: (100 * d["erro_mediano_centro"]).round(1),
        ).rename(columns={"cobertura": "Cobertura", "imoveis": "Imóveis", "faixa_contem": "Faixa contém o real (%)",
                          "erro_mediano_centro": "Erro mediano do centro (%)"})),
        "",
        f"No total, a faixa contém o valor real em **{br(100 * val['contem'].mean(), 1)}%** dos casos. As faixas de prédio são conservadoras "
        "porque também carregam a incerteza do interesse segurável (ex.: partes privativas de apartamento de 10% a 30%), que não é testada aqui. "
        "Quebra de vidros depende só da área e acompanha o intervalo de 80% do modelo de área. "
        "**Atenção:** aqui o \"valor real\" é o centro da faixa calculada com os dados cadastrados (inclusive o padrão estimado pelo IPTU), então este número é otimista. "
        "Contra o custo de reconstrução verdadeiro (área real × CUB × fator do padrão real), a cobertura medida em `docs/12_avaliacao_modelo.md` (E3) é de cerca de 89%.",
        "",
        "## 8. Testado e descartado",
        "",
        "| Ideia | Resultado na base de desenvolvimento | Decisão |",
        "|---|---|---|",
        "| Padrão construtivo pelo condomínio por m² (apartamentos) | Acerto de 48% a 54% contra 58% de chutar NORMAL; aponta SUPERIOR com 44% de acerto (frequência real 23%) | Não entra: pior que a referência |",
        "| Locador mais preciso (aluguel recebido × aluguel por m² da cidade; regularidade dos créditos) | Distribuições iguais entre locadores com e sem conflito de endereço (razão mediana 1,44 × 1,59; mesma regularidade) | Não entra: o sinal não separa os grupos; o vínculo vira pergunta |",
        "| Ajuste de RC familiar para clientes com 2 imóveis | CG, RC Familiar 1.1: a cobertura é ligada ao imóvel segurado | Sem mudança: não há duplicidade |",
        "| Confiança geral por contagem de campos a confirmar | Marcava como média campos que não mudam nada (ex.: área de quem já é Total) | Substituída pela análise de impacto |",
        "",
        "## 9. Casos contrastantes (base de teste)",
        "",
    ]
    for _, r in escolher_casos(casa_t, rec_t).iterrows():
        p += card_caso(r, cob_t)

    p += [
        "## Limitações",
        "",
        "- Os percentuais de perda por evento (danos por água, vendaval, impacto, aeronave, elétricos, roubo) e as faixas de RC familiar são premissas da equipe, sem dado de sinistro por imóvel.",
        "- O CUB vem de agregador secundário (myside.com.br) que cita os Sinduscons; meses de referência diferem entre UFs (ago e set/2026). Goiás usa o DF como proxy.",
        "- Os fatores de padrão vêm da tabela de Minas Gerais (abr/2025) e foram aplicados a todas as UFs.",
        "- O CUB não inclui fundações, elevadores e áreas externas; a reconstrução real pode ser maior.",
        "- A base não informa se o financiamento tem seguro habitacional; por isso a faixa do prédio financiado começa em 50%.",
        "- Os nomes Essencial, Prático e Total não aparecem nas Condições Gerais; a composição de cada plano segue o catálogo do datathon.",
    ]
    caminho = PASTA_DOCS / "02_regras_seguro.md"
    caminho.write_text("\n".join(p) + "\n", encoding="utf-8")
    return caminho


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    inicio = time.perf_counter()
    res = executar()
    tempo = time.perf_counter() - inicio

    for nome in res.recomendacoes:
        for tipo, df in (("recomendacao", res.recomendacoes[nome]), ("coberturas", res.coberturas[nome])):
            destino = PASTA_SAIDAS / f"{tipo}_{nome}.csv"
            df.to_csv(destino, index=False, encoding=ENCODING)
            print(f"✔ saidas/{destino.name}: {len(df)} linhas")
    res.calibracao.tabela().to_csv(PASTA_SAIDAS / "parametros_calibrados.csv", index=False, encoding=ENCODING)
    print("✔ saidas/parametros_calibrados.csv")

    val = validacao.validar()
    val.to_csv(PASTA_SAIDAS / "validacao_faixas.csv", index=False, encoding=ENCODING)
    print(f"✔ saidas/validacao_faixas.csv: faixa contém o valor real em {val['contem'].mean():.1%}")

    relatorio = escrever_relatorio(res, tempo, val)
    print(f"✔ docs/{relatorio.name}")


if __name__ == "__main__":
    main()
