"""Etapa 11 — Consistência entre casos semelhantes (métrica sugerida no guia, seção 8).

Agrupa os imóveis pelos sinais que mais pesam na escolha do plano e mede se imóveis do
mesmo grupo recebem o mesmo plano. Quando não recebem, aponta qual sinal fora do grupo
explica a diferença (eletrônicos, vidraçaria ou desocupação).

Uso (na raiz do projeto):
    python scripts/11_consistencia.py

Saídas:
    saidas/consistencia_grupos.csv     um grupo por linha, com os planos e o motivo da diferença
    docs/15_consistencia.md            resumo por base
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from casa_gemea import regras  # noqa: E402
from casa_gemea.config import PASTA_DOCS, PASTA_SAIDAS  # noqa: E402
from casa_gemea.pipeline import executar  # noqa: E402

GRUPO = ["tipo_imovel", "vinculo", "nivel_bens", "tem_pet", "tem_dependentes"]
# Sinais da pontuação que ficam fora do grupo e podem separar imóveis parecidos.
SINAIS_FORA = {
    "eletronicos_relevantes": "eletrônicos acima de R$ 15 mil",
    "sinal_vidros": "gasto com vidraçaria",
    "imovel_desocupado": "imóvel desocupado (sem roubo)",
}


def pct(parte: float, total: float) -> str:
    return f"{100 * parte / total:.1f}%".replace(".", ",")


def nivel_bens(valor: float) -> str:
    if valor >= regras.CONTEUDO_RELEVANTE:
        return "ALTO"
    return "MODERADO" if valor >= regras.CONTEUDO_MODERADO else "BAIXO"


def preparar(casa: pd.DataFrame, rec: pd.DataFrame) -> pd.DataFrame:
    df = casa.merge(rec[["imovel_id", "plano_recomendado"]], on="imovel_id")
    df = df[df["plano_recomendado"] != ""].copy()
    fracao = df.apply(lambda r: regras.interesse_seguravel(r)[2], axis=1)
    df["nivel_bens"] = (df["conteudo_estimado"] * fracao).map(nivel_bens)
    df["tem_pet"] = df["possui_pet_informado"] == "SIM"
    df["tem_dependentes"] = df["quantidade_dependentes"] > 0
    df["eletronicos_relevantes"] = df["eletronicos_eletro_max"] * fracao >= regras.ELETRO_RELEVANTE
    df["imovel_desocupado"] = df.get("imovel_desocupado", False)
    return df


def grupos(df: pd.DataFrame, base: str) -> pd.DataFrame:
    linhas = []
    for chave, g in df.groupby(GRUPO):
        if len(g) < 2:
            continue
        planos = g["plano_recomendado"].value_counts()
        motivos = [texto for sinal, texto in SINAIS_FORA.items() if g[sinal].nunique() > 1]
        linhas.append({
            "base": base, **dict(zip(GRUPO, chave)), "imoveis": len(g),
            "consistente": len(planos) == 1,
            "planos": "; ".join(f"{p} {n}" for p, n in planos.items()),
            "sinais_que_variam": "; ".join(motivos),
        })
    return pd.DataFrame(linhas)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    res = executar()
    tabela = pd.concat([grupos(preparar(res.casas[b], res.recomendacoes[b]), b) for b in ("desenvolvimento", "teste")])
    tabela.to_csv(PASTA_SAIDAS / "consistencia_grupos.csv", index=False, encoding="utf-8-sig")

    p = [
        "# Etapa 11 — Consistência entre casos semelhantes",
        f"_Gerado por `scripts/11_consistencia.py` em {date.today():%d/%m/%Y}._",
        "",
        "Imóveis com o mesmo tipo, vínculo, nível de bens (baixo < R$ 10 mil ≤ moderado < R$ 20 mil ≤ alto), pet e "
        "dependentes formam um grupo. Mede-se em quantos grupos (com 2 ou mais imóveis) todos recebem o mesmo plano.",
        "",
        "| Base | Grupos | Consistentes | Imóveis em grupos consistentes |",
        "|---|---|---|---|",
    ]
    for base, t in tabela.groupby("base", sort=False):
        ok = t[t["consistente"]]
        p.append(f"| {base} | {len(t)} | {len(ok)} ({pct(len(ok), len(t))}) | "
                 f"{ok['imoveis'].sum()} de {t['imoveis'].sum()} ({pct(ok['imoveis'].sum(), t['imoveis'].sum())}) |")
    inconsist = tabela[~tabela["consistente"]]
    sem_motivo = inconsist[inconsist["sinais_que_variam"] == ""]
    p += [
        "",
        f"Dos {len(inconsist)} grupos com planos diferentes, {len(inconsist) - len(sem_motivo)} são explicados por um sinal "
        "da pontuação que fica fora do grupo (eletrônicos, vidraçaria ou desocupação). "
        + (f"{len(sem_motivo)} não têm um desses sinais variando: a diferença vem do limiar de bens dentro do mesmo nível."
           if len(sem_motivo) else "Nenhum grupo fica sem explicação."),
        "",
        "## Grupos inconsistentes da base de teste",
        "",
        "| Tipo | Vínculo | Bens | Pet | Dependentes | Imóveis | Planos | Sinais que variam |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in inconsist[inconsist["base"] == "teste"].itertuples():
        p.append(f"| {r.tipo_imovel} | {r.vinculo} | {r.nivel_bens} | {'sim' if r.tem_pet else 'não'} | "
                 f"{'sim' if r.tem_dependentes else 'não'} | {r.imoveis} | {r.planos} | {r.sinais_que_variam or '-'} |")
    caminho = PASTA_DOCS / "15_consistencia.md"
    caminho.write_text("\n".join(p) + "\n", encoding="utf-8")
    print(f"✔ saidas/consistencia_grupos.csv: {len(tabela)} grupos")
    print(f"✔ {caminho.relative_to(caminho.parents[1])}")
    print("\n".join(p[6:9]))


if __name__ == "__main__":
    main()
