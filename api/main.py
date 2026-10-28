"""API fina: valida o transporte e delega todas as decisões ao motor existente."""

import math
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt, StrictStr, field_validator
from .rede import ips_locais, origens_locais

RAIZ = Path(__file__).resolve().parents[1]
MAX_NUMERO_JSON = 9_007_199_254_740_991  # Precisão inteira segura do navegador (2**53 - 1).
sys.path.insert(0, str(RAIZ / "src"))

from casa_gemea.motor import RESPOSTAS_ADICIONAIS, Motor, VERSAO_CONTRATO  # noqa: E402
from casa_gemea.perguntas import OPCOES  # noqa: E402
from casa_gemea.config import BASES  # noqa: E402

# O motor implementa o ramo NAO_SEI, mas omite o código em algumas listas.
# Completa apenas as opções de transporte para cumprir o contrato documentado.
# O ramo original preserva selo, confiança e faixa; não confirma o dado.
for _opcoes in OPCOES.values():
    if not any(codigo == "NAO_SEI" for codigo, _ in _opcoes):
        _opcoes.append(("NAO_SEI", "Não sei"))


class Entrada(BaseModel):
    model_config = ConfigDict(extra="forbid")
    versao_contrato: Literal["1.0"] = VERSAO_CONTRATO
    imovel_id: str = Field(min_length=1, max_length=80)
    respostas: dict[str, StrictStr | StrictInt | StrictFloat] = Field(default_factory=dict, max_length=12)

    @field_validator("respostas")
    @classmethod
    def respostas_validas(cls, respostas):
        for campo, valor in respostas.items():
            if campo in RESPOSTAS_ADICIONAIS:  # perguntas dos adicionais: SIM, NAO ou NAO_SEI
                if valor not in RESPOSTAS_ADICIONAIS[campo]:
                    raise ValueError("Resposta fora das opções do motor.")
                continue
            if campo not in OPCOES or campo == "vinculo_locador":
                raise ValueError("Pergunta desconhecida.")
            if isinstance(valor, (float, int)):
                minimo = 1 if campo == "area_m2" else 100
                if campo not in ("area_m2", "conteudo") or valor > MAX_NUMERO_JSON or not math.isfinite(valor) or valor < minimo:
                    raise ValueError("Informe uma área de pelo menos 1 m² ou bens de pelo menos R$ 100.")
            else:
                opcoes = {codigo for codigo, _ in OPCOES[campo]}
                if campo == "vinculo":
                    opcoes |= {codigo for codigo, _ in OPCOES["vinculo_locador"]}
                if valor not in opcoes | {"NAO_SEI"}:
                    raise ValueError("Resposta fora das opções do motor.")
        return respostas


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Redireciona só os caminhos de entrada nesta execução. Nenhuma regra é alterada.
    if os.environ.get("CASA_GEMEA_DADOS"):
        pasta = Path(os.environ["CASA_GEMEA_DADOS"]).expanduser().resolve()
        BASES.update({"desenvolvimento": pasta / "Seguro_Residencial_Desenvolvimento",
                      "teste": pasta / "Seguro_Residencial_Teste_Comum"})
    try:
        app.state.motor = Motor()
        app.state.erro = None
    except FileNotFoundError:
        app.state.motor = None
        app.state.erro = "As duas pastas Seguro_Residencial_* não foram encontradas. Inicie api/rodar.ps1 com -Dados apontando para a pasta que contém as duas bases."
    yield


app = FastAPI(title="Horus · Casa Gêmea", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=origens_locais(), allow_methods=["GET", "POST"],
                   allow_headers=["Content-Type"], allow_credentials=False)


@app.middleware("http")
async def nao_armazenar_dados(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/rede")
def rede_local():
    return {"ips": ips_locais()}


@app.exception_handler(RequestValidationError)
async def entrada_invalida(request: Request, exc: RequestValidationError):
    # Não ecoar valores ou corpos arbitrários na resposta de erro.
    return JSONResponse(status_code=422, content={"detail": "Entrada inválida. Confira a versão, o imóvel e as respostas do contrato."})


def motor_atual() -> Motor:
    if app.state.motor is None:
        raise HTTPException(503, detail=app.state.erro)
    return app.state.motor


@app.get("/api/health")
def health():
    motor_atual()
    return {"status": "ok", "versao_contrato": VERSAO_CONTRATO}


@app.get("/api/imoveis")
def imoveis():
    motor = motor_atual()
    # Lista explícita: nenhum perfil pessoal é serializado neste endpoint.
    return {
        "versao_contrato": VERSAO_CONTRATO,
        "campos_perguntaveis": [c for c in OPCOES if c != "vinculo_locador"],
        "imoveis": [
            {"imovel_id": row["imovel_id"], "cliente_id": row["cliente_id"],
             "municipio": row["municipio_real"], "uf": row["uf_real"]}
            for _, row in motor.casas.sort_index().iterrows()
        ],
    }


@app.get("/api/imoveis/{imovel_id}/sinais")
def sinais(imovel_id: str):
    motor = motor_atual()
    if imovel_id not in motor.casas.index:
        raise HTTPException(404, detail="Imóvel não encontrado.")
    valor = motor.casas.loc[imovel_id].get("inconsistencias", "")
    texto = valor if isinstance(valor, str) else ""
    return {"inconsistencias": [i.strip() for i in texto.split("|") if i.strip()]}


@app.post("/api/recomendar")
def recomendar(entrada: Entrada):
    motor = motor_atual()
    if entrada.imovel_id not in motor.casas.index:
        raise HTTPException(404, detail="Imóvel não encontrado no Teste Comum.")
    resultado = motor.recomendar(entrada.model_dump())
    if "erro" in resultado:
        raise HTTPException(422, detail=resultado["erro"])
    return resultado
