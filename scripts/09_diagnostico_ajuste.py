"""Diagnóstico de ajuste: o modelo generaliza, decora (overfitting) ou é simples demais (underfitting)?

Uso (na raiz do projeto):
    python scripts/09_diagnostico_ajuste.py [V1 V2 V3 V4 V5 V6 V7]     (sem argumentos, roda todos)

Verificações (semente 42; só agregados):
    V1  teste cego: treina no desenvolvimento, avalia nos imóveis do teste com área real; deriva entre bases
    V2  curvas de aprendizado (tamanho da amostra) e de complexidade (modelo de área)
    V3  vazamento na validação cruzada de `validacao.py` (calibração e dobras por cliente)
    V4  rótulo embaralhado (área e padrão construtivo)
    V5  resíduos e viés por subgrupo
    V6  estabilidade dos limiares escolhidos olhando os dados (obra, conteúdo, eletrônicos, padrão)
    V7  distribuição de planos, confiança e perguntas: desenvolvimento contra teste

Saída: saidas/diagnostico_ajuste.csv. Não altera src/ nem as saídas existentes.
Reaproveita funções de scripts/08_avaliar_modelo.py.
"""

import importlib.util
import sys
import warnings
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402
from sklearn.ensemble import GradientBoostingRegressor  # noqa: E402

from casa_gemea import area, inferencias, pipeline, regras, validacao  # noqa: E402
from casa_gemea.calibracao import calibrar  # noqa: E402
from casa_gemea.carregar import ler_base, montar_tabela_imoveis  # noqa: E402
from casa_gemea.config import ENCODING, PASTA_SAIDAS  # noqa: E402
from casa_gemea.inferencias import construir_casa_gemea, inferir_tipo  # noqa: E402

warnings.filterwarnings("ignore")

# Funções do script 08 (o nome do arquivo começa com número, então não dá para importar direto).
_spec = importlib.util.spec_from_file_location("avaliar_modelo", RAIZ / "scripts" / "08_avaliar_modelo.py")
a08 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(a08)

SEMENTE = 42
N_DOBRAS = 5
SAIDA = PASTA_SAIDAS / "diagnostico_ajuste.csv"
LINHAS: list[dict] = []
BASE_NUM = a08.BASE_NUM
EXTRAS = ["log_agua", "quantidade_dependentes", "pet", "log_condominio", "tem_condominio",
          "log_financiamento", "log_aluguel", "log_compras", "log_bens"]


def registrar(verificacao: str, variante: str, **metricas) -> None:
    for nome, valor in metricas.items():
        LINHAS.append({"verificacao": verificacao, "variante": variante, "metrica": nome, "valor": round(float(valor), 4)})


def tabela_com_derivadas(nome: str) -> pd.DataFrame:
    """Mesmas colunas derivadas do script 08, para qualquer base."""
    t = inferir_tipo(montar_tabela_imoveis(ler_base(nome)))
    t["log_iptu"] = np.log(t["pagamento_iptu_anual"].clip(lower=1))
    t["log_energia"] = np.log(t["energia_media_mensal_6m"].clip(lower=1))
    t["log_agua"] = np.log(t["agua_media_mensal_6m"].clip(lower=1))
    t["log_condominio"] = np.log1p(t["pagamento_condominio_mensal"])
    t["log_compras"] = np.log1p(t["compras_moveis_36m"] + t["compras_eletrodomesticos_36m"] + t["compras_eletronicos_36m"])
    t["log_bens"] = np.log1p(t["bens_valor_cadastrado"])
    t["log_financiamento"] = np.log1p(t["parcela_financiamento_imobiliario"])
    t["log_aluguel"] = np.log1p(t["valor_aluguel_recorrente"])
    t["pet"] = (t["possui_pet_informado"] == "SIM").astype(float)
    t["eh_casa_f"] = t["eh_casa"].astype(float)
    t["tem_condominio"] = (t["pagamento_condominio_mensal"] > 0).astype(float)
    return t


def grupos_cliente(ids: pd.Series, repeticao: int = 0) -> np.ndarray:
    """Dobra de cada linha, sorteada por cliente (nunca separa os imóveis de um cliente)."""
    unicos = ids.unique()
    sorteio = np.random.default_rng(SEMENTE + repeticao).permutation(len(unicos))
    mapa = pd.Series(sorteio % N_DOBRAS, index=unicos)
    return ids.map(mapa).to_numpy()


def erro_pct_mediano(real: np.ndarray, log_prev: np.ndarray) -> float:
    return float(np.median(np.abs(real - np.exp(log_prev)) / real))


def r2_log(real: np.ndarray, log_prev: np.ndarray) -> float:
    res = np.log(real) - log_prev
    return float(1 - res.var() / np.log(real).var())


