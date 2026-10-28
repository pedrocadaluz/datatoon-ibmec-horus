"""Parâmetros de mercado calibrados na base de desenvolvimento e reaplicados na de teste.

- IPTU por m² mediano por município: referência para estimar o padrão construtivo.
- Aluguel por m² (quartis 25% e 75%) por município: referência para o aluguel de uma
  moradia temporária quando o cliente é proprietário e mora no imóvel.

Calibrar só na base de desenvolvimento evita usar a base de teste para definir regras.
"""

from dataclasses import dataclass

import pandas as pd


@dataclass
class Calibracao:
    iptu_m2_mediana: dict[str, float]
    aluguel_m2_p25: dict[str, float]
    aluguel_m2_p75: dict[str, float]

    def tabela(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "iptu_anual_por_m2_mediana": self.iptu_m2_mediana,
                "aluguel_mensal_por_m2_p25": self.aluguel_m2_p25,
                "aluguel_mensal_por_m2_p75": self.aluguel_m2_p75,
            }
        ).round(2).rename_axis("municipio").reset_index()


def calibrar(tabela_dev: pd.DataFrame) -> Calibracao:
    """Usa só dados observados: área cadastrada e aluguel efetivamente pago."""
    com_area = tabela_dev[tabela_dev["area_cadastrada_m2"] > 0]
    iptu_m2 = (com_area["pagamento_iptu_anual"] / com_area["area_cadastrada_m2"]).groupby(
        com_area["municipio_real"]
    ).median()

    inquilinos = com_area[com_area["pagamento_aluguel_recorrente"] == "SIM"]
    aluguel_m2 = (inquilinos["valor_aluguel_recorrente"] / inquilinos["area_cadastrada_m2"]).groupby(
        inquilinos["municipio_real"]
    )
    return Calibracao(
        iptu_m2_mediana=iptu_m2.to_dict(),
        aluguel_m2_p25=aluguel_m2.quantile(0.25).to_dict(),
        aluguel_m2_p75=aluguel_m2.quantile(0.75).to_dict(),
    )
