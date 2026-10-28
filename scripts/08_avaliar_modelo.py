"""Avaliação do modelo da Casa Gêmea: o que melhora e o que o modelo atual já resolve.

Uso (na raiz do projeto):
    python scripts/08_avaliar_modelo.py [E1 E2 E3 E4 E5]     (sem argumentos, roda todos)

Experimentos (base de desenvolvimento, validação cruzada agrupada por cliente, semente fixa):
    E1  modelo de área: regressão atual × modelos com mais colunas (ablação)
    E2  padrão construtivo: o que supera "sempre NORMAL"
    E3  calibração das faixas de reconstrução (conformal split) em 50%, 80% e 90%
    E4  estratégia de perguntas: motor atual × aleatória × valor esperado da informação
    E5  robustez dos pontos do plano (cada peso e limiar ±1)

Saída: saidas/avaliacao_modelo.csv (só agregados). Não altera src/ nem as saídas existentes.
"""

import sys
import warnings
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor  # noqa: E402
from sklearn.linear_model import LogisticRegression, RidgeCV  # noqa: E402
from sklearn.model_selection import GroupKFold  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from casa_gemea import area, perguntas, regras  # noqa: E402
from casa_gemea.calibracao import calibrar  # noqa: E402
from casa_gemea.carregar import ler_base, montar_tabela_imoveis  # noqa: E402
from casa_gemea.config import ENCODING, PASTA_SAIDAS  # noqa: E402
from casa_gemea.inferencias import construir_casa_gemea, inferir_tipo  # noqa: E402

warnings.filterwarnings("ignore")
SEMENTE = 42
N_DOBRAS = 5
SAIDA = PASTA_SAIDAS / "avaliacao_modelo.csv"
LINHAS: list[dict] = []   # métricas de todos os experimentos


def registrar(experimento: str, variante: str, **metricas) -> None:
    for nome, valor in metricas.items():
        LINHAS.append({"experimento": experimento, "variante": variante, "metrica": nome, "valor": round(float(valor), 4)})


def dobras(tabela: pd.DataFrame, repeticoes: int = 1):
    """Dobras agrupadas por cliente (um cliente nunca fica em treino e teste ao mesmo tempo)."""
    for rep in range(repeticoes):
        ids = tabela["cliente_id"].unique()
        sorteio = np.random.default_rng(SEMENTE + rep).permutation(len(ids))
        grupo = pd.Series(sorteio % N_DOBRAS, index=ids)
        d = tabela["cliente_id"].map(grupo).to_numpy()
        for k in range(N_DOBRAS):
            yield np.where(d != k)[0], np.where(d == k)[0]


def carregar_dev() -> pd.DataFrame:
    tabela = inferir_tipo(montar_tabela_imoveis(ler_base("desenvolvimento")))
    # Colunas derivadas usadas como candidatas (todas calculáveis sem a área).
    t = tabela
    t["log_iptu"] = np.log(t["pagamento_iptu_anual"].clip(lower=1))
    t["log_energia"] = np.log(t["energia_media_mensal_6m"].clip(lower=1))
    t["log_agua"] = np.log(t["agua_media_mensal_6m"].clip(lower=1))
    t["log_condominio"] = np.log1p(t["pagamento_condominio_mensal"])
    t["log_internet"] = np.log1p(t["internet_mensal"])
    t["log_compras"] = np.log1p(t["compras_moveis_36m"] + t["compras_eletrodomesticos_36m"] + t["compras_eletronicos_36m"])
    t["log_bens"] = np.log1p(t["bens_valor_cadastrado"])
    t["log_renda"] = np.log1p(t["renda_mensal"])
    t["log_financiamento"] = np.log1p(t["parcela_financiamento_imobiliario"])
    t["log_aluguel"] = np.log1p(t["valor_aluguel_recorrente"])
    t["pet"] = (t["possui_pet_informado"] == "SIM").astype(float)
    t["eh_casa_f"] = t["eh_casa"].astype(float)
    t["tem_condominio"] = (t["pagamento_condominio_mensal"] > 0).astype(float)
    t["eh_apto"] = (t["possui_termo_apartamento"] == "SIM").astype(float)
    return t


# Grupos de colunas testados na ablação do modelo de área.
BASE_NUM = ["log_iptu", "log_energia", "eh_casa_f"]
GRUPOS = {
    "água": ["log_agua"],
    "condomínio": ["log_condominio", "tem_condominio"],
    "internet": ["log_internet"],
    "compras e bens": ["log_compras", "log_bens"],
    "financiamento e aluguel": ["log_financiamento", "log_aluguel"],
    "coordenadas": ["latitude_aproximada", "longitude_aproximada"],
    "UF (CUB)": ["uf_real"],
    "renda": ["log_renda"],
    "idade": ["idade"],
    "dependentes": ["quantidade_dependentes", "pet"],
    "app e maturidade digital": ["indice_maturidade_digital", "frequencia_acesso_app_90d", "qtd_produtos_seguridade"],
}


