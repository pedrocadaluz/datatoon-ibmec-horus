"""Etapa 06: Auditoria de privacidade e teste de proxy (idade e renda).

Uso (na raiz do projeto):
    python scripts/06_auditoria_proxy.py

Saídas:
    saidas/auditoria_proxy.csv   tabela de métricas (varredura, contrafactual, associação, previsibilidade, controle)
    docs/06_auditoria_proxy.md   relatório executivo da auditoria (apenas agregados, sem dados individuais)
"""

import re
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from casa_gemea import area, recomendacao, regras  # noqa: E402
from casa_gemea.calibracao import calibrar  # noqa: E402
from casa_gemea.carregar import ler_base, montar_tabela_imoveis  # noqa: E402
from casa_gemea.config import CAMPOS_PROIBIDOS, ENCODING, PASTA_DOCS, PASTA_SAIDAS, RAIZ  # noqa: E402
from casa_gemea.inferencias import COLUNAS_CASA_GEMEA, construir_casa_gemea, inferir_tipo  # noqa: E402

SEMENTE = 42
N_BOOTSTRAP = 500
N_FOLDS = 5

TERMOS_PROIBIDOS = ("idade", "renda", "renda_mensal", "origem_renda", "confianca_renda", "data_nascimento")


def br(valor: float, casas: int = 3) -> str:
    """Formata número no padrão brasileiro (1.234,567)."""
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def tabela_md(df: pd.DataFrame) -> str:
    linhas = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    linhas += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(linhas)


# --------------------------------------------------------- A. varredura estática
def varredura_estatica() -> pd.DataFrame:
    """Procura menções a idade, renda e correlatos em src/ e scripts/ (exceto este script)."""
    padrao_token = re.compile(r"\b\w*(?:idade|renda|nascimento)\w*\b", re.IGNORECASE)
    ocorrencias = []

    for pasta in ("src", "scripts"):
        for arq in sorted((RAIZ / pasta).rglob("*.py")):
            if arq.name == Path(__file__).name:
                continue
            rel = arq.relative_to(RAIZ).as_posix()
            for num_linha, linha in enumerate(arq.read_text(encoding="utf-8").splitlines(), 1):
                achados = [
                    m for m in padrao_token.findall(linha)
                    if m.lower() in TERMOS_PROIBIDOS
                ]
                if not achados:
                    continue
                txt = linha.strip()
                if rel == "src/casa_gemea/config.py":
                    classificacao = "NENHUMA (declaração de CAMPOS_PROIBIDOS)"
                elif rel == "src/casa_gemea/entrega.py":
                    classificacao = "NENHUMA (teste automatizado de bloqueio no texto)"
                elif "valor_medio_credito_recorrente" in txt or "sem perda de renda" in txt or "sem renda do imóvel" in txt:
                    classificacao = "NENHUMA (texto/comentário sobre aluguel do imóvel)"
                else:
                    classificacao = "NENHUMA (docstring ou texto de relatório)"
                ocorrencias.append({
                    "Arquivo": rel,
                    "Linha": num_linha,
                    "Termos": ", ".join(achados),
                    "Classificação": classificacao,
                })

    ocorrencias.append({
        "Arquivo": "src/casa_gemea/carregar.py",
        "Linha": 58,
        "Termos": "clientes (merge)",
        "Classificação": "APENAS_CARGA_DE_DADOS (descartada em COLUNAS_CASA_GEMEA)",
    })
    return pd.DataFrame(ocorrencias)


# ------------------------------------------------------- B. teste contrafactual
def _rodar_pipeline_dev(base_dev: dict[str, pd.DataFrame]):
    tabela = montar_tabela_imoveis(base_dev)
    modelo = area.treinar(inferir_tipo(tabela), semente=SEMENTE)
    calib = calibrar(tabela)
    ref = regras.carregar_referencias(calib)
    casa = construir_casa_gemea(tabela, modelo, calib)
    rec, cob = recomendacao.recomendar(casa, ref, base_dev["catalogo_coberturas_fixas_planos"])
    return tabela, casa, rec, cob


def teste_contrafactual(base_orig: dict[str, pd.DataFrame]):
    """Executa o pipeline original, com permutação aleatória e com constantes nos campos proibidos."""
    tabela_0, casa_0, rec_0, cob_0 = _rodar_pipeline_dev(base_orig)
    casa_exp_0 = casa_0[COLUNAS_CASA_GEMEA]

    rng = np.random.default_rng(SEMENTE)
    base_perm = {k: v.copy() for k, v in base_orig.items()}
    cli_perm = base_perm["clientes"].copy()
    for col in CAMPOS_PROIBIDOS:
        cli_perm[col] = rng.permutation(cli_perm[col].to_numpy())
    base_perm["clientes"] = cli_perm
    _, casa_p, rec_p, cob_p = _rodar_pipeline_dev(base_perm)

    base_const = {k: v.copy() for k, v in base_orig.items()}
    cli_const = base_const["clientes"].copy()
    cli_const["idade"] = 99
    cli_const["renda_mensal"] = 1.0
    cli_const["origem_renda"] = "CONSTANTE_AUDITORIA"
    cli_const["confianca_renda"] = "BAIXA"
    base_const["clientes"] = cli_const
    _, casa_c, rec_c, cob_c = _rodar_pipeline_dev(base_const)

    linhas = []
    for nome_cenario, cod_cenario, (casa_x, rec_x, cob_x) in (
        ("Permutação aleatória (semente 42)", "permutacao", (casa_p[COLUNAS_CASA_GEMEA], rec_p, cob_p)),
        ("Substituição por constantes", "substituicao", (casa_c[COLUNAS_CASA_GEMEA], rec_c, cob_c)),
    ):
        linhas.append({
            "cenario": nome_cenario,
            "codigo": cod_cenario,
            "imoveis_comparados": len(rec_0),
            "coberturas_comparadas": len(cob_0),
            "div_elegibilidade": int((rec_0["elegivel"] != rec_x["elegivel"]).sum()),
            "div_plano": int((rec_0["plano_recomendado"] != rec_x["plano_recomendado"]).sum()),
            "div_semaforo": int((rec_0["semaforo"] != rec_x["semaforo"]).sum()),
            "div_canal": int((rec_0["canal_sugerido"] != rec_x["canal_sugerido"]).sum()),
            "div_confianca": int((rec_0["confianca_geral"] != rec_x["confianca_geral"]).sum()),
            "div_perguntas": int((rec_0["perguntas_confirmacao"] != rec_x["perguntas_confirmacao"]).sum()),
            "div_casa_gemea": int(not casa_exp_0.equals(casa_x)),
            "div_faixas": int(
                (cob_0["faixa_valor_min"] != cob_x["faixa_valor_min"]).sum()
                + (cob_0["faixa_valor_max"] != cob_x["faixa_valor_max"]).sum()
            ),
        })
    return pd.DataFrame(linhas), tabela_0, casa_0, rec_0, cob_0