def ols(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    return np.linalg.lstsq(np.column_stack([np.ones(len(X)), X]), y, rcond=None)[0]


def ols_prever(coef: np.ndarray, X: np.ndarray) -> np.ndarray:
    return np.column_stack([np.ones(len(X)), X]) @ coef


def prever_oof_ols(t: pd.DataFrame, repeticao: int = 0) -> np.ndarray:
    """Previsão fora da amostra de log(área), OLS atual, dobras por cliente."""
    X = a08.matriz(t, BASE_NUM, ["municipio_real"]).to_numpy()
    y = np.log(t["area_cadastrada_m2"].to_numpy())
    d = grupos_cliente(t["cliente_id"], repeticao)
    prev = np.zeros(len(t))
    for k in range(N_DOBRAS):
        tr, te = d != k, d == k
        prev[te] = ols_prever(ols(X[tr], y[tr]), X[te])
    return prev


# ------------------------------------------------------------------------------ V1
def verificacao_1() -> None:
    print("\n== V1: teste cego e deriva ==")
    dev, te = tabela_com_derivadas("desenvolvimento"), tabela_com_derivadas("teste")
    modelo = area.treinar(dev)   # exatamente o modelo do pipeline: só desenvolvimento
    dev_a = dev[dev["area_cadastrada_m2"] > 0].reset_index(drop=True)
    te_a = te[te["area_cadastrada_m2"] > 0].reset_index(drop=True)
    registrar("V1", "n", dev_com_area=len(dev_a), teste_com_area=len(te_a))

    # Validação cruzada no desenvolvimento (por cliente) com a mesma faixa derivada dos resíduos.
    prev = prever_oof_ols(dev_a)
    real = dev_a["area_cadastrada_m2"].to_numpy()
    res = np.log(real) - prev
    r_min, r_max = np.quantile(res, area.QUANTIS_FAIXA)
    cv = {"erro_pct_mediano": erro_pct_mediano(real, prev), "r2_log": r2_log(real, prev),
          "cobertura_faixa_80": np.mean((res >= r_min) & (res <= r_max)), "vies_log_mediano": np.median(res)}
    registrar("V1", "desenvolvimento, validação cruzada por cliente", **cv)

    # Teste cego: modelo e faixa vindos só do desenvolvimento.
    p = modelo.prever(te_a)
    real_t = te_a["area_cadastrada_m2"].to_numpy()
    log_prev_t = np.log(p["area_estimada_m2"].to_numpy())
    res_t = np.log(real_t) - log_prev_t
    dentro = ((real_t >= p["area_estimada_min_m2"].to_numpy()) & (real_t <= p["area_estimada_max_m2"].to_numpy()))
    cego = {"erro_pct_mediano": erro_pct_mediano(real_t, log_prev_t), "r2_log": r2_log(real_t, log_prev_t),
            "cobertura_faixa_80": dentro.mean(), "vies_log_mediano": np.median(res_t)}
    registrar("V1", "teste cego (treino só no desenvolvimento)", **cego)

    rng = np.random.default_rng(SEMENTE)
    boot = {"erro": [], "cob": []}
    for _ in range(2000):
        i = rng.integers(0, len(real_t), len(real_t))
        boot["erro"].append(erro_pct_mediano(real_t[i], log_prev_t[i]))
        boot["cob"].append(dentro[i].mean())
    registrar("V1", "teste cego, IC 95% bootstrap", erro_inf=np.quantile(boot["erro"], .025), erro_sup=np.quantile(boot["erro"], .975),
              cobertura_inf=np.quantile(boot["cob"], .025), cobertura_sup=np.quantile(boot["cob"], .975))
    # Mesmo n no desenvolvimento: quão raro seria um erro tão alto só por azar da amostra pequena?
    n = len(real_t)
    sorteios = [erro_pct_mediano(real[i], prev[i]) for i in (rng.integers(0, len(real), n) for _ in range(2000))]
    registrar("V1", "desenvolvimento, subamostras de mesmo n do teste", erro_p5=np.quantile(sorteios, .05), erro_p95=np.quantile(sorteios, .95),
              p_valor_teste_cego_maior=np.mean(np.array(sorteios) >= cego["erro_pct_mediano"]))
    tt = stats.ttest_1samp(res_t, 0.0)
    registrar("V1", "teste cego, viés do resíduo em log (média diferente de zero?)", media=res_t.mean(), erro_padrao=res_t.std(ddof=1) / np.sqrt(len(res_t)),
              p_valor=tt.pvalue, desvio_residuo_teste=res_t.std(ddof=1), desvio_residuo_dev_cv=res.std(ddof=1))
    print("CV dev", cv, "\nteste cego", cego)

    # Calibração: padrão pelo IPTU/m² e faixa de aluguel/m² (interquartil) no teste, com mediana do desenvolvimento.
    calib = calibrar(dev)
    for rotulo, base in [("teste", te)]:
        sub = base[(base["area_cadastrada_m2"] > 0) & (base["padrao_construtivo_cadastrado"] != "NAO_DISPONIVEL")]
        razao = (sub["pagamento_iptu_anual"] / sub["area_cadastrada_m2"]) / sub["municipio_real"].map(calib.iptu_m2_mediana)
        pred = razao.map(inferencias.classificar_padrao_por_iptu)
        registrar("V1", f"padrão pela regra, {rotulo} (calibração do desenvolvimento)", n=len(sub),
                  **acuracia_padrao(sub["padrao_construtivo_cadastrado"].to_numpy(), pred.to_numpy()))
        inq = base[(base["pagamento_aluguel_recorrente"] == "SIM") & (base["area_cadastrada_m2"] > 0)]
        am2 = inq["valor_aluguel_recorrente"] / inq["area_cadastrada_m2"]
        lo, hi = inq["municipio_real"].map(calib.aluguel_m2_p25), inq["municipio_real"].map(calib.aluguel_m2_p75)
        registrar("V1", f"aluguel/m² dentro de p25 a p75 de dev, {rotulo}", n=len(inq), fracao_dentro=((am2 >= lo) & (am2 <= hi)).mean())
    # Mesmos números no desenvolvimento, calibração refeita fora da dobra (por cliente).
    d = grupos_cliente(dev["cliente_id"])
    pred_all, fracao_aluguel = [], []
    for k in range(N_DOBRAS):
        cal_k = calibrar(dev[d != k])
        av = dev[d == k]
        sub = av[(av["area_cadastrada_m2"] > 0) & (av["padrao_construtivo_cadastrado"] != "NAO_DISPONIVEL")]
        razao = (sub["pagamento_iptu_anual"] / sub["area_cadastrada_m2"]) / sub["municipio_real"].map(cal_k.iptu_m2_mediana)
        pred_all.append(pd.DataFrame({"real": sub["padrao_construtivo_cadastrado"], "pred": razao.map(inferencias.classificar_padrao_por_iptu)}))
        inq = av[(av["pagamento_aluguel_recorrente"] == "SIM") & (av["area_cadastrada_m2"] > 0)]
        am2 = inq["valor_aluguel_recorrente"] / inq["area_cadastrada_m2"]
        dentro_k = (am2 >= inq["municipio_real"].map(cal_k.aluguel_m2_p25)) & (am2 <= inq["municipio_real"].map(cal_k.aluguel_m2_p75))
        fracao_aluguel.append(dentro_k)
    pa = pd.concat(pred_all)
    registrar("V1", "padrão pela regra, desenvolvimento (calibração fora da dobra)", n=len(pa), **acuracia_padrao(pa["real"].to_numpy(), pa["pred"].to_numpy()))
    fa = pd.concat(fracao_aluguel)
    registrar("V1", "aluguel/m² dentro de p25 a p75, desenvolvimento (fora da dobra)", n=len(fa), fracao_dentro=fa.mean())

    # Deriva das entradas.
    for coluna, rotulo in [("log_iptu", "log IPTU"), ("log_energia", "log energia"), ("log_agua", "log água")]:
        ks = stats.ks_2samp(dev[coluna], te[coluna])
        registrar("V1", f"deriva {rotulo}", ks=ks.statistic, p_valor=ks.pvalue,
                  mediana_dev=dev[coluna].median(), mediana_teste=te[coluna].median())
    # Resíduo do modelo de área também com IPTU/energia em m² (mesmo n): razão IPTU por m² da base com área.
    z = stats.ttest_ind(np.log(dev_a["pagamento_iptu_anual"] / dev_a["area_cadastrada_m2"]),
                        np.log(te_a["pagamento_iptu_anual"] / te_a["area_cadastrada_m2"]), equal_var=False)
    registrar("V1", "deriva log IPTU por m² (só com área)", t=z.statistic, p_valor=z.pvalue)
    for coluna in ["eh_casa", "tipo_imovel", "municipio_real", "vinculo_proxy"]:
        if coluna == "vinculo_proxy":
            dev_c = np.select([dev["pagamento_aluguel_recorrente"] == "SIM", dev["parcela_financiamento_imobiliario"] > 0], ["INQ", "FIN"], "OUTRO")
            te_c = np.select([te["pagamento_aluguel_recorrente"] == "SIM", te["parcela_financiamento_imobiliario"] > 0], ["INQ", "FIN"], "OUTRO")
            dev_c, te_c = pd.Series(dev_c), pd.Series(te_c)
        else:
            dev_c, te_c = dev[coluna], te[coluna]
        tab = pd.concat([dev_c.value_counts().rename("dev"), te_c.value_counts().rename("teste")], axis=1).fillna(0)
        chi = stats.chi2_contingency(tab.to_numpy())
        registrar("V1", f"deriva {coluna}", qui2=chi[0], p_valor=chi[1], graus=chi[2])
    registrar("V1", "fração com área real", dev=(dev["area_cadastrada_m2"] > 0).mean(), teste=(te["area_cadastrada_m2"] > 0).mean())
    print("padrão/aluguel/deriva registrados")


def acuracia_padrao(y: np.ndarray, pred: np.ndarray) -> dict:
    classes = ["ECONOMICO", "NORMAL", "SUPERIOR"]
    recalls = [np.mean(pred[y == c] == c) for c in classes if (y == c).any()]
    return {"acuracia": np.mean(pred == y), "acuracia_balanceada": np.mean(recalls), "sempre_normal": np.mean(y == "NORMAL")}


# ------------------------------------------------------------------------------ V2
def montar_X(t: pd.DataFrame, modelo: str) -> np.ndarray:
    if modelo == "constante":
        return np.zeros((len(t), 0))
    if modelo == "OLS só IPTU":
        return t[["log_iptu"]].to_numpy()
    cats = ["municipio_real"]
    if modelo == "OLS atual":
        return a08.matriz(t, BASE_NUM, cats).to_numpy()
    X = a08.matriz(t, BASE_NUM + EXTRAS, cats)
    if modelo in ("OLS proposto", "GBM profundidade 3", "GBM profundidade 6"):
        return X.to_numpy()
    if modelo == "OLS com interações":
        X = X.copy()
        X["iptu2"], X["energia2"] = t["log_iptu"] ** 2, t["log_energia"] ** 2
        X["iptu_x_energia"], X["iptu_x_casa"], X["energia_x_casa"] = t["log_iptu"] * t["log_energia"], t["log_iptu"] * t["eh_casa_f"], t["log_energia"] * t["eh_casa_f"]
        for m in [c for c in X.columns if c.startswith("municipio_real_")]:
            X[f"iptu_x_{m}"] = t["log_iptu"] * X[m]
        return X.to_numpy()
    raise ValueError(modelo)


def ajustar_prever(modelo: str, X_tr, y_tr, X_te_lista):
    if modelo == "constante":
        return [np.full(len(X), y_tr.mean()) for X in X_te_lista]
    if modelo.startswith("GBM"):
        prof = 3 if "3" in modelo else 6
        m = GradientBoostingRegressor(n_estimators=250, max_depth=prof, learning_rate=0.04, subsample=0.8, random_state=SEMENTE).fit(X_tr, y_tr)
        return [m.predict(X) for X in X_te_lista]
    coef = ols(X_tr, y_tr)
    return [ols_prever(coef, X) for X in X_te_lista]


def verificacao_2() -> None:
    print("\n== V2: curvas de aprendizado e de complexidade ==")
    t = tabela_com_derivadas("desenvolvimento")
    t = t[t["area_cadastrada_m2"] > 0].reset_index(drop=True)
    y = np.log(t["area_cadastrada_m2"].to_numpy())
    real = t["area_cadastrada_m2"].to_numpy()
    modelos = ["constante", "OLS só IPTU", "OLS atual", "OLS proposto", "OLS com interações", "GBM profundidade 3", "GBM profundidade 6"]
    fracoes = [0.10, 0.25, 0.50, 0.75, 1.00]
    repeticoes = 3
    X = {m: montar_X(t, m) for m in modelos}
    acc = {}   # (modelo, fração) -> listas
    for rep in range(repeticoes):
        d = grupos_cliente(t["cliente_id"], rep)
        rng = np.random.default_rng(SEMENTE + 100 + rep)
        for k in range(N_DOBRAS):
            tr_total, te = np.where(d != k)[0], np.where(d == k)[0]
            ordem = rng.permutation(tr_total)
            for f in fracoes:
                tr = ordem[: max(int(round(f * len(tr_total))), 10)]
                for m in modelos:
                    p_tr, p_te = ajustar_prever(m, X[m][tr], y[tr], [X[m][tr], X[m][te]])
                    acc.setdefault((m, f), []).append((erro_pct_mediano(real[tr], p_tr), erro_pct_mediano(real[te], p_te),
                                                       np.sqrt(np.mean((y[tr] - p_tr) ** 2)), np.sqrt(np.mean((y[te] - p_te) ** 2))))
    for (m, f), v in acc.items():
        v = np.array(v).mean(axis=0)
        registrar("V2", f"{m}, amostra {f:.0%}", erro_treino=v[0], erro_validacao=v[1], rmse_log_treino=v[2], rmse_log_validacao=v[3],
                  n_treino=int(round(f * len(t) * (N_DOBRAS - 1) / N_DOBRAS)))
    for m in modelos:
        v = np.array(acc[(m, 1.0)]).mean(axis=0)
        v75 = np.array(acc[(m, 0.75)]).mean(axis=0)
        print(f"{m:22s} treino {v[0]:.3f}  validação {v[1]:.3f}  (75%: {v75[1]:.3f})")


# ------------------------------------------------------------------------------ V3
def validar_corrigido(por_cliente: bool, referencia_fora_da_dobra: bool, semente: int = SEMENTE) -> pd.DataFrame:
    """Réplica de `validacao.validar` com opções: dobras por cliente e referência calculada fora da dobra."""
    tabela = montar_tabela_imoveis(ler_base("desenvolvimento"))
    com_area = tabela.index[tabela["area_cadastrada_m2"] > 0]
    if por_cliente:
        dobra = pd.Series(grupos_cliente(tabela.loc[com_area, "cliente_id"]), index=com_area)
    else:
        dobra = pd.Series(np.random.default_rng(semente).integers(0, N_DOBRAS, len(com_area)), index=com_area)

    modelo_t, calib_t = area.treinar(inferir_tipo(tabela)), calibrar(tabela)
    real_global = validacao._faixas(construir_casa_gemea(tabela.loc[com_area], modelo_t, calib_t), regras.carregar_referencias(calib_t))

    pares = []
    for k in range(N_DOBRAS):
        avaliados = dobra.index[dobra == k]
        treino = tabela.copy()
        treino.loc[avaliados, "area_cadastrada_m2"] = 0
        modelo, calib = area.treinar(inferir_tipo(treino)), calibrar(treino)
        ref = regras.carregar_referencias(calib)
        oculto = tabela.loc[avaliados].copy()
        oculto["area_cadastrada_m2"] = 0
        oculto["padrao_construtivo_cadastrado"] = "NAO_DISPONIVEL"
        escondida = validacao._faixas(construir_casa_gemea(oculto, modelo, calib), ref)
        if referencia_fora_da_dobra:
            real = validacao._faixas(construir_casa_gemea(tabela.loc[avaliados], modelo, calib), ref)
        else:
            real = real_global[real_global["imovel_id"].isin(tabela.loc[avaliados, "imovel_id"])]
        pares.append(escondida.merge(real, on=["imovel_id", "cobertura"], suffixes=("", "_real")))
    m = pd.concat(pares)
    m["valor_real"] = np.sqrt(m["faixa_valor_min_real"] * m["faixa_valor_max_real"])
    m["contem"] = (m["faixa_valor_min"] <= m["valor_real"]) & (m["valor_real"] <= m["faixa_valor_max"])
    m["erro_centro"] = np.sqrt(m["faixa_valor_min"] * m["faixa_valor_max"]) / m["valor_real"] - 1
    return m


def verificacao_3() -> None:
    print("\n== V3: vazamento na validação cruzada ==")
    variantes = {
        "A original (dobras por imóvel, referência global)": dict(por_cliente=False, referencia_fora_da_dobra=False),
        "B dobras por cliente": dict(por_cliente=True, referencia_fora_da_dobra=False),
        "C dobras por cliente + referência fora da dobra": dict(por_cliente=True, referencia_fora_da_dobra=True),
    }
    for nome, opcoes in variantes.items():
        m = validar_corrigido(**opcoes)
        registrar("V3", nome, imoveis=m["imovel_id"].nunique(), faixa_contem=m["contem"].mean(),
                  erro_mediano_centro=m["erro_centro"].abs().median(),
                  contem_incendio=m.loc[m["cobertura"] == "INCENDIO_RAIO_EXPLOSAO_FUMACA", "contem"].mean())
        print(f"{nome}: contém {m['contem'].mean():.3f}, erro mediano {m['erro_centro'].abs().median():.3f}")

    # Modelo de área: dobras por imóvel (como em area.treinar) contra por cliente.
    t = tabela_com_derivadas("desenvolvimento")
    t = t[t["area_cadastrada_m2"] > 0].reset_index(drop=True)
    real = t["area_cadastrada_m2"].to_numpy()
    modelo = area.treinar(inferir_tipo(montar_tabela_imoveis(ler_base("desenvolvimento"))))
    registrar("V3", "área: dobras por imóvel (area.treinar)", erro_pct_mediano=modelo.metricas["erro_percentual_mediano"],
              r2_log=modelo.metricas["r2_log"], cobertura_faixa_80=modelo.metricas["cobertura_faixa_80"])
    prev = prever_oof_ols(t)
    registrar("V3", "área: dobras por cliente", erro_pct_mediano=erro_pct_mediano(real, prev), r2_log=r2_log(real, prev))
    # Contagem de clientes com 2 imóveis com área real (risco de vazamento por imóvel).
    por_cliente = t.groupby("cliente_id").size()
    registrar("V3", "clientes com 2 imóveis com área real", clientes=(por_cliente == 2).sum(), imoveis_nesses_clientes=int(por_cliente[por_cliente == 2].sum()))


# ------------------------------------------------------------------------------ V4
def verificacao_4() -> None:
    print("\n== V4: rótulo embaralhado ==")
    t = tabela_com_derivadas("desenvolvimento")
    a = t[t["area_cadastrada_m2"] > 0].reset_index(drop=True)
    real = a["area_cadastrada_m2"].to_numpy()
    prev = prever_oof_ols(a)
    registrar("V4", "área real (referência)", erro_pct_mediano=erro_pct_mediano(real, prev), r2_log=r2_log(real, prev))
    X = a08.matriz(a, BASE_NUM, ["municipio_real"]).to_numpy()
    d = grupos_cliente(a["cliente_id"])
    rng = np.random.default_rng(SEMENTE)
    for rotulo, dentro_cidade in [("embaralhada no desenvolvimento todo", False), ("embaralhada dentro do município", True)]:
        erros, r2s = [], []
        for _ in range(30):
            if dentro_cidade:
                y_emb = np.log(real).copy()
                for m, idx in a.groupby("municipio_real").indices.items():
                    y_emb[idx] = y_emb[rng.permutation(idx)]
            else:
                y_emb = np.log(real)[rng.permutation(len(real))]
            p = np.zeros(len(a))
            for k in range(N_DOBRAS):
                tr, te = d != k, d == k
                p[te] = ols_prever(ols(X[tr], y_emb[tr]), X[te])
            erros.append(np.median(np.abs(np.exp(y_emb) - np.exp(p)) / np.exp(y_emb)))
            r2s.append(1 - (y_emb - p).var() / y_emb.var())
        registrar("V4", f"área {rotulo}, 30 sorteios", erro_pct_mediano=np.mean(erros), erro_pct_p5=np.quantile(erros, .05),
                  r2_log_medio=np.mean(r2s), r2_log_p95=np.quantile(r2s, .95))
        print(f"área {rotulo}: erro {np.mean(erros):.3f}, R² {np.mean(r2s):.3f}")

    # Padrão construtivo: regra com calibração fora da dobra; rótulo permutado.
    p_df = padrao_oof(t)
    y = p_df["real"].to_numpy()
    obs = acuracia_padrao(y, p_df["pred"].to_numpy())
    registrar("V4", "padrão: regra com rótulo real", n=len(p_df), **obs)
    nulo = [acuracia_padrao(rng.permutation(y), p_df["pred"].to_numpy())["acuracia_balanceada"] for _ in range(2000)]
    registrar("V4", "padrão: rótulo embaralhado, 2000 sorteios", bal_media=np.mean(nulo), bal_p95=np.quantile(nulo, .95),
              p_valor=np.mean(np.array(nulo) >= obs["acuracia_balanceada"]))
    print("padrão real", obs, "nulo p95", np.quantile(nulo, .95))

    # Limiares do padrão (1,25 e 0,85) foram escolhidos olhando a base: quanto otimismo isso gera?
    razao = p_df["razao"].to_numpy()
    clientes = p_df["cliente_id"].to_numpy()
    grade_hi, grade_lo = np.arange(1.05, 1.61, 0.05), np.arange(0.60, 1.01, 0.05)

    def bal(yv, r, hi, lo):
        pred = np.where(r >= hi, "SUPERIOR", np.where(r <= lo, "ECONOMICO", "NORMAL"))
        return acuracia_padrao(yv, pred)["acuracia_balanceada"]

    def melhor(yv, r):
        return max(((bal(yv, r, h, l), h, l) for h in grade_hi for l in grade_lo), key=lambda x: x[0])

    unicos = np.unique(clientes)
    for rotulo, embaralhar in [("rótulo real", False), ("rótulo embaralhado", True)]:
        dentro, fora, fixos, his, los = [], [], [], [], []
        for s in range(40):
            r_ = np.random.default_rng(SEMENTE + s)
            metade = set(r_.choice(unicos, len(unicos) // 2, replace=False))
            em_a = np.array([c in metade for c in clientes])
            yy = r_.permutation(y) if embaralhar else y
            ba, h, l = melhor(yy[em_a], razao[em_a])
            dentro.append(ba)
            fora.append(bal(yy[~em_a], razao[~em_a], h, l))
            fixos.append(bal(yy[~em_a], razao[~em_a], 1.25, 0.85))
            his.append(h); los.append(l)
        registrar("V4", f"padrão: limiares reestimados em metade, {rotulo}, 40 divisões", acur_bal_na_metade_de_treino=np.mean(dentro),
                  acur_bal_na_outra_metade=np.mean(fora), acur_bal_limiares_atuais_na_outra_metade=np.mean(fixos),
                  limiar_superior_medio=np.mean(his), limiar_superior_dp=np.std(his), limiar_economico_medio=np.mean(los), limiar_economico_dp=np.std(los))
        print(f"limiares {rotulo}: treino {np.mean(dentro):.3f} outra metade {np.mean(fora):.3f} atuais {np.mean(fixos):.3f} "
              f"hi {np.mean(his):.2f}±{np.std(his):.2f} lo {np.mean(los):.2f}±{np.std(los):.2f}")


def padrao_oof(t: pd.DataFrame) -> pd.DataFrame:
    """Razão IPTU/m² contra a mediana da cidade, com a mediana calculada fora da dobra (por cliente)."""
    d = grupos_cliente(t["cliente_id"])
    saida = []
    for k in range(N_DOBRAS):
        cal = calibrar(t[d != k])
        av = t[d == k]
        sub = av[(av["area_cadastrada_m2"] > 0) & (av["padrao_construtivo_cadastrado"] != "NAO_DISPONIVEL")]
        razao = (sub["pagamento_iptu_anual"] / sub["area_cadastrada_m2"]) / sub["municipio_real"].map(cal.iptu_m2_mediana)
        saida.append(pd.DataFrame({"cliente_id": sub["cliente_id"], "real": sub["padrao_construtivo_cadastrado"], "razao": razao,
                                   "pred": razao.map(inferencias.classificar_padrao_por_iptu)}))
    return pd.concat(saida).reset_index(drop=True)


# ------------------------------------------------------------------------------ V5
def verificacao_5() -> None:
    print("\n== V5: resíduos e viés ==")
    t = tabela_com_derivadas("desenvolvimento")
    t = t[t["area_cadastrada_m2"] > 0].reset_index(drop=True)
    real = t["area_cadastrada_m2"].to_numpy()
    prev = prever_oof_ols(t)
    res = np.log(real) - prev           # positivo = modelo subestima
    r_min, r_max = np.quantile(res, area.QUANTIS_FAIXA)
    dentro = (res >= r_min) & (res <= r_max)
    ep = np.abs(real - np.exp(prev)) / real

    t["res"], t["ep"], t["dentro"] = res, ep, dentro
    # Faixas pela área PREVISTA: agrupar pela área real criaria viés artificial (regressão à média).
    t["faixa_area"] = pd.qcut(prev, 4, labels=["Q1 menor", "Q2", "Q3", "Q4 maior"])
    t["faixa_area_real"] = pd.qcut(real, 4, labels=["Q1 menor", "Q2", "Q3", "Q4 maior"])
    t["faixa_iptu"] = pd.qcut(t["pagamento_iptu_anual"], 4, labels=["Q1 menor", "Q2", "Q3", "Q4 maior"])
    sinais = []
    for coluna in ["municipio_real", "tipo_imovel", "faixa_area", "faixa_iptu", "faixa_area_real"]:
        for grupo, g in t.groupby(coluna, observed=True):
            vies = g["res"].mean()
            ep_vies = g["res"].std() / np.sqrt(len(g))
            registrar("V5", f"{coluna} = {grupo}", n=len(g), vies_log_medio=vies, vies_em_erros_padrao=vies / ep_vies if ep_vies else 0,
                      erro_pct_mediano=g["ep"].median(), cobertura_faixa_80=g["dentro"].mean())
            if abs(vies / ep_vies) > 2.5 and len(g) >= 20:
                sinais.append((coluna, grupo, len(g), vies))
    print("subgrupos com viés > 2,5 erros-padrão:", sinais)
    rho = stats.spearmanr(prev, np.abs(res))
    aux = ols(prev.reshape(-1, 1), res ** 2)
    ajuste = ols_prever(aux, prev.reshape(-1, 1))
    r2_bp = 1 - ((res ** 2 - ajuste) ** 2).sum() / ((res ** 2 - (res ** 2).mean()) ** 2).sum()
    bp = len(res) * r2_bp
    registrar("V5", "heterocedasticidade", spearman_prev_vs_abs_residuo=rho.statistic, p_valor_spearman=rho.pvalue,
              estatistica_bp=bp, p_valor_bp=stats.chi2.sf(bp, 1))
    # Os 10 piores (só agregados).
    piores = t.nlargest(10, "ep")
    registrar("V5", "10 piores casos", erro_pct_medio=piores["ep"].mean(), erro_pct_minimo=piores["ep"].min(),
              fracao_subestimados=(piores["res"] > 0).mean(), fracao_casas=piores["eh_casa"].mean(),
              fracao_com_area_acima_p90=(piores["area_cadastrada_m2"] > np.quantile(real, .9)).mean(),
              fracao_apartamento_sem_condominio=((piores["tipo_imovel"] == "APARTAMENTO") & (piores["pagamento_condominio_mensal"] == 0)).mean())
    registrar("V5", "10 piores casos, municípios distintos", n=piores["municipio_real"].nunique())
    registrar("V5", "cauda", p95_erro_pct=np.quantile(ep, .95), p99_erro_pct=np.quantile(ep, .99), max_erro_pct=ep.max())
    print("heterocedasticidade", rho.statistic, "BP p", stats.chi2.sf(bp, 1))


# ------------------------------------------------------------------------------ V6
def verificacao_6(res: pipeline.Resultado) -> None:
    print("\n== V6: estabilidade dos limiares ==")
    casas = {n: c.copy() for n, c in res.casas.items()}
    for c in casas.values():
        c["fracao_conteudo_do_cliente"] = c.apply(lambda r: regras.interesse_seguravel(r)[2], axis=1)
        c["conteudo_cliente"] = c["conteudo_estimado"] * c["fracao_conteudo_do_cliente"]
        c["eletro_cliente"] = c["eletronicos_eletro_max"] * c["fracao_conteudo_do_cliente"]
    dev, te = casas["desenvolvimento"], casas["teste"]

    # (a) A que percentil cada limiar corresponde, em desenvolvimento, nas metades e no teste.
    limiares = {
        "obra 10 mil (entre quem gastou)": ("gastos_material_construcao_24m", 10_000, True),
        "obra 30 mil (entre quem gastou)": ("gastos_material_construcao_24m", 30_000, True),
        "conteúdo moderado 10 mil": ("conteudo_cliente", 10_000, False),
        "conteúdo relevante 20 mil": ("conteudo_cliente", 20_000, False),
        "eletrônicos 15 mil": ("eletro_cliente", 15_000, False),
    }
    unicos = dev["cliente_id"].unique()
    rng = np.random.default_rng(SEMENTE)
    metades = []
    for _ in range(200):
        a = set(rng.choice(unicos, len(unicos) // 2, replace=False))
        metades.append(dev["cliente_id"].isin(a).to_numpy())

    nivel = {}
    for nome, (col, lim, so_positivos) in limiares.items():
        def pct(df):
            v = df[col][df[col] > 0] if so_positivos else df[col]
            return float((v < lim).mean())
        p_dev = pct(dev)
        p_metades = [pct(dev[m]) for m in metades]
        p_teste = pct(te)
        nivel[nome] = p_dev
        # Teste de proporção dev contra teste (acima do limiar).
        v_dev = dev[col][dev[col] > 0] if so_positivos else dev[col]
        v_te = te[col][te[col] > 0] if so_positivos else te[col]
        acima = np.array([(v_dev >= lim).sum(), (v_te >= lim).sum()])
        n = np.array([len(v_dev), len(v_te)])
        p_pool = acima.sum() / n.sum()
        z = (acima[0] / n[0] - acima[1] / n[1]) / np.sqrt(p_pool * (1 - p_pool) * (1 / n[0] + 1 / n[1]))
        registrar("V6", nome, percentil_no_desenvolvimento=p_dev, percentil_metades_p5=np.quantile(p_metades, .05),
                  percentil_metades_p95=np.quantile(p_metades, .95), percentil_no_teste=p_teste,
                  fracao_acima_dev=acima[0] / n[0], fracao_acima_teste=acima[1] / n[1], p_valor_proporcoes=2 * stats.norm.sf(abs(z)))
        print(f"{nome}: percentil dev {p_dev:.3f}, metades {np.quantile(p_metades, .05):.3f}..{np.quantile(p_metades, .95):.3f}, teste {p_teste:.3f}")

    # (b) Reestimar os limiares (mesmo percentil) numa metade e aplicar na outra: quanto muda o plano e a bandeira de obra?
    linhas_dev = [r for _, r in dev.iterrows()]
    linhas_te = [r for _, r in te.iterrows()]
    atual_const = (regras.CONTEUDO_RELEVANTE, regras.CONTEUDO_MODERADO, regras.ELETRO_RELEVANTE)
    atual_obra = (inferencias.OBRA_REFORMA_MODERADA, inferencias.OBRA_POSSIVEL_RELEVANTE)

    def planos(linhas, c_rel, c_mod, e_rel):
        regras.CONTEUDO_RELEVANTE, regras.CONTEUDO_MODERADO, regras.ELETRO_RELEVANTE = c_rel, c_mod, e_rel
        try:
            return np.array([regras.pontuar_plano(r)["plano_recomendado"] for r in linhas])
        finally:
            regras.CONTEUDO_RELEVANTE, regras.CONTEUDO_MODERADO, regras.ELETRO_RELEVANTE = atual_const

    def obra_a_confirmar(linhas, moderada, relevante):
        inferencias.OBRA_REFORMA_MODERADA, inferencias.OBRA_POSSIVEL_RELEVANTE = moderada, relevante
        try:
            return np.array([inferencias._regra_obra(r)[1] == "A_CONFIRMAR" for r in linhas])
        finally:
            inferencias.OBRA_REFORMA_MODERADA, inferencias.OBRA_POSSIVEL_RELEVANTE = atual_obra

    plano_atual_dev = planos(linhas_dev, *atual_const)
    obra_atual_dev = obra_a_confirmar(linhas_dev, *atual_obra)

    def quantil(df, col, p, so_positivos=False):
        v = df[col][df[col] > 0] if so_positivos else df[col]
        return float(np.quantile(v, p))

    mud_plano, mud_obra, mud_plano_conteudo = [], [], []
    for m in metades[:60]:
        a, b = dev[m], dev[~m]
        idx_b = np.where(~m)[0]
        c_rel = quantil(a, "conteudo_cliente", nivel["conteúdo relevante 20 mil"])
        c_mod = quantil(a, "conteudo_cliente", nivel["conteúdo moderado 10 mil"])
        e_rel = quantil(a, "eletro_cliente", nivel["eletrônicos 15 mil"])
        novo = planos([linhas_dev[i] for i in idx_b], c_rel, c_mod, e_rel)
        mud_plano.append(np.mean(novo != plano_atual_dev[idx_b]))
        o_mod = quantil(a, "gastos_material_construcao_24m", nivel["obra 10 mil (entre quem gastou)"], True)
        o_rel = quantil(a, "gastos_material_construcao_24m", nivel["obra 30 mil (entre quem gastou)"], True)
        nova_obra = obra_a_confirmar([linhas_dev[i] for i in idx_b], o_mod, o_rel)
        mud_obra.append(np.mean(nova_obra != obra_atual_dev[idx_b]))
    registrar("V6", "limiares reestimados em metade, aplicados na outra (60 divisões)", planos_que_mudam_medio=np.mean(mud_plano),
              planos_que_mudam_p95=np.quantile(mud_plano, .95), obra_a_confirmar_que_muda_medio=np.mean(mud_obra),
              obra_a_confirmar_que_muda_p95=np.quantile(mud_obra, .95))
    print(f"planos que mudam {np.mean(mud_plano):.3%} (p95 {np.quantile(mud_plano, .95):.3%}); obra {np.mean(mud_obra):.3%}")

    # (c) Reestimar no teste (mesmo percentil) e aplicar no teste: quanto muda o plano?
    plano_atual_te = planos(linhas_te, *atual_const)
    c_rel = quantil(te, "conteudo_cliente", nivel["conteúdo relevante 20 mil"])
    c_mod = quantil(te, "conteudo_cliente", nivel["conteúdo moderado 10 mil"])
    e_rel = quantil(te, "eletro_cliente", nivel["eletrônicos 15 mil"])
    novo = planos(linhas_te, c_rel, c_mod, e_rel)
    o_mod = quantil(te, "gastos_material_construcao_24m", nivel["obra 10 mil (entre quem gastou)"], True)
    o_rel = quantil(te, "gastos_material_construcao_24m", nivel["obra 30 mil (entre quem gastou)"], True)
    nova_obra = obra_a_confirmar(linhas_te, o_mod, o_rel)
    registrar("V6", "limiares reestimados no próprio teste (mesmo percentil)", limiar_conteudo_relevante=c_rel, limiar_conteudo_moderado=c_mod,
              limiar_eletronicos=e_rel, limiar_obra_moderada=o_mod, limiar_obra_relevante=o_rel,
              planos_que_mudam=np.mean(novo != plano_atual_te), obra_a_confirmar_que_muda=np.mean(nova_obra != obra_a_confirmar(linhas_te, *atual_obra)))
    print("teste: planos que mudam", np.mean(novo != plano_atual_te), "limiares", c_rel, c_mod, e_rel, o_mod, o_rel)

    # (d) Sensibilidade: limiares ±20% (já medida no projeto) em desenvolvimento, para comparar.
    for fator in (0.8, 1.2):
        novo = planos(linhas_dev, atual_const[0] * fator, atual_const[1] * fator, atual_const[2] * fator)
        registrar("V6", f"limiares de conteúdo e eletrônicos x{fator}, desenvolvimento", planos_que_mudam=np.mean(novo != plano_atual_dev))


# ------------------------------------------------------------------------------ V7
def verificacao_7(res: pipeline.Resultado) -> None:
    print("\n== V7: desenvolvimento contra teste ==")
    dev, te = res.recomendacoes["desenvolvimento"], res.recomendacoes["teste"]
    dev = dev.assign(perguntas=dev["qtd_perguntas"].clip(upper=3).astype(str).replace({"3": "3+"}))
    te = te.assign(perguntas=te["qtd_perguntas"].clip(upper=3).astype(str).replace({"3": "3+"}))
    for coluna in ["plano_recomendado", "confianca_geral", "semaforo", "perguntas", "elegivel", "canal_sugerido"]:
        tab = pd.concat([dev[coluna].value_counts().rename("dev"), te[coluna].value_counts().rename("teste")], axis=1).fillna(0)
        chi = stats.chi2_contingency(tab.to_numpy())
        pequenas = int((chi[3] < 5).sum())
        registrar("V7", f"{coluna}: qui-quadrado", qui2=chi[0], p_valor=chi[1], graus=chi[2], celulas_esperadas_menor_5=pequenas)
        for classe, linha in tab.iterrows():
            n = np.array([len(dev), len(te)])
            p = linha.to_numpy() / n
            registrar("V7", f"{coluna} = {classe}", dev=p[0], teste=p[1], diferenca_pp=100 * (p[1] - p[0]))
    registrar("V7", "perguntas: média", dev=dev["qtd_perguntas"].mean(), teste=te["qtd_perguntas"].mean(),
              p_valor_mann_whitney=stats.mannwhitneyu(dev["qtd_perguntas"], te["qtd_perguntas"]).pvalue)
    print("ok")


# ---------------------------------------------------------------------------- main
if __name__ == "__main__":
    escolhidos = {a.upper() for a in sys.argv[1:]} or {f"V{i}" for i in range(1, 8)}
    resultado = pipeline.executar() if escolhidos & {"V6", "V7"} else None
    rodadas = {"V1": verificacao_1, "V2": verificacao_2, "V3": verificacao_3, "V4": verificacao_4, "V5": verificacao_5,
               "V6": lambda: verificacao_6(resultado), "V7": lambda: verificacao_7(resultado)}
    for nome, funcao in rodadas.items():
        if nome in escolhidos:
            funcao()
    antigo = pd.read_csv(SAIDA, encoding=ENCODING) if SAIDA.exists() else pd.DataFrame()
    novo = pd.DataFrame(LINHAS)
    if len(antigo):
        antigo = antigo[~antigo["verificacao"].isin(novo["verificacao"].unique())]
    pd.concat([antigo, novo]).to_csv(SAIDA, index=False, encoding=ENCODING)
    print(f"\nMétricas gravadas em {SAIDA.relative_to(RAIZ)}")