def matriz(t: pd.DataFrame, numericas: list[str], categoricas: list[str]) -> pd.DataFrame:
    X = t[numericas].astype(float).copy()
    for c in categoricas:
        X = X.join(pd.get_dummies(t[c], prefix=c, drop_first=True).astype(float))
    return X


def prever_cv(t: pd.DataFrame, numericas, categoricas, modelo: str, quantis=(0.1, 0.5, 0.9)):
    """Previsão fora da amostra de log(área). Retorna (central, [quantis]) por dobra agrupada."""
    y = np.log(t["area_cadastrada_m2"].to_numpy())
    X = matriz(t, numericas, categoricas).to_numpy()
    central = np.zeros(len(t))
    q = {p: np.zeros(len(t)) for p in quantis}
    for tr, te in dobras(t):
        if modelo == "ols":
            A = np.column_stack([np.ones(len(tr)), X[tr]])
            coef, *_ = np.linalg.lstsq(A, y[tr], rcond=None)
            central[te] = np.column_stack([np.ones(len(te)), X[te]]) @ coef
        elif modelo == "ridge":
            esc = StandardScaler().fit(X[tr])
            m = RidgeCV(alphas=np.logspace(-2, 3, 12)).fit(esc.transform(X[tr]), y[tr])
            central[te] = m.predict(esc.transform(X[te]))
        elif modelo == "gbm":
            m = GradientBoostingRegressor(n_estimators=250, max_depth=3, learning_rate=0.04, subsample=0.8, random_state=SEMENTE)
            central[te] = m.fit(X[tr], y[tr]).predict(X[te])
        elif modelo == "quantilica":
            for p in quantis:
                m = GradientBoostingRegressor(loss="quantile", alpha=p, n_estimators=200, max_depth=2, learning_rate=0.05,
                                              subsample=0.8, random_state=SEMENTE)
                q[p][te] = m.fit(X[tr], y[tr]).predict(X[te])
            central[te] = q[0.5][te]
    return central, q


def metricas_area(real: np.ndarray, log_prev: np.ndarray) -> dict:
    prev = np.exp(log_prev)
    res = np.log(real) - log_prev
    return {
        "erro_percentual_mediano": np.median(np.abs(real - prev) / real),
        "mae_m2": np.mean(np.abs(real - prev)),
        "r2_log": 1 - res.var() / np.log(real).var(),
    }


