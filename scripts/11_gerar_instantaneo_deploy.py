"""Gera o instantâneo que permite ao motor rodar na hospedagem SEM as bases originais.

Guarda só a Casa Gêmea da base de teste (138 imóveis), a calibração por município e o catálogo
de coberturas. Saem dele idade, renda e o endereço completo: o motor não usa nenhum deles.

    python scripts/11_gerar_instantaneo_deploy.py
"""

import pickle
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from casa_gemea.motor import Motor  # noqa: E402

DESTINO = RAIZ / "dados_deploy" / "instantaneo_teste.pkl"

# Fora do instantâneo: guardrails do guia (CAMPOS_PROIBIDOS) e localização fina do imóvel.
REMOVER = ["idade", "renda_mensal", "origem_renda", "confianca_renda",
           "logradouro", "numero", "complemento", "bairro", "cep_agregado",
           "latitude_aproximada", "longitude_aproximada", "territorio_id"]


def main() -> None:
    motor = Motor()
    cal = motor.referencias.calibracao
    pacote = {
        "casas": motor.casas.drop(columns=REMOVER),
        "calibracao": {"iptu_m2_mediana": cal.iptu_m2_mediana, "aluguel_m2_p25": cal.aluguel_m2_p25,
                       "aluguel_m2_p75": cal.aluguel_m2_p75},
        "catalogo": motor.catalogo[["plano", "cobertura_fixa"]],
    }
    DESTINO.parent.mkdir(exist_ok=True)
    with DESTINO.open("wb") as f:
        pickle.dump(pacote, f, protocol=4)
    print(f"{DESTINO.relative_to(RAIZ)}: {len(pacote['casas'])} imóveis, {pacote['casas'].shape[1]} colunas, {DESTINO.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
