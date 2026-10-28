"""Pipeline completo: dados → Casa Gêmea → recomendação. Usado por todos os scripts.

Tudo o que é calibrado (modelo de área, IPTU e aluguel por m²) usa só a base de
desenvolvimento e é reaplicado igual na base de teste.
"""

from dataclasses import dataclass

import pandas as pd

from . import area
from .calibracao import Calibracao, calibrar
from .carregar import ler_base, montar_tabela_imoveis
from .inferencias import construir_casa_gemea, inferir_tipo
from .recomendacao import recomendar
from .regras import Referencias, carregar_referencias

NOMES_BASES = ("desenvolvimento", "teste")


@dataclass
class Resultado:
    modelo_area: area.ModeloArea
    calibracao: Calibracao
    referencias: Referencias
    bases: dict[str, dict[str, pd.DataFrame]]   # tabelas originais
    casas: dict[str, pd.DataFrame]              # Casa Gêmea completa (todas as colunas)
    recomendacoes: dict[str, pd.DataFrame]      # uma linha por imóvel
    coberturas: dict[str, pd.DataFrame]         # uma linha por cobertura


def executar(com_regras: bool = True) -> Resultado:
    bases = {nome: ler_base(nome) for nome in NOMES_BASES}
    tabelas = {nome: montar_tabela_imoveis(base) for nome, base in bases.items()}

    # O tipo do imóvel entra no modelo de área, então é inferido antes do treino.
    modelo = area.treinar(inferir_tipo(tabelas["desenvolvimento"]))
    calibracao = calibrar(tabelas["desenvolvimento"])
    referencias = carregar_referencias(calibracao)

    casas = {nome: construir_casa_gemea(t, modelo, calibracao) for nome, t in tabelas.items()}
    recomendacoes, coberturas = {}, {}
    if com_regras:
        for nome, casa in casas.items():
            catalogo = bases[nome]["catalogo_coberturas_fixas_planos"]
            recomendacoes[nome], coberturas[nome] = recomendar(casa, referencias, catalogo)
    return Resultado(modelo, calibracao, referencias, bases, casas, recomendacoes, coberturas)