# ------------------------------------------------------------------------------ E1
def experimento_1() -> None:
    print("\n== E1: modelo de área ==")
    t = carregar_dev()
    t = t[t["area_cadastrada_m2"] > 0].reset_index(drop=True)
    real = t["area_cadastrada_m2"].to_numpy()
    registrar("E1", "n_imoveis_com_area", n=len(t))

    # Modelo atual: log(IPTU), log(energia), é casa, município (dummies).
    atual_num, atual_cat = BASE_NUM, ["municipio_real"]
    cen, _ = prever_cv(t, atual_num, atual_cat, "ols")
    m = metricas_area(real, cen)
    registrar("E1", "atual (OLS: IPTU, energia, casa, município)", **m)
    print("atual", m)

    # Cobertura do intervalo de 80% com resíduos globais (método atual), em validação cruzada.
    def cobertura_80(central: np.ndarray) -> tuple[float, float]:
        cob, larg = [], []
        res = np.log(real) - central
        for tr, te in dobras(t):
            lo, hi = np.quantile(res[tr], [0.1, 0.9])
            cob.append(((res[te] >= lo) & (res[te] <= hi)).mean() * len(te))
            larg.append((hi - lo))
        return sum(cob) / len(t), float(np.mean(larg))
    c, w = cobertura_80(cen)
    registrar("E1", "atual (OLS: IPTU, energia, casa, município)", cobertura_intervalo_80=c, largura_log_intervalo_80=w)

    # Ablação "adicionar uma coluna ao modelo atual" (OLS) e "tirar uma coluna do modelo completo".
    for nome, cols in GRUPOS.items():
        num = atual_num + [c for c in cols if c != "uf_real"]
        cat = atual_cat + (["uf_real"] if "uf_real" in cols else [])
        cen_g, _ = prever_cv(t, num, cat, "ols")
        mg = metricas_area(real, cen_g)
        delta = mg["erro_percentual_mediano"] - m["erro_percentual_mediano"]
        registrar("E1", f"+ {nome} (OLS)", **mg, delta_erro_pct_mediano=delta)
        print(f"+ {nome:28s} erro {mg['erro_percentual_mediano']:.4f}  delta {delta:+.4f}  R2 {mg['r2_log']:.4f}")

    todas_num = BASE_NUM + [c for g in GRUPOS.values() for c in g if c != "uf_real"]
    todas_cat = ["municipio_real", "uf_real"]
    for modelo, rotulo in [("ols", "todas as colunas (OLS)"), ("ridge", "todas as colunas (Ridge)"), ("gbm", "todas as colunas (gradient boosting)")]:
        cen_m, _ = prever_cv(t, todas_num, todas_cat, modelo)
        mm = metricas_area(real, cen_m)
        c, w = cobertura_80(cen_m)
        registrar("E1", rotulo, **mm, cobertura_intervalo_80=c, largura_log_intervalo_80=w)
        print(rotulo, mm, c, w)
    # Modelo proposto: só as colunas que mostraram ganho (sem idade, renda, app, coordenadas, internet, UF).
    proposto = BASE_NUM + ["log_agua", "quantidade_dependentes", "pet", "log_condominio", "tem_condominio",
                           "log_financiamento", "log_aluguel", "log_compras", "log_bens"]
    cen_p, _ = prever_cv(t, proposto, atual_cat, "ols")
    mp = metricas_area(real, cen_p)
    c, w = cobertura_80(cen_p)
    registrar("E1", "proposto (OLS: atual + água, dependentes, pet, condomínio, financiamento, aluguel, compras, bens)", **mp,
              cobertura_intervalo_80=c, largura_log_intervalo_80=w)
    print("proposto", mp, c, w)

    # Ablação inversa: tira um grupo do modelo completo (OLS).
    completo = metricas_area(real, prever_cv(t, todas_num, todas_cat, "ols")[0])
    for nome, cols in GRUPOS.items():
        num = [c for c in todas_num if c not in cols]
        cat = [c for c in todas_cat if c not in cols]
        mg = metricas_area(real, prever_cv(t, num, cat, "ols")[0])
        registrar("E1", f"completo sem {nome} (OLS)", **mg,
                  delta_erro_pct_mediano=mg["erro_percentual_mediano"] - completo["erro_percentual_mediano"])
        print(f"completo sem {nome:26s} R2 {mg['r2_log']:.4f} (completo {completo['r2_log']:.4f})")

    # Intervalo de confiança (bootstrap por imóvel) da diferença de erro percentual mediano: completo × atual.
    cen_c = prever_cv(t, todas_num, todas_cat, "ols")[0]
    e_atual, e_comp = np.abs(np.exp(cen) - real) / real, np.abs(np.exp(cen_c) - real) / real
    rng = np.random.default_rng(SEMENTE)
    dif = [np.median(e_comp[i]) - np.median(e_atual[i]) for i in (rng.integers(0, len(t), len(t)) for _ in range(1000))]
    lo, hi = np.quantile(dif, [0.025, 0.975])
    registrar("E1", "completo (OLS) menos atual: diferença do erro percentual mediano", diferenca=np.mean(dif), ic95_inferior=lo, ic95_superior=hi)
    print("dif completo - atual", np.mean(dif), lo, hi)

    # Boosting só com as colunas do modelo atual (isola o efeito do algoritmo).
    cen_m, _ = prever_cv(t, BASE_NUM, ["municipio_real"], "gbm")
    mm = metricas_area(real, cen_m)
    c, w = cobertura_80(cen_m)
    registrar("E1", "colunas do modelo atual (gradient boosting)", **mm, cobertura_intervalo_80=c, largura_log_intervalo_80=w)
    print("gbm mesmas colunas", mm, c, w)

    # Regressão quantílica (intervalo direto, sem resíduo global).
    cen_q, q = prever_cv(t, BASE_NUM + ["log_condominio", "tem_condominio", "log_agua"], ["municipio_real"], "quantilica")
    lo, hi = q[0.1], q[0.9]
    mq = metricas_area(real, cen_q)
    registrar("E1", "regressão quantílica (boosting, IPTU+energia+casa+condomínio+água+município)", **mq,
              cobertura_intervalo_80=((np.log(real) >= lo) & (np.log(real) <= hi)).mean(),
              largura_log_intervalo_80=np.mean(hi - lo))
    print("quantilica", mq, ((np.log(real) >= lo) & (np.log(real) <= hi)).mean(), np.mean(hi - lo))

    # Correlação do gerador: R² da área explicada só por IPTU, só por energia.
    for col in ["log_iptu", "log_energia", "log_agua", "log_condominio", "log_renda"]:
        r = np.corrcoef(t[col], np.log(real))[0, 1]
        registrar("E1", f"correlacao_com_log_area:{col}", correlacao=r)


