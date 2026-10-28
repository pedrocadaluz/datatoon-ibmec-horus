"""Caminhos, nomes de bases e constantes compartilhadas pelo projeto."""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

BASES = {
    "desenvolvimento": RAIZ / "Seguro_Residencial_Desenvolvimento",
    "teste": RAIZ / "Seguro_Residencial_Teste_Comum",
}

PASTA_SAIDAS = RAIZ / "saidas"
PASTA_DOCS = RAIZ / "docs"
PASTA_DADOS_EXTERNOS = RAIZ / "dados_externos"

# Os CSVs recebidos têm BOM (marca de ordem de bytes).
ENCODING = "utf-8-sig"

# Selos de natureza da informação (guia: "não apresente estimativas como fatos").
OBSERVADO = "OBSERVADO"
ESTIMADO = "ESTIMADO"
A_CONFIRMAR = "A_CONFIRMAR"
CONFIRMADO = "CONFIRMADO"  # informado pelo cliente na jornada de perguntas

# Níveis de confiança.
ALTA, MEDIA, BAIXA = "ALTA", "MEDIA", "BAIXA"

# Limiares de gasto com material de construção em 24 meses (R$).
# Calibrados na base de desenvolvimento: entre quem tem gasto, a mediana é ~9 mil
# e o percentil 90 é ~38 mil.
OBRA_REFORMA_MODERADA = 10_000
OBRA_POSSIVEL_RELEVANTE = 30_000

# Campos de perfil que NUNCA entram em risco, plano ou valor (guardrail do guia).
CAMPOS_PROIBIDOS = ["idade", "renda_mensal", "origem_renda", "confianca_renda"]

# Campos de perfil usados apenas para escolher o canal de atendimento.
CAMPOS_SO_CANAL = ["usuario_app", "frequencia_acesso_app_90d", "indice_maturidade_digital"]