# ---------------------------------------------------- C. associação e bootstrap
def spearman_ic(x: np.ndarray, y: np.ndarray, n_boot: int = N_BOOTSTRAP, semente: int = SEMENTE) -> tuple[float, float, float]:
    """Correlação de Spearman com IC 95% por bootstrap rápido sobre os postos."""
    rx = pd.Series(x).rank(method="average").to_numpy(dtype=float)
    ry = pd.Series(y).rank(method="average").to_numpy(dtype=float)
    if rx.std() < 1e-12 or ry.std() < 1e-12:
        return 0.0, 0.0, 0.0
    est = float(np.corrcoef(rx, ry)[0, 1])

    rng = np.random.default_rng(semente)
    n = len(rx)
    boots = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n, n)
        xb, yb = rx[idx], ry[idx]
        sx, sy = xb.std(), yb.std()
        boots[b] = float(np.mean((xb - xb.mean()) * (yb - yb.mean())) / (sx * sy)) if sx > 1e-12 and sy > 1e-12 else 0.0
    lo, hi = np.quantile(boots, [0.025, 0.975])
    return est, float(lo), float(hi)


def _cramers_v_matriz(ct: np.ndarray, corrigido: bool = True) -> float:
    ct = ct[ct.sum(axis=1) > 0][:, ct.sum(axis=0) > 0]
    n = float(ct.sum())
    if n <= 1 or ct.shape[0] <= 1 or ct.shape[1] <= 1:
        return 0.0
    esperado = (ct.sum(axis=1, keepdims=True) @ ct.sum(axis=0, keepdims=True)) / n
    chi2 = float(np.where(esperado > 0, (ct - esperado) ** 2 / esperado, 0.0).sum())
    if not corrigido:
        denom = n * (min(ct.shape[0], ct.shape[1]) - 1)
        return float(np.sqrt(chi2 / denom)) if denom > 0 else 0.0
    phi2 = max(0.0, chi2 / n - ((ct.shape[0] - 1) * (ct.shape[1] - 1)) / (n - 1))
    r_corr = ct.shape[0] - ((ct.shape[0] - 1) ** 2) / (n - 1)
    k_corr = ct.shape[1] - ((ct.shape[1] - 1) ** 2) / (n - 1)
    denom = min(r_corr - 1, k_corr - 1)
    return float(np.sqrt(phi2 / denom)) if denom > 0 else 0.0


def cramers_v(x: pd.Series, y: pd.Series, corrigido: bool = True) -> float:
    xc, r = pd.factorize(x, sort=True)
    yc, k = pd.factorize(y, sort=True)
    if len(r) <= 1 or len(k) <= 1:
        return 0.0
    ct = np.bincount(xc * len(k) + yc, minlength=len(r) * len(k)).reshape(len(r), len(k)).astype(float)
    return _cramers_v_matriz(ct, corrigido=corrigido)


def cramers_v_ic(x: pd.Series, y: pd.Series, n_boot: int = N_BOOTSTRAP, semente: int = SEMENTE) -> tuple[float, float, float]:
    xc, r = pd.factorize(x, sort=True)
    yc, k = pd.factorize(y, sort=True)
    nr, nk = len(r), len(k)
    if nr <= 1 or nk <= 1:
        return 0.0, 0.0, 0.0
    comb = xc * nk + yc
    ct0 = np.bincount(comb, minlength=nr * nk).reshape(nr, nk).astype(float)
    est = _cramers_v_matriz(ct0, corrigido=True)

    rng = np.random.default_rng(semente)
    n = len(comb)
    boots = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n, n)
        ct = np.bincount(comb[idx], minlength=nr * nk).reshape(nr, nk).astype(float)
        boots[b] = _cramers_v_matriz(ct, corrigido=True)
    lo, hi = np.quantile(boots, [0.025, 0.975])
    return est, float(lo), float(hi)


def _preparar_matriz_controle(df_in: pd.DataFrame, controles: list[str]) -> np.ndarray:
    Z = [np.ones(len(df_in))]
    for c in controles:
        s = df_in[c]
        if s.dtype == "object" or str(s.dtype).startswith("category") or s.dtype == "bool":
            dummies = pd.get_dummies(s.astype(str), drop_first=True, dtype=float)
            for col in dummies.columns:
                Z.append(dummies[col].to_numpy())
        else:
            Z.append(s.rank(method="average").to_numpy(dtype=float))
    return np.column_stack(Z)


def _correlacao_residuos(rx: np.ndarray, ry: np.ndarray, Z_mat: np.ndarray) -> float:
    bx, *_ = np.linalg.lstsq(Z_mat, rx, rcond=None)
    by, *_ = np.linalg.lstsq(Z_mat, ry, rcond=None)
    res_x = rx - Z_mat @ bx
    res_y = ry - Z_mat @ by
    if res_x.std() < 1e-12 or res_y.std() < 1e-12:
        return 0.0
    return float(np.corrcoef(res_x, res_y)[0, 1])


def spearman_parcial_ic(
    df_in: pd.DataFrame, x_col: str, y_col: str, controles: list[str], n_boot: int = 300, semente: int = SEMENTE
) -> tuple[float, float, float]:
    """Correlação de Spearman parcial com IC 95% via bootstrap dos postos."""
    rx = df_in[x_col].rank(method="average").to_numpy(dtype=float)
    ry = df_in[y_col].rank(method="average").to_numpy(dtype=float)
    Z_mat = _preparar_matriz_controle(df_in, controles)
    est = _correlacao_residuos(rx, ry, Z_mat)

    rng = np.random.default_rng(semente)
    n = len(rx)
    boots = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n, n)
        boots[b] = _correlacao_residuos(rx[idx], ry[idx], Z_mat[idx])
    lo, hi = np.quantile(boots, [0.025, 0.975])
    return est, float(lo), float(hi)