# ------------------------------------------------------------------------------ E2
def experimento_2() -> None:
    print("\n== E2: padrão construtivo ==")
    t = carregar_dev()
    cal = calibrar(t)
    t["razao_iptu_m2"] = np.nan
    com_area = t["area_cadastrada_m2"] > 0
    t.loc[com_area, "razao_iptu_m2"] = (
        t.loc[com_area, "pagamento_iptu_anual"] / t.loc[com_area, "area_cadastrada_m2"]
    ) / t.loc[com_area, "municipio_real"].map(cal.iptu_m2_mediana)
    t["log_iptu_m2"] = np.log(t["pagamento_iptu_anual"].clip(lower=1) / t["area_cadastrada_m2"].where(com_area))
    rot = t[t["padrao_construtivo_cadastrado"] != "NAO_DISPONIVEL"].reset_index(drop=True)
    y = rot["padrao_construtivo_cadastrado"].to_numpy()
    classes = ["ECONOMICO", "NORMAL", "SUPERIOR"]
    registrar("E2", "n_imoveis_com_padrao", n=len(rot))
    registrar("E2", "frequencia_classe_NORMAL", frequencia=(y == "NORMAL").mean())

    def acc(pred, mask=None):
        mask = np.ones(len(y), bool) if mask is None else mask
        yt, yp = y[mask], np.asarray(pred)[mask]
        recalls = [np.mean(yp[yt == c] == c) for c in classes if (yt == c).any()]
        f1 = []
        for c in classes:
            tp = np.sum((yp == c) & (yt == c)); p = tp / max(np.sum(yp == c), 1); r = tp / max(np.sum(yt == c), 1)
            f1.append(0 if p + r == 0 else 2 * p * r / (p + r))
        return {"acuracia": np.mean(yp == yt), "acuracia_balanceada": np.mean(recalls), "f1_macro": np.mean(f1), "n": mask.sum()}

    # Subconjunto onde a regra atual funciona (área real disponível).
    tem_area = rot["area_cadastrada_m2"].to_numpy() > 0
    registrar("E2", "n_com_padrao_e_area", n=tem_area.sum())
    regra_atual = np.array([
        "NORMAL" if np.isnan(v) else ("SUPERIOR" if v >= 1.25 else "ECONOMICO" if v <= 0.85 else "NORMAL") for v in rot["razao_iptu_m2"]
    ])
    for nome, pred in [("sempre NORMAL", np.full(len(y), "NORMAL")), ("regra atual (IPTU/m² × cidade)", regra_atual)]:
        for esc, mask in [("todos", None), ("com área real", tem_area)]:
            a = acc(pred, mask); registrar("E2", f"{nome} [{esc}]", **a); print(nome, esc, a)

    # Modelos com todas as colunas (validação cruzada agrupada por cliente).
    base = ["log_iptu", "log_energia", "log_agua", "log_condominio", "log_internet", "log_compras", "log_bens",
            "log_renda", "idade", "quantidade_dependentes", "latitude_aproximada", "longitude_aproximada",
            "eh_casa_f", "tem_condominio", "log_financiamento", "log_aluguel"]
    rot["razao_iptu_m2"] = rot["razao_iptu_m2"].fillna(1.0)
    rot["log_area"] = np.log(rot["area_cadastrada_m2"].where(rot["area_cadastrada_m2"] > 0)).fillna(0)
    rot["tem_area"] = tem_area.astype(float)
    rot["iptu_rel_cidade"] = np.log(rot["pagamento_iptu_anual"].clip(lower=1)) - np.log(
        rot.groupby("municipio_real")["pagamento_iptu_anual"].transform("median"))
    rot["energia_rel_cidade"] = np.log(rot["energia_media_mensal_6m"].clip(lower=1)) - np.log(
        rot.groupby("municipio_real")["energia_media_mensal_6m"].transform("median"))
    conjuntos = {
        "logística: IPTU/m² e energia relativos à cidade": ["razao_iptu_m2", "iptu_rel_cidade", "energia_rel_cidade", "tem_area"],
        "logística: todas as colunas": base + ["razao_iptu_m2", "log_area", "tem_area", "iptu_rel_cidade", "energia_rel_cidade"],
        "boosting: todas as colunas": base + ["razao_iptu_m2", "log_area", "tem_area", "iptu_rel_cidade", "energia_rel_cidade"],
    }
    for nome, cols in conjuntos.items():
        X = matriz(rot, cols, ["municipio_real"] if "todas" in nome else []).to_numpy()
        pred = np.empty(len(y), dtype=object)
        for tr, te in dobras(rot):
            if nome.startswith("logística"):
                esc = StandardScaler().fit(X[tr])
                m = LogisticRegression(max_iter=2000, C=0.5, class_weight="balanced").fit(esc.transform(X[tr]), y[tr])
                pred[te] = m.predict(esc.transform(X[te]))
            else:
                m = GradientBoostingClassifier(n_estimators=150, max_depth=2, learning_rate=0.05, subsample=0.8, random_state=SEMENTE)
                pred[te] = m.fit(X[tr], y[tr]).predict(X[te])
        for esc, mask in [("todos", None), ("com área real", tem_area)]:
            a = acc(pred, mask); registrar("E2", f"{nome} [{esc}]", **a); print(nome, esc, a)


# ------------------------------------------------------------------------------ E3
def fatores_cub() -> dict:
    return regras.carregar_referencias(calibrar(inferir_tipo(montar_tabela_imoveis(ler_base("desenvolvimento"))))).fator_padrao


