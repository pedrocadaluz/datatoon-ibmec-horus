"""Estimativa da área do imóvel quando ela não está cadastrada (61% dos casos).

Modelo log-linear treinado nos imóveis com área real:

    log(área) = b0 + b1·log(IPTU anual) + b2·log(energia mensal) + b3·[é casa] + município

Por que essas variáveis (medido na base de desenvolvimento):
- IPTU e energia têm correlação ~0,8 com a área;
- casas têm, em média, o dobro da área de apartamentos;
- o IPTU por m² varia por cidade (ex.: ~18 R$/m² em São Paulo e ~10 R$/m² em Fortaleza).
Condomínio, renda e padrão construtivo não mostraram relação com a área e ficaram de fora.

A faixa (mín/máx) usa os resíduos da validação cruzada: é um intervalo de 80%.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

QUANTIS_FAIXA = (0.10, 0.90)
# Fora deste intervalo (95%), a área cadastrada diverge dos sinais e vira pergunta.
QUANTIS_DIVERGENCIA = (0.025, 0.975)


def _matriz(df: pd.DataFrame, municipios: list[str]) -> np.ndarray:
    colunas = [
        np.ones(len(df)),
        np.log(df["pagamento_iptu_anual"].clip(lower=1)),
        np.log(df["energia_media_mensal_6m"].clip(lower=1)),
        df["eh_casa"].astype(float),
    ]
    # Município de referência = o primeiro da lista (efeito embutido no intercepto).
    colunas += [(df["municipio_real"] == m).astype(float) for m in municipios[1:]]
    return np.column_stack(colunas)


@dataclass
class ModeloArea:
    coeficientes: np.ndarray
    municipios: list[str]
    residuo_min: float
    residuo_max: float
    residuo_divergencia: tuple[float, float]
    metricas: dict

    def prever(self, df: pd.DataFrame) -> pd.DataFrame:
        """Retorna área estimada (central, mín e máx) em m² e o resíduo da área cadastrada."""
        log_area = _matriz(df, self.municipios) @ self.coeficientes
        cadastrada = df["area_cadastrada_m2"].where(df["area_cadastrada_m2"] > 0)
        residuo = np.log(cadastrada) - log_area
        lo, hi = self.residuo_divergencia
        return pd.DataFrame(
            {
                "area_estimada_m2": np.exp(log_area).round(),
                "area_estimada_min_m2": np.exp(log_area + self.residuo_min).round(),
                "area_estimada_max_m2": np.exp(log_area + self.residuo_max).round(),
                "sinal_area_divergente": (residuo < lo) | (residuo > hi),
            },
            index=df.index,
        )


def _ajustar(df: pd.DataFrame, municipios: list[str]) -> np.ndarray:
    X = _matriz(df, municipios)
    y = np.log(df["area_cadastrada_m2"])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return coef


def treinar(df: pd.DataFrame, n_folds: int = 5, semente: int = 42) -> ModeloArea:
    """Treina nos imóveis com área real e mede o erro com validação cruzada."""
    treino = df[df["area_cadastrada_m2"] > 0].copy()
    municipios = sorted(df["municipio_real"].unique())

    rng = np.random.default_rng(semente)
    dobra = rng.integers(0, n_folds, len(treino))
    previsto = np.zeros(len(treino))
    for k in range(n_folds):
        coef = _ajustar(treino[dobra != k], municipios)
        previsto[dobra == k] = _matriz(treino[dobra == k], municipios) @ coef

    real = treino["area_cadastrada_m2"].to_numpy()
    residuos = np.log(real) - previsto
    r_min, r_max = np.quantile(residuos, QUANTIS_FAIXA)
    area_prevista = np.exp(previsto)
    dentro = (real >= area_prevista * np.exp(r_min)) & (real <= area_prevista * np.exp(r_max))

    metricas = {
        "imoveis_treino": int(len(treino)),
        "erro_medio_absoluto_m2": float(np.mean(np.abs(real - area_prevista))),
        "erro_percentual_mediano": float(np.median(np.abs(real - area_prevista) / real)),
        "r2_log": float(1 - residuos.var() / np.log(real).var()),
        "cobertura_faixa_80": float(dentro.mean()),
        "largura_relativa_faixa": f"-{1 - np.exp(r_min):.0%} / +{np.exp(r_max) - 1:.0%}",
    }
    divergencia = tuple(np.quantile(residuos, QUANTIS_DIVERGENCIA))
    return ModeloArea(_ajustar(treino, municipios), municipios, r_min, r_max, divergencia, metricas)