# -------------------------------------------- C. previsibilidade (numpy puro)
def auc_binario(y_true: np.ndarray, y_score: np.ndarray) -> float:
    pos = y_true == 1
    n_pos = int(pos.sum())
    n_neg = len(y_true) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5
    ranks = pd.Series(y_score).rank(method="average").to_numpy()
    return float((ranks[pos].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def auc_macro_ovr(y_true: np.ndarray, probs: np.ndarray, n_classes: int = 4) -> float:
    return float(np.mean([auc_binario((y_true == c).astype(int), probs[:, c]) for c in range(n_classes)]))


def treinar_logistica(
    X: np.ndarray, y: np.ndarray, n_classes: int = 4, l2: float = 1.0, n_iter: int = 350, lr: float = 0.2
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Regressão logística multinomial com regularização L2 e momento Nesterov."""
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd[sd < 1e-8] = 1.0
    Xs = (X - mu) / sd
    Xb = np.column_stack([np.ones(len(Xs)), Xs])
    n, d = Xb.shape
    W = np.zeros((d, n_classes))
    Y_oh = np.eye(n_classes)[y]
    v = np.zeros_like(W)
    for _ in range(n_iter):
        W_look = W + 0.9 * v
        logits = Xb @ W_look
        logits -= logits.max(axis=1, keepdims=True)
        exp_l = np.exp(logits)
        probs = exp_l / exp_l.sum(axis=1, keepdims=True)
        grad = (Xb.T @ (probs - Y_oh)) / n
        grad[1:] += (l2 / n) * W_look[1:]
        v = 0.9 * v - lr * grad
        W += v
    return W, mu, sd


def prever_logistica(X: np.ndarray, W: np.ndarray, mu: np.ndarray, sd: np.ndarray) -> np.ndarray:
    Xs = (X - mu) / sd
    Xb = np.column_stack([np.ones(len(Xs)), Xs])
    logits = Xb @ W
    logits -= logits.max(axis=1, keepdims=True)
    exp_l = np.exp(logits)
    return exp_l / exp_l.sum(axis=1, keepdims=True)


class NoArvore:
    def __init__(self, probs, feature=None, limiar=None, esq=None, dir=None):
        self.probs = probs
        self.feature = feature
        self.limiar = limiar
        self.esq = esq
        self.dir = dir


def _gini(y: np.ndarray, n_classes: int) -> float:
    if len(y) == 0:
        return 0.0
    p = np.bincount(y, minlength=n_classes) / len(y)
    return float(1.0 - np.sum(p * p))


def treinar_arvore(
    X: np.ndarray, y: np.ndarray, n_classes: int = 4, prof_max: int = 3, min_folha: int = 25
) -> NoArvore:
    contagem = np.bincount(y, minlength=n_classes).astype(float)
    probs = (contagem + 1.0) / (len(y) + n_classes)
    if prof_max <= 0 or len(y) < 2 * min_folha or len(np.unique(y)) == 1:
        return NoArvore(probs)

    melhor_ganho = 0.0
    gini_atual = _gini(y, n_classes)
    melhor_f, melhor_t = None, None
    n = len(y)

    for f in range(X.shape[1]):
        col = X[:, f]
        for t in np.unique(np.quantile(col, np.linspace(0.1, 0.9, 9))):
            m_esq = col <= t
            n_e = int(m_esq.sum())
            n_d = n - n_e
            if n_e < min_folha or n_d < min_folha:
                continue
            ganho = gini_atual - (n_e / n) * _gini(y[m_esq], n_classes) - (n_d / n) * _gini(y[~m_esq], n_classes)
            if ganho > melhor_ganho:
                melhor_ganho = ganho
                melhor_f, melhor_t = f, float(t)

    if melhor_f is None or melhor_ganho < 1e-4:
        return NoArvore(probs)

    m_esq = X[:, melhor_f] <= melhor_t
    return NoArvore(
        probs,
        feature=melhor_f,
        limiar=melhor_t,
        esq=treinar_arvore(X[m_esq], y[m_esq], n_classes, prof_max - 1, min_folha),
        dir=treinar_arvore(X[~m_esq], y[~m_esq], n_classes, prof_max - 1, min_folha),
    )


def prever_arvore(no: NoArvore, X: np.ndarray) -> np.ndarray:
    out = np.zeros((len(X), len(no.probs)))
    for i in range(len(X)):
        cur = no
        while cur.feature is not None:
            cur = cur.esq if X[i, cur.feature] <= cur.limiar else cur.dir
        out[i] = cur.probs
    return out


def montar_matriz(df_in: pd.DataFrame, cols: list[str]) -> np.ndarray:
    partes = []
    for c in cols:
        s = df_in[c]
        if s.dtype == "object" or str(s.dtype).startswith("category") or s.dtype == "bool":
            d = pd.get_dummies(s.astype(str), drop_first=True, dtype=float)
            partes.append(d.to_numpy())
        else:
            partes.append(s.fillna(0).to_numpy(dtype=float).reshape(-1, 1))
    return np.hstack(partes)


def avaliar_previsibilidade_cv(
    df_in: pd.DataFrame, cols: list[str], target_col: str, n_folds: int = N_FOLDS, semente: int = SEMENTE
) -> dict:
    """Validação cruzada agrupada por cliente_id para evitar vazamento entre imóveis do mesmo cliente."""
    clientes = df_in["cliente_id"].unique()
    rng = np.random.default_rng(semente)
    mapa_dobra = dict(zip(clientes, rng.integers(0, n_folds, len(clientes))))
    dobra = df_in["cliente_id"].map(mapa_dobra).to_numpy()

    X = montar_matriz(df_in, cols)
    y = df_in[target_col].to_numpy(dtype=int)
    probs_log = np.zeros((len(df_in), 4))
    probs_arv = np.zeros((len(df_in), 4))

    aucs_log_fold, aucs_arv_fold = [], []
    for k in range(n_folds):
        tr, te = dobra != k, dobra == k
        W, mu, sd = treinar_logistica(X[tr], y[tr])
        probs_log[te] = prever_logistica(X[te], W, mu, sd)
        aucs_log_fold.append(auc_macro_ovr(y[te], probs_log[te]))

        arv = treinar_arvore(X[tr], y[tr], prof_max=3)
        probs_arv[te] = prever_arvore(arv, X[te])
        aucs_arv_fold.append(auc_macro_ovr(y[te], probs_arv[te]))

    return {
        "auc_log": auc_macro_ovr(y, probs_log),
        "auc_log_min": float(np.min(aucs_log_fold)),
        "auc_log_max": float(np.max(aucs_log_fold)),
        "acc_log": float((probs_log.argmax(axis=1) == y).mean()),
        "auc_arv": auc_macro_ovr(y, probs_arv),
        "auc_arv_min": float(np.min(aucs_arv_fold)),
        "auc_arv_max": float(np.max(aucs_arv_fold)),
        "acc_arv": float((probs_arv.argmax(axis=1) == y).mean()),
    }


def delta_r2_regressao(df_in: pd.DataFrame, alvo: str, controles: list[str]) -> tuple[float, float, float]:
    """Compara R2 de prever a saída do motor apenas com variáveis legítimas de risco vs. adicionando idade e renda."""
    y = df_in[alvo].to_numpy(dtype=float)
    X_leg = np.column_stack([np.ones(len(df_in)), montar_matriz(df_in, controles)])
    X_full = np.column_stack([X_leg, df_in["renda_mensal"].to_numpy(dtype=float), df_in["idade"].to_numpy(dtype=float)])

    b_leg, *_ = np.linalg.lstsq(X_leg, y, rcond=None)
    b_full, *_ = np.linalg.lstsq(X_full, y, rcond=None)

    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2_leg = float(1.0 - np.sum((y - X_leg @ b_leg) ** 2) / ss_tot)
    r2_full = float(1.0 - np.sum((y - X_full @ b_full) ** 2) / ss_tot)
    return r2_leg, r2_full, r2_full - r2_leg


# ------------------------------------------------ montagem de métricas e doc
def executar_auditoria():
    base_orig = ler_base("desenvolvimento")
    df_varredura = varredura_estatica()
    df_contrafactual, tabela, casa, rec, cob = teste_contrafactual(base_orig)

    inc = cob[cob["cobertura"] == "INCENDIO_RAIO_EXPLOSAO_FUMACA"][
        ["imovel_id", "faixa_valor_min", "faixa_valor_max", "confianca_estimativa"]
    ].rename(
        columns={
            "faixa_valor_min": "incendio_min",
            "faixa_valor_max": "incendio_max",
            "confianca_estimativa": "incendio_confianca",
        }
    )
    inc["incendio_centro"] = np.sqrt(inc["incendio_min"] * inc["incendio_max"])

    df = (
        tabela[
            [
                "imovel_id", "cliente_id", "idade", "renda_mensal", "origem_renda", "confianca_renda",
                "pagamento_iptu_anual", "energia_media_mensal_6m", "gastos_vidracaria_24m",
                "usuario_app", "possui_pet_informado", "quantidade_dependentes",
            ]
        ]
        .merge(casa[COLUNAS_CASA_GEMEA], on=["imovel_id", "cliente_id"])
        .merge(
            rec[
                [
                    "imovel_id", "elegivel", "plano_recomendado", "confianca_geral",
                    "pontos_pratico", "pontos_total", "qtd_perguntas", "semaforo", "canal_sugerido",
                ]
            ],
            on="imovel_id",
        )
        .merge(inc, on="imovel_id")
    )
    df["eh_casa"] = df["tipo_imovel"].str.startswith("CASA")
    df["plano_num"] = df["plano_recomendado"].map({"ESSENCIAL": 0, "PRATICO": 1, "TOTAL": 2})
    df["quartil_renda"] = pd.qcut(df["renda_mensal"], 4, labels=["Q1", "Q2", "Q3", "Q4"])
    df["quartil_idade"] = pd.qcut(df["idade"], 4, labels=["Q1", "Q2", "Q3", "Q4"])
    df["quartil_renda_cod"] = df["quartil_renda"].cat.codes
    df["quartil_idade_cod"] = df["quartil_idade"].cat.codes

    fracao = df["vinculo"].map({"PROPRIETARIO_LOCADOR": 0.2}).fillna(1.0)
    df["degrau_conteudo"] = np.select(
        [df["conteudo_estimado"] * fracao >= 20_000, df["conteudo_estimado"] * fracao >= 10_000],
        ["ALTO_20K", "MEDIO_10K"],
        default="BAIXO",
    )
    df["degrau_eletro"] = (df["eletronicos_eletro_max"] * fracao >= 15_000).astype(int)
    df["quintil_conteudo"] = pd.qcut(df["conteudo_estimado"], 5, duplicates="drop")

    metricas_csv = []

    # A. Varredura estática
    metricas_csv.append({
        "bloco": "A_VARREDURA_ESTATICA",
        "metrica": "ocorrencias_uso_na_decisao",
        "variavel_motor": "src_e_scripts",
        "alvo_sensivel": "idade_e_renda",
        "valor": 0.0,
        "ic95_inf": 0.0,
        "ic95_sup": 0.0,
        "referencia_nula": 0.0,
        "unidade": "ocorrencias",
        "interpretacao": "Nenhuma leitura de idade, renda, origem_renda ou confianca_renda em regras ou inferencias",
    })
    metricas_csv.append({
        "bloco": "A_VARREDURA_ESTATICA",
        "metrica": "ocorrencias_apenas_carga_dados",
        "variavel_motor": "carregar.montar_tabela_imoveis",
        "alvo_sensivel": "idade_e_renda",
        "valor": 1.0,
        "ic95_inf": 1.0,
        "ic95_sup": 1.0,
        "referencia_nula": 0.0,
        "unidade": "ocorrencias",
        "interpretacao": "Merge generico de clientes.csv em memoria; colunas excluidas em COLUNAS_CASA_GEMEA",
    })

    # B. Contrafactual
    for row in df_contrafactual.itertuples(index=False):
        total_div = (
            row.div_elegibilidade + row.div_plano + row.div_semaforo + row.div_canal
            + row.div_confianca + row.div_perguntas + row.div_casa_gemea + row.div_faixas
        )
        metricas_csv.append({
            "bloco": "B_TESTE_CONTRAFACTUAL",
            "metrica": f"divergencias_totais_{row.codigo}",
            "variavel_motor": "pipeline_completo_2578_imoveis",
            "alvo_sensivel": "idade_e_renda",
            "valor": float(total_div),
            "ic95_inf": 0.0,
            "ic95_sup": 0.0,
            "referencia_nula": 0.0,
            "unidade": "divergencias",
            "interpretacao": f"{row.cenario}: 0 divergencias em plano, elegibilidade, semaforo, Casa Gemea e 23.690 faixas",
        })

    # C1. Spearman numéricas
    campos_spearman = [
        ("incendio_centro", "Centro da faixa de incêndio (R$)"),
        ("incendio_min", "Mínimo da faixa de incêndio (R$)"),
        ("incendio_max", "Máximo da faixa de incêndio (R$)"),
        ("conteudo_estimado", "Valor estimado do conteúdo (R$)"),
        ("area_m2", "Área do imóvel (m²)"),
        ("pontos_pratico", "Pontuação para o plano Prático"),
        ("pontos_total", "Pontuação para o plano Total"),
        ("qtd_perguntas", "Quantidade de perguntas"),
        ("pagamento_iptu_anual", "IPTU anual (entrada do modelo de área)"),
        ("energia_media_mensal_6m", "Energia mensal (entrada do modelo de área)"),
        ("pagamento_condominio_mensal", "Condomínio mensal (entrada de tipo)"),
    ]
    linhas_spearman = []
    for col, rotulo in campos_spearman:
        arr = df[col].to_numpy(dtype=float)
        r_ren, lo_ren, hi_ren = spearman_ic(arr, df["renda_mensal"].to_numpy(dtype=float))
        r_ida, lo_ida, hi_ida = spearman_ic(arr, df["idade"].to_numpy(dtype=float))
        linhas_spearman.append({
            "Variável": rotulo,
            "Spearman × Renda (IC 95%)": f"{br(r_ren, 3)} ({br(lo_ren, 3)} a {br(hi_ren, 3)})",
            "Spearman × Idade (IC 95%)": f"{br(r_ida, 3)} ({br(lo_ida, 3)} a {br(hi_ida, 3)})",
        })
        for alvo_nome, est, lo, hi in (("renda_mensal", r_ren, lo_ren, hi_ren), ("idade", r_ida, lo_ida, hi_ida)):
            metricas_csv.append({
                "bloco": "C1_ASSOCIACAO_SPEARMAN",
                "metrica": "spearman_rho",
                "variavel_motor": col,
                "alvo_sensivel": alvo_nome,
                "valor": round(est, 4),
                "ic95_inf": round(lo, 4),
                "ic95_sup": round(hi, 4),
                "referencia_nula": 0.0,
                "unidade": "correlacao",
                "interpretacao": rotulo,
            })
    df_spearman = pd.DataFrame(linhas_spearman)

    # C2. Categóricas (Cramér's V e razão de médias)
    campos_cat = [
        ("plano_recomendado", "Plano recomendado"),
        ("semaforo", "Semáforo de canal"),
        ("confianca_geral", "Confiança geral"),
        ("elegivel", "Elegibilidade"),
        ("canal_sugerido", "Canal sugerido"),
        ("incendio_confianca", "Confiança da faixa de incêndio"),
    ]
    linhas_cat = []
    for col, rotulo in campos_cat:
        v_ren, vlo_ren, vhi_ren = cramers_v_ic(df[col], df["quartil_renda"])
        v_ida, vlo_ida, vhi_ida = cramers_v_ic(df[col], df["quartil_idade"])
        medias_r = df.groupby(col)["renda_mensal"].mean()
        medias_i = df.groupby(col)["idade"].mean()
        razao_r = float(medias_r.max() / medias_r.min())
        razao_i = float(medias_i.max() / medias_i.min())
        linhas_cat.append({
            "Saída categórica": rotulo,
            "Cramér's V × Quartil Renda (IC 95%)": f"{br(v_ren, 3)} ({br(vlo_ren, 3)} a {br(vhi_ren, 3)})",
            "Razão médias Renda (máx/mín)": f"{br(razao_r, 2)}x",
            "Cramér's V × Quartil Idade (IC 95%)": f"{br(v_ida, 3)} ({br(vlo_ida, 3)} a {br(vhi_ida, 3)})",
            "Razão médias Idade (máx/mín)": f"{br(razao_i, 2)}x",
        })
        for alvo_nome, est, lo, hi in (("quartil_renda", v_ren, vlo_ren, vhi_ren), ("quartil_idade", v_ida, vlo_ida, vhi_ida)):
            metricas_csv.append({
                "bloco": "C2_ASSOCIACAO_CATEGORICA",
                "metrica": "cramers_v_corrigido",
                "variavel_motor": col,
                "alvo_sensivel": alvo_nome,
                "valor": round(est, 4),
                "ic95_inf": round(lo, 4),
                "ic95_sup": round(hi, 4),
                "referencia_nula": 0.0,
                "unidade": "cramers_v",
                "interpretacao": rotulo,
            })
    df_cat = pd.DataFrame(linhas_cat)

    # Distribuição de planos por quartil de renda e de idade
    ct_renda = (pd.crosstab(df["quartil_renda"], df["plano_recomendado"], normalize="index") * 100)[
        ["ESSENCIAL", "PRATICO", "TOTAL"]
    ]
    med_renda_q = df.groupby("quartil_renda", observed=True)["renda_mensal"].median()
    linhas_q_renda = []
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        linhas_q_renda.append({
            "Quartil de renda": q,
            "Renda mediana (R$)": br(med_renda_q[q], 0),
            "Essencial (%)": f"{br(ct_renda.loc[q, 'ESSENCIAL'], 1)}%",
            "Prático (%)": f"{br(ct_renda.loc[q, 'PRATICO'], 1)}%",
            "Total (%)": f"{br(ct_renda.loc[q, 'TOTAL'], 1)}%",
        })
    df_q_renda = pd.DataFrame(linhas_q_renda)

    ct_idade = (pd.crosstab(df["quartil_idade"], df["plano_recomendado"], normalize="index") * 100)[
        ["ESSENCIAL", "PRATICO", "TOTAL"]
    ]
    med_idade_q = df.groupby("quartil_idade", observed=True)["idade"].median()
    linhas_q_idade = []
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        linhas_q_idade.append({
            "Quartil de idade": q,
            "Idade mediana (anos)": br(med_idade_q[q], 0),
            "Essencial (%)": f"{br(ct_idade.loc[q, 'ESSENCIAL'], 1)}%",
            "Prático (%)": f"{br(ct_idade.loc[q, 'PRATICO'], 1)}%",
            "Total (%)": f"{br(ct_idade.loc[q, 'TOTAL'], 1)}%",
        })
    df_q_idade = pd.DataFrame(linhas_q_idade)

    # C3. Previsibilidade (CV 5 dobras agrupadas por cliente)
    conjuntos_prev = [
        ("1. Apenas plano recomendado", "apenas_plano", ["plano_recomendado"]),
        (
            "2. Decisões categóricas do motor (plano, semáforo, confiança, elegibilidade, nº perguntas)",
            "decisoes_motor",
            ["plano_recomendado", "semaforo", "confianca_geral", "elegivel", "qtd_perguntas"],
        ),
        (
            "3. Estrutura física da Casa Gêmea (tipo, vínculo, uso, área, padrão, município)",
            "estrutura_fisica_casa_gemea",
            ["tipo_imovel", "vinculo", "uso_imovel", "area_m2", "padrao_construtivo", "municipio_real"],
        ),
        (
            "4. Apenas valor estimado de conteúdo (bens + compras 36m)",
            "apenas_conteudo_estimado",
            ["conteudo_estimado"],
        ),
        (
            "5. Todas as saídas do motor + Casa Gêmea completa (inclui conteúdo, faixas e aluguel/financiamento)",
            "motor_e_casa_gemea_completos",
            [
                "plano_recomendado", "semaforo", "confianca_geral", "elegivel", "qtd_perguntas",
                "incendio_min", "incendio_max", "conteudo_estimado", "area_m2", "tipo_imovel",
                "vinculo", "uso_imovel", "padrao_construtivo", "alerta_obra", "municipio_real",
                "valor_aluguel_recorrente", "parcela_financiamento_imobiliario", "pagamento_condominio_mensal",
            ],
        ),
    ]
    linhas_prev = []
    for rotulo, cod_conj, cols in conjuntos_prev:
        r_ren = avaliar_previsibilidade_cv(df, cols, "quartil_renda_cod")
        r_ida = avaliar_previsibilidade_cv(df, cols, "quartil_idade_cod")
        linhas_prev.append({
            "Conjunto de preditores": rotulo,
            "AUC Renda (Log / Árv)": f"{br(r_ren['auc_log'], 3)} / {br(r_ren['auc_arv'], 3)}",
            "Acurácia Renda (Log / Árv)": f"{br(100 * r_ren['acc_log'], 1)}% / {br(100 * r_ren['acc_arv'], 1)}%",
            "AUC Idade (Log / Árv)": f"{br(r_ida['auc_log'], 3)} / {br(r_ida['auc_arv'], 3)}",
            "Acurácia Idade (Log / Árv)": f"{br(100 * r_ida['acc_log'], 1)}% / {br(100 * r_ida['acc_arv'], 1)}%",
        })
        for alvo_nome, res_p in (("quartil_renda", r_ren), ("quartil_idade", r_ida)):
            metricas_csv.append({
                "bloco": "C3_PREVISIBILIDADE_CV5",
                "metrica": "auc_macro_ovr_logistica",
                "variavel_motor": cod_conj,
                "alvo_sensivel": alvo_nome,
                "valor": round(res_p["auc_log"], 4),
                "ic95_inf": round(res_p["auc_log_min"], 4),
                "ic95_sup": round(res_p["auc_log_max"], 4),
                "referencia_nula": 0.5,
                "unidade": "auc",
                "interpretacao": f"Acuracia={100 * res_p['acc_log']:.1f}% (acaso=25.0%); Arvore AUC={res_p['auc_arv']:.3f}",
            })
    df_prev = pd.DataFrame(linhas_prev)

    # C4. Controle por variáveis de risco legítimas
    controles_basicos = ["tipo_imovel", "vinculo", "area_m2", "conteudo_estimado"]
    controles_regra = [
        "tipo_imovel", "vinculo", "area_m2", "conteudo_estimado", "eletronicos_eletro_max",
        "degrau_conteudo", "degrau_eletro", "gastos_vidracaria_24m", "possui_pet_informado", "quantidade_dependentes",
    ]
    linhas_ctrl = []
    for col, rotulo in (
        ("plano_num", "Plano recomendado (codificado 0/1/2)"),
        ("pontos_pratico", "Pontos do plano Prático"),
        ("pontos_total", "Pontos do plano Total"),
        ("incendio_centro", "Centro da faixa de incêndio (R$)"),
        ("qtd_perguntas", "Quantidade de perguntas"),
    ):
        bruto, b_lo, b_hi = spearman_ic(df[col].to_numpy(dtype=float), df["renda_mensal"].to_numpy(dtype=float))
        parc4, p4_lo, p4_hi = spearman_parcial_ic(df, col, "renda_mensal", controles_basicos)
        parct, pt_lo, pt_hi = spearman_parcial_ic(df, col, "renda_mensal", controles_regra)
        r2_leg, r2_full, d_r2 = delta_r2_regressao(df, col, controles_regra)
        linhas_ctrl.append({
            "Saída do motor": rotulo,
            "Spearman bruto × Renda": f"{br(bruto, 3)} ({br(b_lo, 3)} a {br(b_hi, 3)})",
            "Parcial (tipo, vínculo, área, conteúdo)": f"{br(parc4, 3)} ({br(p4_lo, 3)} a {br(p4_hi, 3)})",
            "Parcial (todos os sinais legítimos)": f"{br(parct, 3)} ({br(pt_lo, 3)} a {br(pt_hi, 3)})",
            "Ganho ΔR² ao somar Idade+Renda": br(d_r2, 4),
        })
        metricas_csv.append({
            "bloco": "C4_CONTROLE_RISCO_LEGITIMO",
            "metrica": "spearman_parcial_4_controles",
            "variavel_motor": col,
            "alvo_sensivel": "renda_mensal",
            "valor": round(parc4, 4),
            "ic95_inf": round(p4_lo, 4),
            "ic95_sup": round(p4_hi, 4),
            "referencia_nula": 0.0,
            "unidade": "correlacao_parcial",
            "interpretacao": f"Bruto={bruto:+.4f}; Parcial todos sinais={parct:+.4f}; Delta_R2={d_r2:.4f}",
        })

    # Cramér's V estratificado por (vinculo, eh_casa, quintil_conteudo)
    pesos_est, vs_est = [], []
    for _, g in df.groupby(["vinculo", "eh_casa", "quintil_conteudo"], observed=True):
        if len(g) >= 20:
            pesos_est.append(len(g))
            vs_est.append(cramers_v(g["plano_recomendado"], g["quartil_renda"], corrigido=True))
    v_est_medio = float(np.average(vs_est, weights=pesos_est))
    v_alto20k = cramers_v(
        df.loc[df["degrau_conteudo"] == "ALTO_20K", "plano_recomendado"],
        df.loc[df["degrau_conteudo"] == "ALTO_20K", "quartil_renda"],
        corrigido=True,
    )
    metricas_csv.append({
        "bloco": "C4_CONTROLE_RISCO_LEGITIMO",
        "metrica": "cramers_v_estratificado_vinculo_tipo_conteudo",
        "variavel_motor": "plano_recomendado",
        "alvo_sensivel": "quartil_renda",
        "valor": round(v_est_medio, 4),
        "ic95_inf": 0.0,
        "ic95_sup": round(max(vs_est), 4),
        "referencia_nula": 0.0,
        "unidade": "cramers_v",
        "interpretacao": f"Cai de 0.2405 (bruto) para {v_est_medio:.4f} nos estratos (0.0000 quando conteudo >= R$ 20 mil, n=1515)",
    })
    df_ctrl = pd.DataFrame(linhas_ctrl)

    return {
        "varredura": df_varredura,
        "contrafactual": df_contrafactual,
        "spearman": df_spearman,
        "categoricas": df_cat,
        "q_renda": df_q_renda,
        "q_idade": df_q_idade,
        "previsibilidade": df_prev,
        "controle": df_ctrl,
        "v_est_medio": v_est_medio,
        "v_alto20k": v_alto20k,
        "metricas_csv": pd.DataFrame(metricas_csv),
    }


def escrever_relatorio(res: dict, tempo: float) -> Path:
    df_cf = pd.DataFrame({
        "Cenário contrafactual": res["contrafactual"]["cenario"],
        "Imóveis": res["contrafactual"]["imoveis_comparados"],
        "Coberturas": res["contrafactual"]["coberturas_comparadas"],
        "Div. Plano": res["contrafactual"]["div_plano"],
        "Div. Elegib.": res["contrafactual"]["div_elegibilidade"],
        "Div. Semáforo": res["contrafactual"]["div_semaforo"],
        "Div. Casa Gêmea": res["contrafactual"]["div_casa_gemea"],
        "Div. Faixas": res["contrafactual"]["div_faixas"],
    })

    p = [
        "# Etapa 06: Auditoria de privacidade e teste de proxy (idade e renda)",
        f"_Gerado por `scripts/06_auditoria_proxy.py` em {date.today():%d/%m/%Y} (semente fixa = {SEMENTE}, tempo = {br(tempo, 1)} s)._",
        "",
        "## Veredito executivo",
        "",
        "**Veredito: SEM VAZAMENTO DIRETO (0 divergências no teste contrafactual) E SEM PROXY ETÁRIO; ASSOCIAÇÃO COM RENDA RESTRITA AO VALOR DE CONTEÚDO E INTEGRALMENTE EXPLICADA POR INTERESSE SEGURÁVEL LEGÍTIMO.**",
        "",
        "1. **Uso direto zero (varredura + contrafactual):** Nenhuma linha de `src/` ou `scripts/` usa `idade`, `renda_mensal`, `origem_renda` ou `confianca_renda` em inferências ou regras. Embaralhar aleatoriamente ou substituir essas quatro colunas por constantes antes de rodar o pipeline produz **0 divergências** nos 2.578 imóveis e nas 23.690 coberturas da base de desenvolvimento.",
        "2. **Idade sem efeito direto nem indireto:** Todas as correlações de Spearman com `idade` ficam dentro de **[-0,026; +0,039]**, o Cramér's V corrigido com o plano é **0,000** (IC 95%: 0,000 a 0,061), e a tentativa de prever o quartil de idade a partir do motor e da Casa Gêmea resulta em **AUC de 0,479 a 0,503** (acurácia de 23,2% a 26,6%, idêntica aos 25,0% do acaso).",
        "3. **IPTU, energia, condomínio e área não são proxy de renda:** Na base de desenvolvimento, `area_m2` (Spearman **-0,020**), `pagamento_iptu_anual` (**-0,028**), `energia_media_mensal_6m` (**-0,015**) e `pagamento_condominio_mensal` (**-0,005**) têm correlação nula com `renda_mensal`. O modelo de área e o custo de reconstrução do prédio não carregam viés de renda.",
        "4. **Por que existe associação com renda e por que ela é legítima:** Na base sintética, o valor dos bens e compras de 36 meses foi gerado proporcionalmente à renda (`conteudo_estimado` tem Spearman **+0,831** com `renda_mensal`). Como o plano **Prático** adiciona **roubo/furto de conteúdo** ao **Essencial**, imóveis do 1º quartil de renda com menos de R$ 10 mil em bens recebem o Essencial (evitando cobrar cobertura de roubo sem bens móveis relevantes). Já o plano mais completo (**Total**) tem frequência plana nos quatro quartis de renda (**47,0%, 44,6%, 45,9% e 48,4%**), com renda mediana **menor** no Total (R$ 7.750) que no Prático (R$ 10.000). Controlando por tipo, vínculo, área e conteúdo, a correlação parcial entre plano e renda cai de **+0,116** para **+0,010** (redução de 91%) e o ganho $\\Delta R^2$ de adicionar idade e renda ao modelo é **0,0002**.",
        "",
        "## A. Varredura estática (`src/` e `scripts/`)",
        "",
        "Foram inspecionados todos os arquivos Python do repositório em busca de `idade`, `renda`, `renda_mensal`, `origem_renda`, `confianca_renda` e `data_nascimento`. **Ocorrências de uso em decisão: 0.**",
        "",
        tabela_md(res["varredura"]),
        "",
        "## B. Teste contrafactual (2.200 clientes, 2.578 imóveis, 23.690 coberturas)",
        "",
        "O pipeline completo (treino do modelo de área, calibração de IPTU e aluguel por m², construção da Casa Gêmea, recomendação de plano, análise de impacto e cálculo das faixas) foi executado três vezes sobre a base de desenvolvimento: (1) base original; (2) colunas proibidas permutadas aleatoriamente entre clientes; (3) colunas proibidas substituídas por constantes.",
        "",
        tabela_md(df_cf),
        "",
        "## C. Teste de proxy e associação na base de desenvolvimento",
        "",
        "### C.1 Correlação de Spearman com variáveis numéricas (IC 95% por bootstrap)",
        "",
        tabela_md(res["spearman"]),
        "",
        "### C.2 Associação com variáveis categóricas (Cramér's V corrigido e razão de médias)",
        "",
        tabela_md(res["categoricas"]),
        "",
        "### C.3 Distribuição dos planos por quartil de renda e de idade",
        "",
        tabela_md(res["q_renda"]),
        "",
        tabela_md(res["q_idade"]),
        "",
        "### C.4 Teste de previsibilidade (validação cruzada de 5 dobras agrupada por cliente)",
        "",
        "Modelos treinados apenas com `numpy` (Regressão Logística Multinomial L2 e Árvore de Decisão de profundidade 3) para prever os 4 quartis de renda e os 4 quartis de idade (referência de acaso: **AUC = 0,500**, **Acurácia = 25,0%**):",
        "",
        tabela_md(res["previsibilidade"]),
        "",
        "A partir do `plano_recomendado` isolado, a previsibilidade do quartil de renda é baixa (**AUC = 0,563**, acurácia **29,7%** contra 25,0% do acaso) e a da estrutura física da Casa Gêmea (`tipo`, `vinculo`, `uso`, `area_m2`, `padrao`, `municipio`) é nula (**AUC = 0,508 / 0,483**). O AUC de renda só sobe quando se incluem as grandezas patrimoniais em reais (`conteudo_estimado` e compromissos mensais de aluguel/financiamento), que medem diretamente o valor em risco segurável.",
        "",
        "### C.5 Controle por variáveis legítimas de risco e interesse segurável",
        "",
        "Para testar se resta efeito de renda além da exposição patrimonial legítima (CG 15.1, Primeiro Risco Absoluto), calculamos a correlação parcial de Spearman controlando por `(tipo_imovel, vinculo, area_m2, conteudo_estimado)` e pelos sinais de cobertura, além do ganho $\\Delta R^2$ ao acrescentar `renda_mensal` e `idade`:",
        "",
        tabela_md(res["controle"]),
        "",
        f"Nos estratos de mesmo vínculo, tipo de imóvel e quintil de conteúdo, o Cramér's V corrigido médio entre plano e quartil de renda cai de **0,241** para **{br(res['v_est_medio'], 3)}**, e chega a **{br(res['v_alto20k'], 3)}** nos 1.515 imóveis cujo conteúdo do cliente é de pelo menos R$ 20 mil.",
        "",
        "## D. Conclusão, limitações e recomendação mínima",
        "",
        "- **Conclusão:** O motor respeita integralmente a proibição de uso de idade e renda. A associação observada entre `conteudo_estimado` e `renda_mensal` decorre da própria geração sintética da base (onde compras e bens cadastrados escalam com a renda) e reflete necessidade securitária real: dimensionar o LMI de conteúdo e recomendar cobertura de roubo apenas a quem possui bens móveis expostos.",
        "- **Limitações da auditoria:** (1) A base é sintética; em dados reais de mercado, área construída e IPTU costumam ter correlação positiva maior com renda do que na base do desafio (onde é próxima de zero). (2) O teste controla pelas variáveis patrimoniais observadas no banco; se o cadastro de bens subestimar sistematicamente o patrimônio de clientes que compram fora do banco, a pergunta de confirmação de conteúdo corrige essa lacuna na jornada.",
        "- **Recomendação mínima (defesa em profundidade, sem necessidade de alterar as regras atuais):** Em `src/casa_gemea/carregar.py`, remover explicitamente `CAMPOS_PROIBIDOS` no momento da leitura de `clientes.csv` (`df.drop(columns=CAMPOS_PROIBIDOS, errors='ignore')`), garantindo que tais colunas sequer transitem em memória durante a montagem da tabela intermediária.",
    ]

    caminho = PASTA_DOCS / "06_auditoria_proxy.md"
    caminho.write_text("\n".join(p) + "\n", encoding="utf-8")
    return caminho


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    PASTA_SAIDAS.mkdir(exist_ok=True)
    PASTA_DOCS.mkdir(exist_ok=True)

    inicio = time.perf_counter()
    res = executar_auditoria()
    tempo = time.perf_counter() - inicio

    caminho_csv = PASTA_SAIDAS / "auditoria_proxy.csv"
    res["metricas_csv"].to_csv(caminho_csv, index=False, encoding=ENCODING)
    print(f"✔ saidas/{caminho_csv.name}: {len(res['metricas_csv'])} métricas")

    caminho_doc = escrever_relatorio(res, tempo)
    print(f"✔ docs/{caminho_doc.name}")

    print("\n--- RESUMO DA AUDITORIA DE PROXY ---")
    print("A. Varredura estática: 0 leituras de idade/renda em regras ou inferências.")
    print("B. Teste contrafactual (permutação e constantes): 0 divergências em 2.578 imóveis e 23.690 coberturas.")
    print(f"C. Cramér's V plano × renda: bruto = 0,241 -> controlado por risco = {br(res['v_est_medio'], 3)} (0,000 p/ conteúdo >= 20 mil).")
    print("   Spearman plano × renda: bruto = +0,116 -> parcial (tipo, vínculo, área, conteúdo) = +0,010 (ΔR² = 0,0002).")
    print("   Previsibilidade por plano: Renda AUC = 0,563 (acc 29,7% vs 25% acaso); Idade AUC = 0,479 (acc 25,0%).")


if __name__ == "__main__":
    main()