def experimento_3() -> None:
    """Faixa do custo de reconstrução com área e padrão escondidos: cobertura nominal × empírica."""
    print("\n== E3: calibração das faixas ==")
    t = carregar_dev()
    cal0 = calibrar(t)
    ref = regras.carregar_referencias(cal0)
    alvo = t[(t["area_cadastrada_m2"] > 0) & (t["padrao_construtivo_cadastrado"] != "NAO_DISPONIVEL")].reset_index(drop=True)
    com_area = t[t["area_cadastrada_m2"] > 0].reset_index(drop=True)
    registrar("E3", "n_imoveis_validacao", n=len(alvo))

    grupo = lambda d: np.where(d["eh_casa"], "CASA", "APARTAMENTO")
    cub = alvo["uf_real"].map(ref.cub_r8n).to_numpy()
    g = grupo(alvo)
    f = lambda p: np.array([ref.fator_padrao[(gi, p)] for gi in g])
    f_real = np.array([ref.fator_padrao[(gi, pi)] for gi, pi in zip(g, alvo["padrao_construtivo_cadastrado"])])
    f_min, f_max = (f("ECONOMICO") + f("NORMAL")) / 2, (f("SUPERIOR") + f("NORMAL")) / 2   # padrão escondido
    verdade = alvo["area_cadastrada_m2"].to_numpy() * cub * f_real

    # Área prevista fora da amostra, treinando só com imóveis de outros clientes; resíduos globais para a faixa.
    area_prev = np.zeros(len(alvo)); resid_min = np.zeros(len(alvo)); resid_max = np.zeros(len(alvo))
    chave = alvo["cliente_id"]
    for tr, te in dobras(alvo):
        clientes_te = set(chave.iloc[te])
        treino = com_area[~com_area["cliente_id"].isin(clientes_te)]
        modelo = area.treinar(pd.concat([treino, alvo.iloc[te].assign(area_cadastrada_m2=0)]))
        prev = modelo.prever(alvo.iloc[te])
        area_prev[te] = prev["area_estimada_m2"]; resid_min[te] = modelo.residuo_min; resid_max[te] = modelo.residuo_max
    area_lo = area_prev * np.exp(resid_min); area_hi = area_prev * np.exp(resid_max)
    central = area_prev * cub * np.sqrt(f_min * f_max)
    w = np.sqrt((np.log(area_hi / area_lo) / 2) ** 2 + (np.log(f_max / f_min) / 2) ** 2)   # igual a regras.faixa_combinada
    score = np.abs(np.log(verdade / central)) / w     # quantas "meias-larguras" o erro ocupa

    atual_cobertura = np.mean(score <= 1)
    registrar("E3", "faixa atual (k = 1)", cobertura_empirica=atual_cobertura, razao_max_min_mediana=np.median(np.exp(2 * w)))
    print("atual", atual_cobertura, np.median(np.exp(2 * w)))

    # Conformal split: k é o quantil do escore nas dobras de calibração; avalia na dobra de teste.
    for nominal in (0.5, 0.8, 0.9):
        dentro = np.zeros(len(alvo), bool); razao = np.zeros(len(alvo))
        for tr, te in dobras(alvo):
            n = len(tr)
            k = np.quantile(score[tr], min(1.0, np.ceil((n + 1) * nominal) / n))
            dentro[te] = score[te] <= k; razao[te] = np.exp(2 * k * w[te])
        registrar("E3", f"conformal nominal {nominal:.0%}", cobertura_empirica=dentro.mean(),
                  razao_max_min_mediana=np.median(razao), estreitamento_vs_atual=1 - np.median(np.log(razao)) / np.median(2 * w))
        print("conformal", nominal, dentro.mean(), np.median(razao))

    # Mesma curva só para a área (intervalo global de resíduos × conformal por tipo de imóvel).
    real = alvo["area_cadastrada_m2"].to_numpy(); res = np.log(real / area_prev)
    for nominal in (0.5, 0.8, 0.9):
        dentro = np.zeros(len(alvo), bool); larg = []
        casa = alvo["eh_casa"].to_numpy()
        for tr, te in dobras(alvo):
            for tipo in (True, False):   # Mondrian: calibra separado para casa e apartamento
                a = tr[casa[tr] == tipo]; b = te[casa[te] == tipo]
                lo, hi = np.quantile(res[a], [(1 - nominal) / 2, 1 - (1 - nominal) / 2])
                dentro[b] = (res[b] >= lo) & (res[b] <= hi); larg.append(hi - lo)
        registrar("E3", f"área, conformal por tipo, nominal {nominal:.0%}", cobertura_empirica=dentro.mean(), largura_log=np.mean(larg))
        print("area mondrian", nominal, dentro.mean(), np.mean(larg))


# ------------------------------------------------------------------------------ E5
PESOS_BASE = {"conteudo_alto": 2, "conteudo_medio": 1, "eletro": 1, "vidros": 1, "casa": 1,
              "inquilino": 2, "locador": 2, "pet": 1, "dependentes": 1, "limiar_total": 3, "limiar_total_combinado": 2,
              "limiar_pratico_combinado": 1, "limiar_pratico": 2}


def plano_parametrico(r: pd.Series, p: dict) -> str:
    """Mesma lógica de regras.pontuar_plano, com os pesos e limiares parametrizados."""
    conteudo = r["conteudo_estimado"] * r["fracao_conteudo_do_cliente"]
    roubo_util = not r.get("imovel_desocupado", False)
    pr = 0
    if roubo_util and conteudo >= regras.CONTEUDO_RELEVANTE:
        pr += p["conteudo_alto"]
    elif roubo_util and conteudo >= regras.CONTEUDO_MODERADO:
        pr += p["conteudo_medio"]
    if roubo_util and r["eletronicos_eletro_max"] * r["fracao_conteudo_do_cliente"] >= regras.ELETRO_RELEVANTE:
        pr += p["eletro"]
    if r["sinal_vidros"]:
        pr += p["vidros"]
    if roubo_util and r["eh_casa"]:
        pr += p["casa"]
    to = 0
    if r["vinculo"] == "INQUILINO":
        to += p["inquilino"]
    if r["vinculo"] == "PROPRIETARIO_LOCADOR":
        to += p["locador"]
    if r["possui_pet_informado"] == "SIM":
        to += p["pet"]
    if r["quantidade_dependentes"] > 0:
        to += p["dependentes"]
    if to >= p["limiar_total"] or (to >= p["limiar_total_combinado"] and pr >= p["limiar_pratico_combinado"]):
        return "TOTAL"
    return "PRATICO" if pr >= p["limiar_pratico"] else "ESSENCIAL"


def casa_com_fracao(base: str, cal=None, modelo=None) -> pd.DataFrame:
    tabela = montar_tabela_imoveis(ler_base(base))
    dev = montar_tabela_imoveis(ler_base("desenvolvimento"))
    modelo = area.treinar(inferir_tipo(dev)); cal = calibrar(dev)
    casa = construir_casa_gemea(tabela, modelo, cal)
    casa["fracao_conteudo_do_cliente"] = casa.apply(lambda r: regras.interesse_seguravel(r)[2], axis=1)
    return casa


def experimento_5() -> None:
    print("\n== E5: robustez dos pontos do plano ==")
    for base in ("desenvolvimento", "teste"):
        casa = casa_com_fracao(base)
        linhas = [r for _, r in casa.iterrows()]
        oficial = np.array([regras.pontuar_plano(r)["plano_recomendado"] for r in linhas])
        base_param = np.array([plano_parametrico(r, PESOS_BASE) for r in linhas])
        assert (oficial == base_param).all(), "versão parametrizada diverge do motor"
        registrar("E5", f"{base}: distribuição", essencial=(oficial == "ESSENCIAL").mean(), pratico=(oficial == "PRATICO").mean(), total=(oficial == "TOTAL").mean())
        pior = 0
        for chave, delta in product(PESOS_BASE, (-1, +1)):
            p = dict(PESOS_BASE); p[chave] = max(0, p[chave] + delta)
            novo = np.array([plano_parametrico(r, p) for r in linhas])
            mudou = (novo != oficial).mean()
            pior = max(pior, mudou)
            registrar("E5", f"{base}: {chave} {delta:+d}", imoveis_que_mudam_de_plano=mudou)
        registrar("E5", f"{base}: pior caso de um ponto", imoveis_que_mudam_de_plano=pior)
        # Perturbação conjunta: todos os pesos com ruído de ±1 sorteado (500 sorteios, mediana e p95).
        rng = np.random.default_rng(SEMENTE)
        pesos_pontuaveis = [k for k in PESOS_BASE if not k.startswith("limiar")]
        taxas = []
        for _ in range(60):
            p = dict(PESOS_BASE)
            for k in pesos_pontuaveis:
                p[k] = max(0, p[k] + int(rng.integers(-1, 2)))
            taxas.append((np.array([plano_parametrico(r, p) for r in linhas]) != oficial).mean())
        registrar("E5", f"{base}: todos os pesos com ruído -1/0/+1 (60 sorteios)", mediana=np.median(taxas), p95=np.quantile(taxas, 0.95))
        print(base, "pior um ponto", pior, "conjunto", np.median(taxas), np.quantile(taxas, 0.95))


# ------------------------------------------------------------------------------ E4
CAMPOS_E4 = ["area_m2", "padrao_construtivo", "conteudo", "vinculo", "tipo_imovel"]
# Probabilidade a priori de a inferência estar certa nos campos ambíguos (premissa declarada, sem rótulo na base).
P_VINCULO_CERTO, P_TIPO_CERTO = 0.5, 0.7
N_IMOVEIS_E4 = 600
ORDENS_E4 = ("motor atual", "aleatória", "valor esperado da informação")


def aplicar_resposta(r: pd.Series, campo: str, valor) -> pd.Series:
    """Confirma um campo com o valor informado (mesma mecânica de perguntas._cenarios_*)."""
    from casa_gemea.config import ALTA, CONFIRMADO, OBSERVADO
    from casa_gemea.inferencias import _regra_uso
    if campo == "area_m2":
        return perguntas._com(r, area_m2=valor, area_min_m2=valor, area_max_m2=valor, area_m2_selo=CONFIRMADO)
    if campo == "padrao_construtivo":
        return perguntas._com(r, padrao_construtivo=valor, padrao_construtivo_selo=OBSERVADO, padrao_construtivo_confianca=ALTA)
    if campo == "conteudo":
        escala = valor / r["conteudo_max"] if r["conteudo_max"] > 0 else 1.0
        eletro = r["eletronicos_eletro_max"] * escala
        return perguntas._com(r, conteudo_min=valor, conteudo_max=valor, conteudo_estimado=valor,
                              eletronicos_eletro_min=eletro, eletronicos_eletro_max=eletro)
    if campo == "vinculo":
        novo = perguntas._com(r, vinculo=valor, vinculo_confianca=ALTA, vinculo_selo=CONFIRMADO)
        novo["uso_imovel"] = _regra_uso(novo)[0]
        return novo
    if campo == "tipo_imovel":
        return perguntas._com(r, tipo_imovel=valor, tipo_imovel_confianca=ALTA, tipo_imovel_selo=CONFIRMADO)
    raise ValueError(campo)


def cenarios_de_resposta(r: pd.Series, campo: str, freq_padrao: dict) -> list[tuple[float, object]]:
    """Respostas possíveis e suas probabilidades a priori (sem usar a verdade do imóvel)."""
    if campo == "area_m2":
        return [(0.2, a) for a in np.geomspace(r["area_min_m2"], r["area_max_m2"], 5)]
    if campo == "padrao_construtivo":
        return [(p, c) for c, p in freq_padrao.items()]
    if campo == "conteudo":
        meio = float(np.sqrt(max(r["conteudo_min"], 1) * max(r["conteudo_max"], 1)))
        return [(1 / 3, v) for v in (r["conteudo_min"], meio, r["conteudo_max"])]
    if campo == "vinculo":
        alt = "PROPRIETARIO_QUITADO" if r["vinculo"] == "PROPRIETARIO_LOCADOR" else "INQUILINO"
        return [(P_VINCULO_CERTO, r["vinculo"]), (1 - P_VINCULO_CERTO, alt)]
    alt = perguntas.ALTERNATIVAS_TIPO.get(r["tipo_imovel"], ["CASA"])[0]
    return [(P_TIPO_CERTO, r["tipo_imovel"]), (1 - P_TIPO_CERTO, alt)]


def estado_e4(r: pd.Series, ref) -> tuple[str, float, float, float]:
    """(plano, largura log da faixa de incêndio, mín, máx)."""
    incendio = regras.calcular_coberturas(r, ref)[0]
    plano = regras.pontuar_plano(r)["plano_recomendado"]
    return plano, float(np.log(incendio["faixa_valor_max"] / incendio["faixa_valor_min"])), incendio["faixa_valor_min"], incendio["faixa_valor_max"]


def escolher_campo(ordem: str, r: pd.Series, ref, incertos: list[str], freq_padrao: dict, rng) -> str | None:
    if not incertos:
        return None
    if ordem == "aleatória":
        return incertos[rng.integers(len(incertos))]
    if ordem == "motor atual":
        respondidas = frozenset(set(CAMPOS_E4) - set(incertos))
        fila = perguntas.analisar(r, ref, regras.ELEGIVEL, respondidas)["perguntas"]
        fila = [p["campo"] for p in fila if p["campo"] in incertos]   # obra e ocupação não são simuladas
        return fila[0] if fila else None
    # valor esperado da informação: chance de mudar o plano + redução relativa esperada da largura
    plano0, largura0, _, _ = estado_e4(r, ref)
    melhor, melhor_score = None, -1.0
    for campo in incertos:
        muda, ganho = 0.0, 0.0
        for peso, valor in cenarios_de_resposta(r, campo, freq_padrao):
            plano1, largura1, _, _ = estado_e4(aplicar_resposta(r, campo, valor), ref)
            muda += peso * (plano1 != plano0)
            ganho += peso * (1 - largura1 / largura0 if largura0 > 0 else 0.0)
        if muda + ganho > melhor_score:
            melhor, melhor_score = campo, muda + ganho
    return melhor


def experimento_4() -> None:
    print("\n== E4: estratégia de perguntas ==")
    bruta = montar_tabela_imoveis(ler_base("desenvolvimento"))
    rng = np.random.default_rng(SEMENTE)
    conhecidos = bruta.loc[bruta["padrao_construtivo_cadastrado"] != "NAO_DISPONIVEL", "padrao_construtivo_cadastrado"]
    freq_padrao = conhecidos.value_counts(normalize=True).to_dict()
    com_area = bruta.index[bruta["area_cadastrada_m2"] > 0]
    amostra = bruta.loc[rng.choice(com_area, N_IMOVEIS_E4, replace=False)]
    dobra = pd.Series(rng.integers(0, N_DOBRAS, len(amostra)), index=amostra.index)

    # Casa Gêmea "às cegas": área e padrão escondidos; modelo e calibração treinados sem os clientes avaliados.
    escondida = []
    for k in range(N_DOBRAS):
        alvo = amostra[dobra == k]
        treino = bruta[~bruta["cliente_id"].isin(set(alvo["cliente_id"]))]
        modelo, cal = area.treinar(inferir_tipo(treino)), calibrar(treino)
        oculto = alvo.copy()
        oculto["area_cadastrada_m2"] = 0
        oculto["padrao_construtivo_cadastrado"] = "NAO_DISPONIVEL"
        escondida.append(construir_casa_gemea(oculto, modelo, cal))
    casas = pd.concat(escondida)
    ref = regras.carregar_referencias(calibrar(bruta))
    casas["fracao_conteudo_do_cliente"] = casas.apply(lambda r: regras.interesse_seguravel(r)[2], axis=1)

    resultados = {o: [] for o in ORDENS_E4}
    campos_incertos = []
    max_k = len(CAMPOS_E4)
    for idx, r in casas.iterrows():
        real = amostra.loc[idx]
        # Verdade: a da base onde existe (área, padrão); sorteada nas premissas declaradas onde não existe.
        verdade = {"area_m2": float(real["area_cadastrada_m2"])}
        verdade["padrao_construtivo"] = (real["padrao_construtivo_cadastrado"] if real["padrao_construtivo_cadastrado"] != "NAO_DISPONIVEL"
                                         else rng.choice(list(freq_padrao), p=list(freq_padrao.values())))
        verdade["conteudo"] = float(np.exp(rng.uniform(np.log(max(r["conteudo_min"], 1)), np.log(max(r["conteudo_max"], 1)))))
        incerto_vinculo = (r["vinculo"] == "PROPRIETARIO_LOCADOR" and r["vinculo_confianca"] != "ALTA") or r["vinculo"] == "INDEFINIDO"
        incerto_tipo = r["tipo_imovel_confianca"] != "ALTA"
        alt_v = "PROPRIETARIO_QUITADO" if r["vinculo"] == "PROPRIETARIO_LOCADOR" else "INQUILINO"
        alt_t = perguntas.ALTERNATIVAS_TIPO.get(r["tipo_imovel"], ["CASA"])[0]
        verdade["vinculo"] = r["vinculo"] if (not incerto_vinculo or rng.random() < P_VINCULO_CERTO) else alt_v
        verdade["tipo_imovel"] = r["tipo_imovel"] if (not incerto_tipo or rng.random() < P_TIPO_CERTO) else alt_t
        incertos0 = ["area_m2", "padrao_construtivo"] + (["conteudo"] if r["conteudo_min"] != r["conteudo_max"] else []) \
            + (["vinculo"] if incerto_vinculo else []) + (["tipo_imovel"] if incerto_tipo else [])
        campos_incertos.append(len(incertos0))

        pleno = r
        for campo in incertos0:
            pleno = aplicar_resposta(pleno, campo, verdade[campo])
        plano_real, _, f_min, f_max = estado_e4(pleno, ref)
        centro_real = np.sqrt(f_min * f_max)

        for ordem, saida in resultados.items():
            estado, incertos, perguntadas = r, list(incertos0), 0
            for k in range(max_k + 1):
                plano, largura, fmin, fmax = estado_e4(estado, ref)
                saida.append({"k": k, "plano_certo": plano == plano_real, "largura_log": largura,
                              "contem_verdade": fmin <= centro_real <= fmax, "perguntadas": perguntadas})
                campo = escolher_campo(ordem, estado, ref, incertos, freq_padrao, rng) if k < max_k else None
                if campo is None:
                    continue    # o motor parou (ou acabaram os campos): o estado se mantém nos k seguintes
                estado = aplicar_resposta(estado, campo, verdade[campo])
                incertos.remove(campo)
                perguntadas += 1

    registrar("E4", "amostra", imoveis=len(casas), campos_incertos_media=np.mean(campos_incertos))
    for ordem, saida in resultados.items():
        d = pd.DataFrame(saida)
        for k, g in d.groupby("k"):
            registrar("E4", f"{ordem}, k={k}", plano_certo=g["plano_certo"].mean(), razao_max_min_mediana=np.exp(g["largura_log"]).median(),
                      faixa_contem_verdade=g["contem_verdade"].mean(), perguntas_feitas_media=g["perguntadas"].mean())
            print(f"{ordem:30s} k={k} plano {g['plano_certo'].mean():.3f}  razão {np.exp(g['largura_log']).median():.2f}  "
                  f"contém {g['contem_verdade'].mean():.3f}  feitas {g['perguntadas'].mean():.2f}")


if __name__ == "__main__":
    escolhidos = {a.upper() for a in sys.argv[1:]} or {"E1", "E2", "E3", "E4", "E5"}
    rodadas = {"E1": experimento_1, "E2": experimento_2, "E3": experimento_3, "E4": experimento_4, "E5": experimento_5}
    for nome, funcao in rodadas.items():
        if nome in escolhidos:
            funcao()
    antigo = pd.read_csv(SAIDA, encoding=ENCODING) if SAIDA.exists() else pd.DataFrame()
    novo = pd.DataFrame(LINHAS)
    if len(antigo):
        antigo = antigo[~antigo["experimento"].isin(novo["experimento"].unique())]
    pd.concat([antigo, novo]).to_csv(SAIDA, index=False, encoding=ENCODING)
    print(f"\nMétricas gravadas em {SAIDA.relative_to(SAIDA.parents[1])}")
