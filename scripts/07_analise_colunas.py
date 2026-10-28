"""Etapa 07: Análise minuciosa de todas as colunas da base para hiperpersonalização.

Uso (na raiz do projeto):
    python scripts/07_analise_colunas.py

Saídas:
    saidas/analise_colunas.csv   73 linhas (uma por coluna das 5 tabelas de dados)
    docs/07_analise_colunas.md   relatório executivo (até 3 páginas, apenas agregados)
"""

import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.cluster import KMeans  # noqa: E402
from sklearn.metrics import adjusted_rand_score, silhouette_score  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from casa_gemea.carregar import ler_base, montar_tabela_imoveis  # noqa: E402
from casa_gemea.config import ENCODING, PASTA_DOCS, PASTA_SAIDAS  # noqa: E402

SEMENTE = 42
TABELAS_DADOS = ["clientes", "enderecos_imoveis", "sinais_imobiliarios", "bens_compras", "territorio"]


def br(valor: float, casas: int = 1) -> str:
    """Formata número no padrão brasileiro (1.234,5)."""
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def tabela_md(df: pd.DataFrame) -> str:
    linhas = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    linhas += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(linhas)


def cramers_v_corrigido(x: pd.Series, y: pd.Series) -> float:
    """Cramér's V com correção de viés de Bergsma (2013)."""
    xc, r = pd.factorize(x.astype(str), sort=True)
    yc, k = pd.factorize(y.astype(str), sort=True)
    if len(r) <= 1 or len(k) <= 1:
        return 0.0
    ct = np.bincount(xc * len(k) + yc, minlength=len(r) * len(k)).reshape(len(r), len(k)).astype(float)
    ct = ct[ct.sum(axis=1) > 0][:, ct.sum(axis=0) > 0]
    n = float(ct.sum())
    if n <= 1 or ct.shape[0] <= 1 or ct.shape[1] <= 1:
        return 0.0
    esperado = (ct.sum(axis=1, keepdims=True) @ ct.sum(axis=0, keepdims=True)) / n
    chi2 = float(np.where(esperado > 0, (ct - esperado) ** 2 / esperado, 0.0).sum())
    phi2 = max(0.0, chi2 / n - ((ct.shape[0] - 1) * (ct.shape[1] - 1)) / (n - 1))
    r_corr = ct.shape[0] - ((ct.shape[0] - 1) ** 2) / (n - 1)
    k_corr = ct.shape[1] - ((ct.shape[1] - 1) ** 2) / (n - 1)
    denom = min(r_corr - 1, k_corr - 1)
    return float(np.sqrt(phi2 / denom)) if denom > 0 else 0.0


# ----------------------------------------------------------------- metadados das 73 colunas
# Cada entrada define: (tipo_semantico, uso_atual, ideias_de_feature, sinal_para_cobertura, forca_do_sinal, risco)
META_COLUNAS: dict[tuple[str, str], tuple[str, str, str, str, str, str]] = {
    # === CLIENTES (12) ===
    ("CLIENTES", "cliente_id"): (
        "ID_CHAVE (str)",
        "USADA_SO_CALCULO: chave de junção entre tabelas e agrupamento de múltiplos imóveis (carregar.py)",
        "qtd_imoveis_cliente = count(imovel_id por cliente_id); flag_multi_imovel = (qtd_imoveis_cliente > 1)",
        "Indireto (via múltiplos imóveis): segunda residência afeta ROUBO_FURTO_ARROMBAMENTO e PERDA_PAGAMENTO_ALUGUEL",
        "NULA",
        "Identificador pseudonimizado; não expor casos individuais em relatórios",
    ),
    ("CLIENTES", "idade"): (
        "INTEIRO_CONTINUO (int64, anos)",
        "IGNORADA_HOJE: listada em config.CAMPOS_PROIBIDOS (0 efeito no motor atual)",
        "faixa_momento_vida = cut(idade, [18,30,45,60,90]); flag_senior_assistencia = (idade >= 60) para destacar assistência 24h e acessibilidade na argumentação",
        "Sinal nulo na base sintética para plano/risco; em produto real apoia tom de comunicação e destaque de DESPESAS_EMERGENCIAIS e assistências residenciais",
        "FRACA",
        "Atributo pessoal (LGPD): nunca usar para encarecer prêmio ou negar elegibilidade; no gerador tem correlação zero com todas as variáveis",
    ),
    ("CLIENTES", "renda_mensal"): (
        "MOEDA_CONTINUO (int64, R$)",
        "IGNORADA_HOJE: listada em config.CAMPOS_PROIBIDOS (0 efeito direto no motor atual)",
        "comprometimento_moradia = (valor_aluguel_recorrente + parcela_financiamento_imobiliario + pagamento_condominio_mensal) / renda_mensal; razao_obra_renda = gastos_material_construcao_24m / (12 * renda_mensal); gap_protecao_patrimonial = conteudo_estimado / renda_mensal",
        "PERDA_PAGAMENTO_ALUGUEL e DESPESAS_EMERGENCIAIS (alta necessidade quando comprometimento_moradia >= 30%, pois sinistro compromete fluxo mensal); ROUBO_FURTO_ARROMBAMENTO e DANOS_ELETRICOS (via estoque de bens)",
        "FORTE",
        "Viés socioeconômico se usada isoladamente para negar cobertura; na base sintética governa compras 36m (rho=+0,83), aluguel pago (rho=+0,79), financiamento (rho=+0,75) e gasto de obra >0 (rho=+0,82)",
    ),
    ("CLIENTES", "origem_renda"): (
        "CATEGORICO_BINARIO (str)",
        "IGNORADA_HOJE: listada em config.CAMPOS_PROIBIDOS",
        "flag_renda_comprovada = (origem_renda == 'INFORMADA'); peso_confianca_comprometimento = 1,0 se INFORMADA senão 0,7",
        "Modulador de confiança para dimensionar PERDA_PAGAMENTO_ALUGUEL e capacidade de absorção de franquia",
        "FRACA",
        "100% colinear com confianca_renda (INFORMADA <-> ALTA, PRESUMIDA <-> MEDIA); semente sintética equilibrada 50%/50%",
    ),
    ("CLIENTES", "confianca_renda"): (
        "CATEGORICO_ORDINAL (str)",
        "IGNORADA_HOJE: listada em config.CAMPOS_PROIBIDOS",
        "Redundante com origem_renda (colinearidade perfeita V=1,000); manter apenas flag_renda_comprovada",
        "Modulador de largura de faixa quando a renda entra em índices de comprometimento familiar",
        "NULA",
        "Redundância total (100% bijetiva com origem_renda na base de desenvolvimento e na de teste)",
    ),
    ("CLIENTES", "indice_maturidade_digital"): (
        "INTEIRO_ESCALA_0_100 (int64)",
        "IGNORADA_HOJE: listada em config.CAMPOS_SO_CANAL, mas semaforo() usa apenas usuario_app",
        "tier_jornada_digital = 'AUTONOMO_OCB' se >= 70, 'GUIADO_APP' se 35 a 69, 'ASSISTIDO_HUMANO' se < 35; controla nível de detalhe da explicação na interface",
        "Não altera cobertura securitária; define canal (One Click Buy vs. App Guiado vs. SAC/Gerente) e formato de contratação",
        "MEDIA",
        "Gerador aplica corte determinístico exato: usuario_app == 'SIM' equivale a indice_maturidade_digital >= 35 em 100% dos casos",
    ),
    ("CLIENTES", "usuario_app"): (
        "BINARIO_SIM_NAO (str)",
        "USADA_SO_CANAL: define ONE_CLICK_BUY (no sinal verde) ou APP_COM_CONFIRMACAO (no amarelo) em regras.semaforo()",
        "Combinar com frequencia_acesso_app_90d >= 30 para One Click Buy real (evitando enviar ao OCB clientes com usuario_app=SIM mas 0 acessos recentes)",
        "Não altera cobertura; direciona canal de autoatendimento vs. atendimento assistido",
        "MEDIA",
        "Inconsistência na base: 235 clientes com usuario_app=NAO possuem frequencia_acesso_app_90d > 0 (até 69 acessos), e 17 clientes com SIM têm 0 acessos",
    ),
    ("CLIENTES", "frequencia_acesso_app_90d"): (
        "INTEIRO_CONTINUO (int64, acessos/90d)",
        "IGNORADA_HOJE: listada em config.CAMPOS_SO_CANAL, mas não lida em regras.semaforo()",
        "engajamento_app_diario = frequencia_acesso_app_90d / 90; flag_heavy_user_app = (frequencia_acesso_app_90d >= 90) para notificação contextual de upgrade de cobertura in-app",
        "Não altera cobertura; prioriza gatilho de oferta ativa in-app e contratação em 1 clique",
        "MEDIA",
        "Forte correlação com indice_maturidade_digital (rho=+0,80); apresenta valores >0 mesmo quando usuario_app=NAO",
    ),
    ("CLIENTES", "quantidade_dependentes"): (
        "INTEIRO_DISCRETO (int64, 0 a 3)",
        "USADA_NA_DECISAO: +1 ponto para TOTAL (regras.pontuar_plano) e escala faixas de RESPONSABILIDADE_CIVIL_FAMILIAR e DESPESAS_EMERGENCIAIS",
        "tamanho_domicilio = 1 + quantidade_dependentes; consumo_agua_por_pessoa = agua_media_mensal_6m / (1 + quantidade_dependentes); flag_familia_numerosa = (quantidade_dependentes >= 2)",
        "RESPONSABILIDADE_CIVIL_FAMILIAR (+R$ 5 mil a R$ 10 mil de LMI por dependente, danos de filhos/empregados a terceiros, CG RC 1.1) e DESPESAS_EMERGENCIAIS (diárias de hospedagem familiar, CG 1.3)",
        "FORTE",
        "Indica necessidade familiar legítima; no gerador também impulsiona agua_media_mensal_6m (rho=+0,70) e energia_media_mensal_6m (rho=+0,31)",
    ),
    ("CLIENTES", "possui_pet_informado"): (
        "BINARIO_SIM_NAO (str)",
        "USADA_NA_DECISAO: +1 ponto para TOTAL (regras.pontuar_plano) e adiciona R$ 10 mil a R$ 30 mil na faixa de RESPONSABILIDADE_CIVIL_FAMILIAR",
        "interacao_pet_condominio = (possui_pet_informado == 'SIM') & (pagamento_condominio_mensal > 0); interacao_pet_familia = (possui_pet_informado == 'SIM') & (quantidade_dependentes > 0)",
        "RESPONSABILIDADE_CIVIL_FAMILIAR (cobre danos corporais e materiais causados por animais domésticos a terceiros e vizinhos, CG RC 1.1 c) e argumento para assistência pet",
        "FORTE",
        "Baixo risco de viés; alta relevância de argumento comercial palpável para o cliente ('seu pet está coberto contra acidentes com vizinhos')",
    ),
    ("CLIENTES", "qtd_produtos_seguridade"): (
        "INTEIRO_DISCRETO (int64, 0 a 3)",
        "IGNORADA_HOJE: não utilizada em src/casa_gemea/",
        "propensao_seguridade = 'ALTA_CARTEIRA' se >= 2, 'INICIADO' se == 1, 'ESTREANTE' se == 0; flag_inconsistencia_seguro = (possui_seguro_residencial == 'SIM') & (qtd_produtos_seguridade == 0)",
        "Não muda o risco físico, mas define apetite a pacotes completos (TOTAL ou coberturas adicionais de RC e Despesas Emergenciais em cross-sell)",
        "MEDIA",
        "Inconsistência crítica do gerador: 144 de 366 clientes (39,3%) com possui_seguro_residencial=SIM têm qtd_produtos_seguridade=0",
    ),
    ("CLIENTES", "possui_seguro_residencial"): (
        "BINARIO_SIM_NAO (str)",
        "IGNORADA_HOJE: não utilizada em src/casa_gemea/",
        "modo_recomendacao = 'ENDOSSO_UPGRADE_LMI' se SIM senão 'NOVA_CONTRATACAO'; permite comparar a apólice atual com as lacunas detectadas na Casa Gêmea",
        "Transversal a todas as coberturas: muda o pitch de 'contratar seguro' para 'revisar capital segurado defasado ou adicionar ROUBO/RC/ALUGUEL ausentes na apólice atual'",
        "FORTE",
        "No gerador sintético foi sorteada independentemente (16,6% dev, 22,5% teste, V~0 com plano, vínculo e renda), mas no produto real é essencial para evitar oferta duplicada",
    ),
    # === ENDERECOS_IMOVEIS (22) ===
    ("ENDERECOS_IMOVEIS", "imovel_id"): (
        "ID_CHAVE (str)",
        "USADA_SO_CALCULO: chave primária de imóvel em todo o pipeline e no contrato JSON",
        "ordem_imovel_cliente = sufixo numérico (_01 vs _02) indicando primeiro ou segundo imóvel cadastrado do cliente",
        "Nenhuma (identificador)",
        "NULA",
        "Identificador pseudonimizado",
    ),
    ("ENDERECOS_IMOVEIS", "cliente_id"): (
        "ID_CHAVE (str)",
        "USADA_SO_CALCULO: chave estrangeira para unir com clientes e contar imóveis por titular",
        "Ver CLIENTES.cliente_id",
        "Nenhuma (identificador)",
        "NULA",
        "Identificador pseudonimizado",
    ),
    ("ENDERECOS_IMOVEIS", "territorio_id"): (
        "ID_CHAVE (str)",
        "USADA_SO_CALCULO: chave 1:1 para unir com territorio.csv (carregar.py)",
        "Redundante com imovel_id (relação bijetiva 1:1 TER_... <-> IMO_...)",
        "Nenhuma (identificador)",
        "NULA",
        "Identificador pseudonimizado",
    ),
    ("ENDERECOS_IMOVEIS", "logradouro"): (
        "CATEGORICO_TEXTO (str)",
        "IGNORADA_HOJE: não lida pelo motor",
        "tipo_via = extrair prefixo ('Avenida', 'Rua', 'Estrada', 'Alameda', 'Travessa', 'Rodovia'); flag_via_rural_estrada = prefixo in ('Estrada', 'Rodovia')",
        "IMPACTO_VEICULOS_TERRESTRES (vias de trânsito rápido como Avenidas/Estradas em casas) e alerta de validação de zona rural se Estrada/Rodovia",
        "FRACA",
        "No LEIA-ME consta como endereço fictício; na base sintética o prefixo 'Estrada Araucarias' (4,0%) não tem correlação com ruralidade real",
    ),
    ("ENDERECOS_IMOVEIS", "numero"): (
        "INTEIRO_CADASTRAL (int64)",
        "IGNORADA_HOJE: não lida pelo motor",
        "Nenhuma feature recomendada (ruído uniforme entre 1 e 2498)",
        "Nenhuma evidência para cobertura",
        "NULA",
        "Dado puramente sintético e uniforme; usar geraria overfitting espúrio",
    ),
    ("ENDERECOS_IMOVEIS", "complemento"): (
        "CATEGORICO_TEXTO (str, 10 categorias)",
        "USADA_NA_DECISAO: texto exibido na evidência e checagem de palavra 'CASA' para definir confiança ALTA vs MEDIA em inferencias._regra_tipo()",
        "subtipo_imovel_complemento = 'CASA_CONDOMINIO_LOTE' se contém 'QUADRA' ou 'LOTE', 'CASA_FUNDOS' se 'FUNDOS', 'APTO_TORRE_BLOCO' se 'TORRE' ou 'BLOCO'",
        "ROUBO_FURTO_ARROMBAMENTO, VENDAVAL_GRANIZO e IMPACTO_VEICULOS_TERRESTRES (casas de rua/lote têm maior exposição perimetral e de telhado que apartamentos)",
        "FORTE",
        "Em 'LOTE 04' (11,1% da base), possui_termo_casa=SIM mas a string não contém a palavra 'CASA', o que reduz a confiança do tipo para MEDIA",
    ),
    ("ENDERECOS_IMOVEIS", "bairro"): (
        "CATEGORICO_NOMINAL (str, SETOR_01 a SETOR_36)",
        "IGNORADA_HOJE: não lida pelo motor",
        "densidade_vertical_setor = média de apartamentos no par (municipio_real, bairro); iptu_m2_setor = mediana de IPTU/m2 no setor",
        "Em base real de seguradora, bairro calibra risco de ROUBO_FURTO_ARROMBAMENTO, VENDAVAL_GRANIZO e DANOS_ELETRICOS; na base sintética os 36 setores são uniformes",
        "FRACA",
        "Bairros fictícios (SETOR_XX) sem georreferenciamento real; não atribuir risco criminal a setores sintéticos",
    ),
    ("ENDERECOS_IMOVEIS", "municipio_real"): (
        "CATEGORICO_NOMINAL (str, 10 capitais)",
        "USADA_SO_CALCULO: efeito fixo no modelo de área (area.py) e calibração de IPTU/m2 e aluguel/m2 (calibracao.py)",
        "custo_aluguel_m2_cidade = mediana de aluguel/m2 do município; pressao_iptu_cidade = iptu_m2_mediana; permite normalizar gastos e estimar moradia temporária",
        "INCENDIO_RAIO_EXPLOSAO_FUMACA (via estimativa de área) e PERDA_PAGAMENTO_ALUGUEL (dimensiona aluguel de moradia temporária para proprietário morador)",
        "FORTE",
        "Referência territorial real; modelo de área depende dos 10 municípios calibrados (extrapolar para outras cidades requer fallback por UF)",
    ),
    ("ENDERECOS_IMOVEIS", "uf_real"): (
        "CATEGORICO_NOMINAL (str, 10 UFs)",
        "USADA_SO_CALCULO: seleciona o CUB R8-N (R$/m2) da UF para calcular custo de reconstrução do prédio (regras.custo_reconstrucao)",
        "cub_uf_r8n = mapa de custo Sinduscon por UF (de R$ 2.218,68/m2 na BA a R$ 2.943,73/m2 no RS)",
        "INCENDIO_RAIO_EXPLOSAO_FUMACA, DANOS_POR_AGUA, VENDAVAL_GRANIZO, IMPACTO_VEICULOS_TERRESTRES e QUEDA_AERONAVE (dimensiona valor de reconstrução do prédio)",
        "FORTE",
        "Relação bijetiva 1:1 com municipio_real na base (1 capital por UF); GO usa proxy do DF no CUB R8-N",
    ),
    ("ENDERECOS_IMOVEIS", "codigo_ibge_municipio"): (
        "INTEIRO_CATEGORICO (int64, 10 códigos)",
        "USADA_SO_CALCULO: exportada em COLUNAS_CASA_GEMEA para rastreabilidade territorial",
        "Chave padrão para cruzamento com bases públicas do IBGE/CEMADEN/INMET em produção",
        "Mesmo efeito de municipio_real (colinearidade perfeita 1:1)",
        "NULA",
        "Redundante com municipio_real dentro da base atual",
    ),
    ("ENDERECOS_IMOVEIS", "cep_agregado"): (
        "CATEGORICO_NOMINAL (str, 389 códigos)",
        "IGNORADA_HOJE: não lida pelo motor",
        "cluster_microterritorio = prefixo de cep_agregado; na base sintética tem no máximo 23 imóveis por código",
        "Em produção real, micro-CEP refina VENDAVAL_GRANIZO (alagamento/arborização) e DANOS_ELETRICOS (rede aérea vs. subterrânea)",
        "FRACA",
        "CEP fictício agregado (ex.: SP-308-02); alta cardinalidade (389) e baixa amostragem por célula na base de teste",
    ),
    ("ENDERECOS_IMOVEIS", "endereco_principal_compativel"): (
        "BINARIO_SIM_NAO (str)",
        "USADA_NA_DECISAO: define uso_imovel (MORADIA_HABITUAL vs TEMPORADA_OU_SEGUNDA_RESIDENCIA) e detecta conflito com locador (inferencias.py)",
        "status_ocupacao_inferido = combinar endereco_principal_compativel com qtd_imoveis_cliente, agua_media_mensal_6m e energia_media_mensal_6m para distinguir imóvel vago de habitado",
        "ROUBO_FURTO_ARROMBAMENTO e PERDA_PAGAMENTO_ALUGUEL (imóvel desocupado perde cobertura de roubo e aluguel nas CG: Roubo 2.1 c e Aluguel 3.1 a)",
        "FORTE",
        "Anomalia importante: 392 clientes com apenas 1 imóvel têm endereco_principal_compativel=NAO, e 240 clientes com 2 imóveis têm SIM em ambos",
    ),
    ("ENDERECOS_IMOVEIS", "possui_termo_apartamento"): (
        "BINARIO_SIM_NAO (str)",
        "USADA_NA_DECISAO: define tipo_imovel = APARTAMENTO em inferencias._regra_tipo()",
        "conflito_apto_sem_condominio = (possui_termo_apartamento == 'SIM') & (pagamento_condominio_mensal == 0)",
        "Dimensiona interesse segurável do prédio (10% a 30% em apartamento vs 100% em casa, CG 5.4/15.2) e recomendação de RESPONSABILIDADE_CIVIL_FAMILIAR (infiltração no vizinho, CG RC 1.1 e)",
        "FORTE",
        "Exatamente complementar a possui_termo_casa na base (soma = 100% em dev e teste); 397 apartamentos não têm condomínio pago",
    ),
    ("ENDERECOS_IMOVEIS", "possui_termo_casa"): (
        "BINARIO_SIM_NAO (str)",
        "USADA_NA_DECISAO: define tipo_imovel (CASA ou CASA_EM_CONDOMINIO) e soma +1 ponto para o plano PRATICO (regras.pontuar_plano)",
        "casa_rua_exposta = (possui_termo_casa == 'SIM') & (pagamento_condominio_mensal == 0); casa_fechada = (possui_termo_casa == 'SIM') & (pagamento_condominio_mensal > 0)",
        "ROUBO_FURTO_ARROMBAMENTO (+1 ponto Prático por acessos térreo), VENDAVAL_GRANIZO (20% prédio vs 3% apto), IMPACTO_VEICULOS_TERRESTRES (10% vs 3%) e INCENDIO (100% da estrutura)",
        "FORTE",
        "100% colinear com o complemento de possui_termo_apartamento na base atual",
    ),
    ("ENDERECOS_IMOVEIS", "possui_termo_bloco"): (
        "BINARIO_SIM_NAO (str)",
        "IGNORADA_HOJE: não lida pelo motor",
        "flag_conjunto_vertical = (possui_termo_bloco == 'SIM'); reforça classificação de apartamento mesmo quando pagamento_condominio_mensal == 0",
        "Auxilia na confiança de tipo_imovel = APARTAMENTO (nos 58 casos de 'BLOCO B APTO 305' sem condomínio pago, reduzindo necessidade de pergunta)",
        "FRACA",
        "100% determinística: vale SIM apenas quando complemento == 'BLOCO B APTO 305' (7,6% da base)",
    ),
    ("ENDERECOS_IMOVEIS", "possui_termo_condominio"): (
        "BINARIO_SIM_NAO (str)",
        "USADA_NA_DECISAO: usada em inferencias._regra_tipo() junto com pagamento_condominio_mensal > 0",
        "Redundante com (pagamento_condominio_mensal > 0): as duas condições são 100% idênticas nos 2.578 imóveis de dev e 138 de teste",
        "Diferencia CASA_EM_CONDOMINIO (interesse segurável de 80% a 100% do prédio) de CASA de rua e confirma APARTAMENTO com confiança ALTA",
        "MEDIA",
        "Apesar do nome sugerir texto de endereço, no gerador sintético foi preenchida exatamente como (pagamento_condominio_mensal > 0)",
    ),
    ("ENDERECOS_IMOVEIS", "area_cadastrada_m2"): (
        "INTEIRO_CONTINUO (int64, m2, 0 = ausente)",
        "USADA_SO_CALCULO: define area_m2 quando > 0 e treina ModeloArea (area.py); estreita todas as faixas de prédio e vidros",
        "residuo_log_area = log(area_cadastrada_m2) - log(area_estimada_m2); flag_area_suspeita = abs(residuo_log_area) > quantil_975",
        "INCENDIO_RAIO_EXPLOSAO_FUMACA, DANOS_POR_AGUA, VENDAVAL_GRANIZO, IMPACTO_VEICULOS_TERRESTRES, QUEDA_AERONAVE, QUEBRA_DE_VIDROS e PERDA_PAGAMENTO_ALUGUEL (proprietário morador)",
        "FORTE",
        "Ausente (valor 0) em 60,6% de dev e 66,7% de teste; quando presente mas divergente de IPTU/energia (2,4% dos casos), requer confirmação",
    ),
    ("ENDERECOS_IMOVEIS", "origem_area"): (
        "CATEGORICO_NOMINAL (str, 4 categorias)",
        "USADA_NA_DECISAO: quando 'LAUDO_FINANCIAMENTO' sem parcela atual, eleva confiança de PROPRIETARIO_QUITADO para ALTA (inferencias._regra_vinculo)",
        "peso_precisao_area = 1,0 se LAUDO_FINANCIAMENTO, 0,9 se CADASTRO_IPTU ou CADASTRO_PUBLICO_MUNICIPAL, 0,0 se NAO_DISPONIVEL",
        "Aumenta confiança (estreita faixa de LMI) de INCENDIO_RAIO_EXPLOSAO_FUMACA e demais coberturas de prédio; evita pergunta desnecessária de vínculo para quitados",
        "MEDIA",
        "Quando NAO_DISPONIVEL (60,6%), area_cadastrada_m2 é sempre 0",
    ),
    ("ENDERECOS_IMOVEIS", "confianca_area"): (
        "CATEGORICO_BINARIO (str, ALTA ou BAIXA)",
        "IGNORADA_HOJE: o motor recalcula area_m2_confianca diretamente a partir de (area_cadastrada_m2 > 0)",
        "Redundante: 100% bijetiva com (area_cadastrada_m2 > 0) -> ALTA (39,4%) e (area_cadastrada_m2 == 0) -> BAIXA (60,6%)",
        "Indica se as coberturas de estrutura e QUEBRA_DE_VIDROS partem de metragem observada ou estimada",
        "NULA",
        "Colinearidade perfeita (100%) com a presença de area_cadastrada_m2",
    ),
    ("ENDERECOS_IMOVEIS", "padrao_construtivo_cadastrado"): (
        "CATEGORICO_ORDINAL (str, ECONOMICO/NORMAL/SUPERIOR + NAO_DISPONIVEL)",
        "USADA_SO_CALCULO: aplica fator CUB Sinduscon (0,75x a 1,56x) no custo de reconstrução do prédio (regras.custo_reconstrucao)",
        "estimativa_padrao_combinada = usar razão de IPTU/m2 (todas as tipologias) + condominio/m2 (quando condomínio > 0: mediana R$ 6,33 no Econômico, R$ 7,00 no Normal e R$ 10,00 no Superior)",
        "INCENDIO_RAIO_EXPLOSAO_FUMACA, DANOS_POR_AGUA, VENDAVAL_GRANIZO, IMPACTO_VEICULOS_TERRESTRES, QUEDA_AERONAVE e QUEBRA_DE_VIDROS (acabamentos e esquadrias especiais)",
        "FORTE",
        "Ausente ('NAO_DISPONIVEL') em 72,8% de dev e 71,0% de teste; curiosidade sintética: no gerador tem correlação levemente negativa com renda",
    ),
    ("ENDERECOS_IMOVEIS", "material_parede_externa_cadastrado"): (
        "CATEGORICO_BINARIO (str, ALVENARIA ou NAO_DISPONIVEL)",
        "USADA_NA_DECISAO: checada em regras.avaliar_elegibilidade() contra MATERIAIS_COMBUSTIVEIS",
        "flag_declaracao_alvenaria_necessaria = (material_parede_externa_cadastrado == 'NAO_DISPONIVEL')",
        "Pré-requisito de elegibilidade para INCENDIO_RAIO_EXPLOSAO_FUMACA e para a apólice como um todo (Guia 9.1)",
        "FRACA",
        "Sem variância discriminante na base: 78,3% NAO_DISPONIVEL e 21,7% ALVENARIA (0 casos de madeira/combustível); resolvido via declaração única",
    ),
    ("ENDERECOS_IMOVEIS", "situacao_imovel_cadastral"): (
        "CONSTANTE (str, 100% REGULAR)",
        "USADA_NA_DECISAO: checada em regras.avaliar_elegibilidade() (se != REGULAR seria INELEGIVEL)",
        "Manter apenas como trava defensiva de regra (guardrail cadastral)",
        "Elegibilidade geral da apólice",
        "NULA",
        "Variância zero (100,0% REGULAR em desenvolvimento e teste); não tem poder discriminante nos dados fornecidos",
    ),
    # === SINAIS_IMOBILIARIOS (18) ===
    ("SINAIS_IMOBILIARIOS", "cliente_id"): (
        "ID_CHAVE (str)",
        "USADA_SO_CALCULO: chave de junção com enderecos_imoveis",
        "Ver CLIENTES.cliente_id",
        "Nenhuma (identificador)",
        "NULA",
        "Identificador pseudonimizado",
    ),
    ("SINAIS_IMOBILIARIOS", "imovel_id"): (
        "ID_CHAVE (str)",
        "USADA_SO_CALCULO: chave de junção 1:1 com enderecos_imoveis",
        "Ver ENDERECOS_IMOVEIS.imovel_id",
        "Nenhuma (identificador)",
        "NULA",
        "Identificador pseudonimizado",
    ),
    ("SINAIS_IMOBILIARIOS", "pagamento_aluguel_recorrente"): (
        "BINARIO_SIM_NAO (str)",
        "USADA_NA_DECISAO: define vinculo = INQUILINO (+2 pontos para TOTAL) e reduz interesse segurável no prédio para 3% a 10% (benfeitorias)",
        "flag_inquilino = (pagamento_aluguel_recorrente == 'SIM'); direciona argumentação para proteção de conteúdo próprio, aluguel e RC perante o locador",
        "PERDA_PAGAMENTO_ALUGUEL (forte: inquilino continua devendo aluguel ou precisa de moradia temporária se o imóvel sinistrar, CG 1.1.2) e RESPONSABILIDADE_CIVIL_FAMILIAR",
        "FORTE",
        "100% mutuamente exclusivo com financiamento e crédito de aluguel na base; 100% bijetivo com (valor_aluguel_recorrente > 0)",
    ),
    ("SINAIS_IMOBILIARIOS", "valor_aluguel_recorrente"): (
        "MOEDA_CONTINUO (int64, R$/mês, 0 se não inquilino)",
        "USADA_SO_CALCULO: dimensiona faixa de PERDA_PAGAMENTO_ALUGUEL (3x a 6x o aluguel mensal) e calibra aluguel/m2 por cidade (calibracao.py)",
        "comprometimento_aluguel_renda = valor_aluguel_recorrente / renda_mensal; razao_aluguel_m2_cidade = (valor_aluguel_recorrente / area_m2) / mediana_aluguel_m2_municipio",
        "PERDA_PAGAMENTO_ALUGUEL (dimensionamento direto do LMI de 3 a 6 meses, CG Perda de Aluguel 1.2) e proxy de padrão do imóvel alugado",
        "FORTE",
        "Entre inquilinos (>0), correlaciona fortemente com renda_mensal (rho=+0,792) e moderadamente com area_cadastrada_m2 (rho=+0,299)",
    ),
    ("SINAIS_IMOBILIARIOS", "credito_recorrente_compativel_aluguel"): (
        "BINARIO_SIM_NAO (str)",
        "USADA_NA_DECISAO: define vinculo = PROPRIETARIO_LOCADOR (+2 pontos para TOTAL) e limita conteúdo segurado a 20% (bens de terceiros excluídos, CG 6.1 r)",
        "locador_confirmado_secundario = (credito_recorrente_compativel_aluguel == 'SIM') & (endereco_principal_compativel == 'NAO'); locador_em_conflito = SIM & endereco_principal_compativel == 'SIM'",
        "PERDA_PAGAMENTO_ALUGUEL (protege a renda mensal de locação que cessa se o imóvel ficar inabitável, CG 1.1.1) e INCENDIO (100% do prédio, 20% conteúdo)",
        "FORTE",
        "Alta taxa de conflito cadastral: 186 de 241 casos (77,2% em dev) ocorrem no endereço principal do cliente, exigindo 1 pergunta de confirmação",
    ),
    ("SINAIS_IMOBILIARIOS", "valor_medio_credito_recorrente"): (
        "MOEDA_CONTINUO (int64, R$/mês, 0 se não locador)",
        "USADA_SO_CALCULO: dimensiona faixa de PERDA_PAGAMENTO_ALUGUEL do locador (3x a 6x o crédito mensal)",
        "area_impl_credito_aluguel = valor_medio_credito_recorrente / aluguel_m2_mediano_cidade; nos locadores com área real, tem correlação rho=+0,899 com area_cadastrada_m2!",
        "PERDA_PAGAMENTO_ALUGUEL (LMI exato de perda de renda de aluguel por 3 a 6 meses) e estimativa cruzada da área do imóvel locado",
        "FORTE",
        "Descoberta chave: ao contrário do aluguel pago pelo inquilino, o crédito recebido pelo locador não depende da renda do cliente (rho=+0,021), mas sim da área do imóvel (rho=+0,899)",
    ),
    ("SINAIS_IMOBILIARIOS", "quantidade_creditos_recorrentes_12m"): (
        "INTEIRO_DISCRETO (int64, 0 ou 8 a 12 meses)",
        "USADA_NA_DECISAO: define confiança do vínculo de locador (MEDIA se >= 10 meses e fora do endereço principal, senão BAIXA em inferencias._regra_vinculo)",
        "taxa_ocupacao_locacao_12m = quantidade_creditos_recorrentes_12m / 12; se < 10 meses (8 ou 9), sinaliza rotatividade de inquilino / vacância",
        "PERDA_PAGAMENTO_ALUGUEL (confiança da renda locatícia) e alerta de vacância para ROUBO_FURTO_ARROMBAMENTO (períodos desocupados entre locações)",
        "MEDIA",
        "Positiva apenas nos 241 locadores (valores 8, 9, 10, 11 ou 12 meses)",
    ),
    ("SINAIS_IMOBILIARIOS", "parcela_financiamento_imobiliario"): (
        "MOEDA_CONTINUO (int64, R$/mês, 0 se não financiado)",
        "USADA_NA_DECISAO: define vinculo = PROPRIETARIO_FINANCIADO e ajusta interesse segurável do prédio (50% a 100%, pois DFI cobre estrutura em 1o risco, CG 15.2)",
        "comprometimento_financiamento = parcela_financiamento_imobiliario / renda_mensal; razao_parcela_predio = (parcela_financiamento_imobiliario * 120) / custo_reconstrucao",
        "Reduz necessidade de superdimensionar INCENDIO no prédio (já há DFI habitacional) e redireciona o orçamento do cliente para ROUBO_FURTO_ARROMBAMENTO, DANOS_ELETRICOS e RC_FAMILIAR",
        "FORTE",
        "Entre financiados (>0, 30,3% da base), correlaciona com renda_mensal (rho=+0,751) e com area_cadastrada_m2 (rho=+0,363)",
    ),
    ("SINAIS_IMOBILIARIOS", "pagamento_condominio_mensal"): (
        "MOEDA_CONTINUO (int64, R$/mês, 0 se sem condomínio)",
        "USADA_NA_DECISAO: distingue CASA_EM_CONDOMINIO de CASA de rua e confirma APARTAMENTO com confiança ALTA (inferencias._regra_tipo)",
        "condominio_por_m2 = pagamento_condominio_mensal / area_m2; area_impl_condominio = pagamento_condominio_mensal / 6,85 (quando > 0, correlaciona rho=+0,815 com area_cadastrada_m2!)",
        "Define interesse segurável no prédio (10%-30% em apto, 80%-100% em casa em condomínio, CG 5.4/15.2) e puxa RESPONSABILIDADE_CIVIL_FAMILIAR (danos/vazamentos a vizinhos e áreas comuns)",
        "FORTE",
        "Paradoxo de Simpson: na base inteira tem correlação ~0 com área porque casas de rua (maiores) têm condomínio=0; mas condicionando em >0 (n=983), rho=+0,815 com área e indica padrão SUPERIOR (mediana R$ 10,00/m2 vs R$ 6,33/m2 no Econômico)!",
    ),
    ("SINAIS_IMOBILIARIOS", "pagamento_iptu_anual"): (
        "MOEDA_CONTINUO (int64, R$/ano)",
        "USADA_SO_CALCULO: principal preditor de area_m2 (area.py, coef +0,6 em log) e indicador de padrao_construtivo via razão IPTU/m2 (inferencias.inferir_padrao)",
        "iptu_por_m2_normalizado = (pagamento_iptu_anual / area_m2) / mediana_iptu_m2_municipio; separa padrão ECONOMICO (mediana 0,82x), NORMAL (0,98x) e SUPERIOR (1,32x)",
        "INCENDIO_RAIO_EXPLOSAO_FUMACA, DANOS_POR_AGUA, VENDAVAL_GRANIZO, IMPACTO_VEICULOS_TERRESTRES, QUEDA_AERONAVE e QUEBRA_DE_VIDROS (via metragem e padrão de acabamento)",
        "FORTE",
        "Se a área foi estimada a partir do próprio IPTU, não usar IPTU/m2 para inferir padrão construtivo (evita raciocínio circular, já bloqueado em inferir_padrao)",
    ),
    ("SINAIS_IMOBILIARIOS", "energia_media_mensal_6m"): (
        "MOEDA_CONTINUO (int64, R$/mês)",
        "USADA_SO_CALCULO: segundo preditor do modelo de área (area.py, coef +0,4 em log) e detecção de área divergente",
        "intensidade_eletrica_m2 = energia_media_mensal_6m / area_m2; excesso_energia_esperada = energia_media_mensal_6m / (area_m2 * 3,3 + 40 * quantidade_dependentes) (sinal de ar-condicionado/equipamentos potentes)",
        "DANOS_ELETRICOS (maior carga elétrica instalada e climatização; 53,3% dos sinistros da carteira BB Seguros) e INCENDIO_RAIO_EXPLOSAO_FUMACA (via área)",
        "FORTE",
        "Correlaciona fortemente com area_cadastrada_m2 (rho=+0,817) e moderadamente com quantidade_dependentes (rho=+0,311) e água (rho=+0,611)",
    ),
    ("SINAIS_IMOBILIARIOS", "agua_media_mensal_6m"): (
        "INTEIRO_DISCRETO (int64, R$/mês, degraus de 50 a 400)",
        "IGNORADA_HOJE: não utilizada em src/casa_gemea/",
        "ocupacao_hidrica_estimada = (agua_media_mensal_6m - 0,5 * area_m2) / 35; alerta_alta_pressao_hidraulica = (agua_media_mensal_6m >= 250); valida se 2a residência ou imóvel alugado tem moradores ativos",
        "DANOS_POR_AGUA (2a maior causa de sinistro BB Seguros com 14,6%: mais banheiros e maior volume hidráulico em uso), DESPESAS_EMERGENCIAIS (proxy do número real de moradores) e RC_FAMILIAR (infiltração em vizinhos)",
        "FORTE",
        "Oportunidade imediata ignorada pelo motor atual: tem rho=+0,700 com quantidade_dependentes e rho=+0,497 com area_cadastrada_m2!",
    ),
    ("SINAIS_IMOBILIARIOS", "internet_mensal"): (
        "INTEIRO_DISCRETO (int64, R$/mês, degraus de 100 a 350)",
        "IGNORADA_HOJE: não utilizada em src/casa_gemea/",
        "flag_conectividade_premium = (internet_mensal >= 250) & (compras_eletronicos_36m >= 15000) (indicador de home office / gamers / casa conectada)",
        "DANOS_ELETRICOS e cobertura/argumento de proteção de equipamentos de trabalho/home office (ROUBO_FURTO_ARROMBAMENTO)",
        "FRACA",
        "No gerador sintético foi sorteada quase independentemente (todas as correlações de Spearman em [-0,039; +0,029]); usar apenas combinada com eletrônicos",
    ),
    ("SINAIS_IMOBILIARIOS", "compras_moveis_36m"): (
        "MOEDA_CONTINUO (int64, R$ em 36m)",
        "USADA_NA_DECISAO: compõe conteudo_min e conteudo_max (inferencias.inferir_conteudo), que definem pontos do PRATICO e faixas de conteúdo",
        "share_mobiliario = compras_moveis_36m / (compras_moveis_36m + compras_eletrodomesticos_36m + compras_eletronicos_36m); mobiliario_por_m2 = compras_moveis_36m / area_m2",
        "INCENDIO_RAIO_EXPLOSAO_FUMACA, DANOS_POR_AGUA (30% do conteúdo, pois água estraga marcenaria/estofados) e VENDAVAL_GRANIZO (10% do conteúdo)",
        "FORTE",
        "Forte correlação com renda_mensal (rho=+0,735) no gerador; móveis fixos sofrem menor risco de roubo que portáteis, mas alta perda em incêndio e alagamento/água",
    ),
    ("SINAIS_IMOBILIARIOS", "compras_eletrodomesticos_36m"): (
        "MOEDA_CONTINUO (int64, R$ em 36m)",
        "USADA_NA_DECISAO: compõe conteudo_estimado e eletronicos_eletro_min/max (+1 ponto PRATICO se >= R$ 15 mil e base de DANOS_ELETRICOS)",
        "estoque_linha_branca_clima = max(bens_ponderado_eletrodomestico, 0,7 * compras_eletrodomesticos_36m)",
        "DANOS_ELETRICOS (50% de eletrônicos + eletrodomésticos: geladeira, inverter, ar-condicionado, máquina de lavar) e INCENDIO/DANOS_POR_AGUA",
        "FORTE",
        "Correlaciona com renda_mensal (rho=+0,729) e com compras_moveis_36m (rho=+0,714)",
    ),
    ("SINAIS_IMOBILIARIOS", "compras_eletronicos_36m"): (
        "MOEDA_CONTINUO (int64, R$ em 36m)",
        "USADA_NA_DECISAO: compõe conteudo_estimado e eletronicos_eletro_min/max (+1 ponto PRATICO e base de DANOS_ELETRICOS e ROUBO)",
        "exposicao_portateis_roubo = max(bens_ponderado_eletronico, compras_eletronicos_36m); flag_alta_densidade_eletronica = (compras_eletronicos_36m >= 15000)",
        "ROUBO_FURTO_ARROMBAMENTO (itens de alta liquidez visados em arrombamento, exceto celulares excluídos na CG 6.1) e DANOS_ELETRICOS (TVs, computadores, home theater)",
        "FORTE",
        "Importante transparentar na jornada que celulares e joias são excluídos nas CG (item 6.1), focando a cobertura em TVs, notebooks, som e eletroportáteis",
    ),
    ("SINAIS_IMOBILIARIOS", "gastos_material_construcao_24m"): (
        "MOEDA_CONTINUO (int64, R$ em 24m, 82,1% zeros)",
        "USADA_NA_DECISAO: define alerta_obra (REFORMA_LEVE < 10k, MODERADA 10k-30k, POSSIVEL_OBRA_RELEVANTE >= 30k ou >= 10k + vidraçaria) e ELEGIVEL_CONDICIONADO",
        "intensidade_obra_relativa = gastos_material_construcao_24m / custo_reconstrucao_predio; razao_obra_renda_anual = gastos_material_construcao_24m / (12 * renda_mensal)",
        "Elegibilidade de INCENDIO e pacote estrutural (CG 7.1 x/y excluem imóveis em construção/reforma estrutural); quando reforma concluída ou leve, valoriza benfeitorias (especialmente de inquilino!)",
        "FORTE",
        "Descoberta crítica: nos 461 casos >0, o gasto escala com a renda (rho=+0,819) e não com a área (rho=-0,088)! Limiar fixo de R$ 30 mil penaliza alta renda fazendo acabamento simples; usar razão sobre custo do prédio",
    ),
    ("SINAIS_IMOBILIARIOS", "gastos_vidracaria_24m"): (
        "MOEDA_CONTINUO (int64, R$ em 24m, 90,6% zeros)",
        "USADA_NA_DECISAO: +1 ponto para o plano PRATICO (sinal_vidros), eleva reforma moderada para relevante e fixa piso do máximo de QUEBRA_DE_VIDROS em 1,5x o gasto",
        "densidade_vidros_m2 = gastos_vidracaria_24m / area_m2; flag_envidracamento_especial = (gastos_vidracaria_24m >= 3000) (fechamento de sacada/cortina de vidro/blindex)",
        "QUEBRA_DE_VIDROS (evidência direta de instalação de box, espelhos, sacada envidraçada ou janelas amplas) e VENDAVAL_GRANIZO (esquadrias expostas)",
        "FORTE",
        "Ao contrário de material de construção, entre os 242 casos >0 não depende da renda (rho=+0,017), mas sim da área do imóvel (rho=+0,231): sinal físico puro!",
    ),
    # === BENS_COMPRAS (11) ===
    ("BENS_COMPRAS", "bem_id"): (
        "ID_CHAVE (str)",
        "USADA_SO_CALCULO: contagem de bens vinculados ao imóvel (qtd_bens em carregar.resumir_bens)",
        "qtd_bens_por_imovel = count(bem_id); alerta no LEIA-ME: bem_id se repete entre dev e teste, nunca cruzar bases por ele",
        "Indireto (volume de itens seguráveis no imóvel)",
        "NULA",
        "Armadilha de chave: identificadores BEM_xxxxxx se repetem entre as pastas de desenvolvimento e teste",
    ),
    ("BENS_COMPRAS", "cliente_id"): (
        "ID_CHAVE (str)",
        "IGNORADA_HOJE: resumir_bens() agrupa diretamente por imovel_id_referencia",
        "patrimonio_movel_total_cliente = sum(valor_cadastrado por cliente_id) para comparar com o alocado em cada imóvel quando qtd_imoveis_cliente == 2",
        "Evita dupla contagem de bens portáteis entre 1o e 2o imóvel do mesmo titular",
        "NULA",
        "Identificador pseudonimizado",
    ),
    ("BENS_COMPRAS", "imovel_id_referencia"): (
        "ID_CHAVE (str)",
        "USADA_SO_CALCULO: chave de agregação dos bens para montar a linha do imóvel (carregar.resumir_bens)",
        "concentracao_bens_imovel = bens_valor_cadastrado_imovel / bens_valor_cadastrado_cliente",
        "Aloca o LMI de conteúdo (INCENDIO, ROUBO, DANOS_ELETRICOS, DANOS_POR_AGUA) ao imóvel correto",
        "NULA",
        "Identificador pseudonimizado",
    ),
    ("BENS_COMPRAS", "tipo_bem"): (
        "CATEGORICO_NOMINAL (str, 4 categorias equilibradas ~25%)",
        "USADA_NA_DECISAO: pivotada em carregar.resumir_bens(); ELETRONICO e ELETRODOMESTICO entram em eletronicos_eletro_min/max; ITEM_LAZER e MOVEL entram apenas no total",
        "bens_ponderado_item_lazer e flag_possui_item_lazer_alto = (bens_ponderado_item_lazer >= 5000); flag_home_office_equipado = (bens_ponderado_eletronico >= 10000)",
        "ELETRONICO -> DANOS_ELETRICOS e ROUBO_FURTO_ARROMBAMENTO; ELETRODOMESTICO -> DANOS_ELETRICOS e DANOS_POR_AGUA; MOVEL -> INCENDIO e DANOS_POR_AGUA; ITEM_LAZER -> ROUBO_FURTO_ARROMBAMENTO, RESPONSABILIDADE_CIVIL_FAMILIAR (uso de bicicletas/lazer) e cobertura adicional de Bicicleta/Equipamentos Esportivos",
        "FORTE",
        "Lacuna atual de hiperpersonalização: ITEM_LAZER representa 25,5% dos bens (2.296 itens em dev, mediana R$ 3.300, P90 R$ 14.250) e hoje não gera menção específica na justificativa!",
    ),
    ("BENS_COMPRAS", "valor_cadastrado"): (
        "MOEDA_CONTINUO (int64, R$ por bem)",
        "USADA_NA_DECISAO: soma por imóvel (bens_valor_cadastrado) define o teto conteudo_max da Casa Gêmea",
        "maior_bem_individual = max(valor_cadastrado por imovel); flag_bem_unitario_alto_valor = (max_valor_cadastrado >= 15000) (alerta de sublimite contratual por item)",
        "ROUBO_FURTO_ARROMBAMENTO, DANOS_ELETRICOS e INCENDIO_RAIO_EXPLOSAO_FUMACA (define limite superior da faixa de conteúdo)",
        "FORTE",
        "Soma por imóvel correlaciona fortemente com renda_mensal (rho=+0,76); bens de alto valor individual podem exigir verificação de exclusões (CG 6.1)",
    ),
    ("BENS_COMPRAS", "mesma_uf_imovel"): (
        "BINARIO_SIM_NAO (str)",
        "USADA_SO_CALCULO: embutida na fórmula de probabilidade_bem_no_imovel_referencia (+0,18 quando SIM)",
        "fracao_bens_outra_uf = sum(valor_cadastrado com mesma_uf_imovel=='NAO') / bens_valor_cadastrado (sinal de mudança interestadual ou compra para 2a residência)",
        "Afeta a largura da faixa de conteúdo (INCENDIO e ROUBO_FURTO_ARROMBAMENTO): bens comprados em outra UF (7,3%) têm probabilidade de apenas 0,20 a 0,48 de estarem no imóvel",
        "MEDIA",
        "Quando NAO, mesmo_municipio_imovel é obrigatoriamente NAO (hierarquia geográfica preservada em 100% da base)",
    ),
    ("BENS_COMPRAS", "mesmo_municipio_imovel"): (
        "BINARIO_SIM_NAO (str)",
        "USADA_SO_CALCULO: embutida na fórmula de probabilidade_bem_no_imovel_referencia (+0,28 quando SIM)",
        "fracao_bens_outro_municipio = sum(valor_cadastrado com mesmo_municipio_imovel=='NAO') / bens_valor_cadastrado",
        "Controla a confiança do LMI de ROUBO_FURTO_ARROMBAMENTO e DANOS_ELETRICOS (26,5% dos bens foram adquiridos fora do município do imóvel)",
        "MEDIA",
        "Principal fator geográfico da probabilidade do bem estar no imóvel (+28 pontos percentuais na fórmula do gerador)",
    ),
    ("BENS_COMPRAS", "bem_financiado_pelo_banco"): (
        "BINARIO_SIM_NAO (str)",
        "USADA_SO_CALCULO: embutida na fórmula de probabilidade_bem_no_imovel_referencia (+0,18 quando SIM)",
        "valor_bens_financiados_banco = sum(valor_cadastrado onde bem_financiado_pelo_banco=='SIM'); comprova existência e nota fiscal do bem junto ao banco",
        "Aumenta a confiança da estimativa de DANOS_ELETRICOS e ROUBO_FURTO_ARROMBAMENTO (bem rastreado com endereço de entrega e garantia bancária)",
        "MEDIA",
        "27,9% dos bens são financiados pelo banco; eleva a probabilidade máxima para 0,94 quando no mesmo município",
    ),
    ("BENS_COMPRAS", "probabilidade_bem_no_imovel_referencia"): (
        "PROBABILIDADE_FLOAT (float64, 9 valores entre 0,20 e 0,94)",
        "USADA_SO_CALCULO: multiplica valor_cadastrado para gerar valor_bem_ponderado_referencia",
        "Fórmula exata descoberta no gerador: p = 0,30 + 0,18*[mesma_uf] + 0,28*[mesmo_municipio] + 0,18*[bem_financiado] - 0,10*[ruido_binario_22pct]",
        "Dimensiona o piso (conteudo_min) de INCENDIO_RAIO_EXPLOSAO_FUMACA, DANOS_POR_AGUA, DANOS_ELETRICOS e ROUBO_FURTO_ARROMBAMENTO",
        "FORTE",
        "Contém componente aleatório sintético (-0,10 em ~22% dos itens com mesmas flags); não superinterpretar diferenças de 0,10 entre bens idênticos",
    ),
    ("BENS_COMPRAS", "nivel_confianca_vinculo"): (
        "CATEGORICO_ORDINAL (str, ALTA/MEDIA/BAIXA)",
        "USADA_NA_DECISAO: carregar.resumir_bens() conta bens_qtd_vinculo_baixo; se > 50% dos bens do imóvel são BAIXA, conteudo_confianca cai para BAIXA (A_CONFIRMAR)",
        "Regra determinística exata do gerador: ALTA se prob >= 0,76 (mesmo município, exceto prob=0,66), MEDIA se prob in {0,56, 0,66}, BAIXA se prob <= 0,48 (outro município e não financiado)",
        "Aciona pergunta de confirmação do valor de conteúdo quando muda o plano (PRATICO vs ESSENCIAL) ou alarga a faixa de INCENDIO",
        "MEDIA",
        "100% derivada de probabilidade_bem_no_imovel_referencia; 21,2% dos bens têm confiança BAIXA",
    ),
    ("BENS_COMPRAS", "valor_bem_ponderado_referencia"): (
        "MOEDA_CONTINUO (int64, R$)",
        "USADA_NA_DECISAO: soma por imóvel e por tipo_bem define conteudo_min e eletronicos_eletro_min (inferencias.inferir_conteudo)",
        "soma_ponderada_por_categoria = pivot_table(valor_bem_ponderado_referencia por tipo_bem); separar explicitamente bens_ponderado_item_lazer e bens_ponderado_movel nas regras de texto",
        "Base direta do LMI mínimo de DANOS_ELETRICOS, ROUBO_FURTO_ARROMBAMENTO, DANOS_POR_AGUA e INCENDIO_RAIO_EXPLOSAO_FUMACA",
        "FORTE",
        "Vale exatamente round(valor_cadastrado * probabilidade_bem_no_imovel_referencia, -1) em 100% das 8.988 linhas de dev e 494 de teste",
    ),
    # === TERRITORIO (10) ===
    ("TERRITORIO", "territorio_id"): (
        "ID_CHAVE (str)",
        "USADA_SO_CALCULO: chave primária para junção com enderecos_imoveis",
        "Ver ENDERECOS_IMOVEIS.territorio_id",
        "Nenhuma (identificador)",
        "NULA",
        "Identificador pseudonimizado",
    ),
    ("TERRITORIO", "codigo_ibge_municipio"): (
        "INTEIRO_CATEGORICO (int64, 10 códigos)",
        "IGNORADA_HOJE: já lida de enderecos_imoveis (100% idêntica)",
        "Duplicata exata de ENDERECOS_IMOVEIS.codigo_ibge_municipio",
        "Ver ENDERECOS_IMOVEIS.codigo_ibge_municipio",
        "NULA",
        "Coluna duplicada entre enderecos_imoveis e territorio (100% de concordância)",
    ),
    ("TERRITORIO", "municipio_real"): (
        "CATEGORICO_NOMINAL (str, 10 capitais)",
        "IGNORADA_HOJE: já lida de enderecos_imoveis (100% idêntica)",
        "Duplicata exata de ENDERECOS_IMOVEIS.municipio_real",
        "Ver ENDERECOS_IMOVEIS.municipio_real",
        "NULA",
        "Coluna duplicada entre enderecos_imoveis e territorio",
    ),
    ("TERRITORIO", "uf_real"): (
        "CATEGORICO_NOMINAL (str, 10 UFs)",
        "IGNORADA_HOJE: já lida de enderecos_imoveis (100% idêntica)",
        "Duplicata exata de ENDERECOS_IMOVEIS.uf_real",
        "Ver ENDERECOS_IMOVEIS.uf_real",
        "NULA",
        "Coluna duplicada entre enderecos_imoveis e territorio",
    ),
    ("TERRITORIO", "cep_agregado"): (
        "CATEGORICO_NOMINAL (str, 389 códigos)",
        "IGNORADA_HOJE: já presente em enderecos_imoveis (100% idêntica)",
        "Duplicata exata de ENDERECOS_IMOVEIS.cep_agregado",
        "Ver ENDERECOS_IMOVEIS.cep_agregado",
        "NULA",
        "Coluna duplicada entre enderecos_imoveis e territorio",
    ),
    ("TERRITORIO", "latitude_aproximada"): (
        "COORDENADA_FLOAT (float64, graus decimais)",
        "IGNORADA_HOJE: carregada em montar_tabela_imoveis(), mas descartada em COLUNAS_CASA_GEMEA",
        "distancia_centro_capital_km = haversine(lat, lon, lat_capital, lon_capital); na base sintética é apenas centroide da capital + ruído gaussiano (dp ~0,03 grau ~3 km)",
        "Em produção (com geocodificação real), cruza com mancha de inundação (DANOS_POR_AGUA / VENDAVAL_GRANIZO) e incidência de raios (DANOS_ELETRICOS)",
        "FRACA",
        "Observação explícita na tabela: 'COORDENADA PERTURBADA; NAO REPRESENTA DOMICILIO REAL'; proibido usar para inferir micro-risco real na base sintética",
    ),
    ("TERRITORIO", "longitude_aproximada"): (
        "COORDENADA_FLOAT (float64, graus decimais)",
        "IGNORADA_HOJE: carregada em montar_tabela_imoveis(), mas descartada em COLUNAS_CASA_GEMEA",
        "Par de latitude_aproximada (ruído isotrópico ao redor do centro de cada uma das 10 capitais)",
        "Mesmo papel de latitude_aproximada (enriquecimento climático/topográfico apenas quando coordenada for real)",
        "FRACA",
        "Coordenada sintética perturbada para preservação de privacidade territorial",
    ),
    ("TERRITORIO", "chave_enriquecimento_publico"): (
        "CONSTANTE_METADADO (str, 1 valor)",
        "IGNORADA_HOJE: metadado descritivo constante",
        "Nenhuma (100% igual a 'CODIGO_IBGE+COORDENADA_APROXIMADA')",
        "Nenhuma",
        "NULA",
        "Variância zero (constante documental)",
    ),
    ("TERRITORIO", "observacao_privacidade"): (
        "CONSTANTE_METADADO (str, 1 valor)",
        "IGNORADA_HOJE: metadado descritivo constante",
        "Nenhuma (100% igual a 'COORDENADA PERTURBADA; NAO REPRESENTA DOMICILIO REAL')",
        "Nenhuma",
        "NULA",
        "Variância zero; documenta o guardrail de não fazer micro-georreferenciamento na base sintética",
    ),
    ("TERRITORIO", "orientacao_enriquecimento"): (
        "CONSTANTE_METADADO (str, 1 valor)",
        "IGNORADA_HOJE: metadado descritivo constante",
        "Nenhuma (100% igual a 'INDICADORES TERRITORIAIS NAO FORNECIDOS; ENRIQUECIMENTO EXTERNO OPCIONAL')",
        "Nenhuma",
        "NULA",
        "Variância zero; autoriza o uso do CUB por UF (Sinduscon) adotado pelo projeto",
    ),
}


# --------------------------------------------------- calculo de metricas por coluna
def _resumo_e_deriva(s_dev: pd.Series, s_tst: pd.Series, nome_col: str) -> tuple[str, str, str, str]:
    """Devolve (pct_nulos_str, cardinalidade_str, resumo_str, deriva_str)."""
    na_dev = 100.0 * s_dev.isna().mean()
    na_tst = 100.0 * s_tst.isna().mean()

    if s_dev.dtype == "object":
        nd_dev = 100.0 * (s_dev == "NAO_DISPONIVEL").mean()
        nd_tst = 100.0 * (s_tst == "NAO_DISPONIVEL").mean()
        if nd_dev > 0 or nd_tst > 0:
            pct_nulos = f"0,0% NaN ({br(nd_dev, 1)}% dev / {br(nd_tst, 1)}% teste NAO_DISPONIVEL)"
        else:
            pct_nulos = f"{br(na_dev, 1)}% dev / {br(na_tst, 1)}% teste"
    else:
        z_dev = 100.0 * (s_dev == 0).mean()
        z_tst = 100.0 * (s_tst == 0).mean()
        if nome_col == "area_cadastrada_m2":
            pct_nulos = f"0,0% NaN ({br(z_dev, 1)}% dev / {br(z_tst, 1)}% teste com 0 = sem cadastro)"
        elif z_dev >= 5.0:
            pct_nulos = f"0,0% NaN ({br(z_dev, 1)}% dev / {br(z_tst, 1)}% teste iguais a zero)"
        else:
            pct_nulos = f"{br(na_dev, 1)}% dev / {br(na_tst, 1)}% teste"

    card_d = int(s_dev.nunique(dropna=True))
    card_t = int(s_tst.nunique(dropna=True))
    cardinalidade = f"{card_d} (dev) / {card_t} (teste)"

    eh_id = nome_col.endswith("_id") or nome_col == "imovel_id_referencia"
    if eh_id:
        resumo = f"Chave identificadora única ({card_d} valores em dev, {card_t} em teste)"
        deriva = "NAO_SE_APLICA (identificador único por base)"
        return pct_nulos, cardinalidade, resumo, deriva

    if s_dev.dtype == "object" or card_d <= 10:
        vc_d = s_dev.value_counts(normalize=True)
        vc_t = s_tst.value_counts(normalize=True)
        top_cats = ", ".join(f"{k}: {br(100 * v, 1)}%" for k, v in vc_d.head(4).items())
        if len(vc_d) > 4:
            top_cats += f" (+{len(vc_d) - 4} cats)"
        resumo = top_cats

        todas_cats = sorted(set(vc_d.index).union(set(vc_t.index)), key=str)
        diffs = [abs(vc_d.get(c, 0.0) - vc_t.get(c, 0.0)) for c in todas_cats]
        tvd = 0.5 * sum(diffs)
        max_c = todas_cats[int(np.argmax(diffs))]
        max_diff_pp = 100.0 * max(diffs)
        status = "ESTAVEL" if tvd < 0.06 else ("LEVE" if tvd < 0.12 else "MODERADA")
        deriva = f"{status}: TVD={br(100 * tvd, 1)} pp (maior diff em '{max_c}': {br(100 * vc_d.get(max_c, 0.0), 1)}% dev vs {br(100 * vc_t.get(max_c, 0.0), 1)}% teste, {br(max_diff_pp, 1)} pp)"
    else:
        q_d = s_dev.quantile([0.0, 0.5, 0.9, 1.0]).to_dict()
        casas = 2 if s_dev.dtype == "float64" else 0
        resumo = f"min={br(q_d[0.0], casas)}, med={br(q_d[0.5], casas)}, p90={br(q_d[0.9], casas)}, max={br(q_d[1.0], casas)}"
        if (s_dev == 0).mean() > 0.20:
            pos_d = s_dev[s_dev > 0]
            if len(pos_d) > 0:
                resumo += f" (entre >0, n={len(pos_d)}: med={br(float(pos_d.median()), casas)}, p90={br(float(pos_d.quantile(0.9)), casas)})"

        dp_d = float(s_dev.std())
        smd = float((s_tst.mean() - s_dev.mean()) / dp_d) if dp_d > 1e-9 else 0.0
        status = "ESTAVEL" if abs(smd) < 0.15 else ("LEVE" if abs(smd) < 0.25 else "MODERADA")
        deriva = f"{status}: SMD={smd:+.2f} (mediana {br(float(s_dev.median()), casas)} dev vs {br(float(s_tst.median()), casas)} teste; média {br(float(s_dev.mean()), 1)} vs {br(float(s_tst.mean()), 1)})"

    return pct_nulos, cardinalidade, resumo, deriva


def _associacoes_coluna(tabela_up: str, col: str, full_d: pd.DataFrame, bc_full: pd.DataFrame) -> str:
    """Calcula associações com plano_recomendado, semaforo, conteudo_estimado, area_m2 e renda_mensal."""
    if col.endswith("_id") or col == "imovel_id_referencia":
        if col == "cliente_id":
            return "Agrupa 2.200 clientes em 2.578 imóveis (378 clientes com 2 imóveis = 29,3% dos imóveis)"
        return "Identificador primário/estrangeiro (cardinalidade 1:1 com a entidade)"

    df_ref = bc_full if tabela_up == "BENS_COMPRAS" else full_d
    if col not in df_ref.columns:
        return "Sem associação (metadado constante em 100% das linhas)"
    s = df_ref[col]
    if s.nunique(dropna=True) <= 1:
        return "Sem associação (coluna constante em 100% das linhas)"

    partes = []
    if s.dtype == "object" or s.nunique() <= 4:
        v_plano = cramers_v_corrigido(s, df_ref["plano_recomendado"])
        v_sem = cramers_v_corrigido(s, df_ref["semaforo"])
        med_cont = df_ref.groupby(col)["conteudo_estimado"].median()
        raz_cont = float(med_cont.max() / max(med_cont.min(), 1.0))
        med_area = df_ref.groupby(col)["area_m2"].median()
        raz_area = float(med_area.max() / max(med_area.min(), 1.0))
        partes.append(f"Plano V={br(v_plano, 2)}")
        partes.append(f"Semáforo V={br(v_sem, 2)}")
        partes.append(f"Conteúdo razão med={br(raz_cont, 2)}x")
        partes.append(f"Área razão med={br(raz_area, 2)}x")
    else:
        num = s.astype(float)
        rho_cont = float(num.corr(df_ref["conteudo_estimado"], method="spearman"))
        rho_area = float(num.corr(df_ref["area_m2"], method="spearman"))
        rho_renda = float(num.corr(df_ref["renda_mensal"], method="spearman"))
        v_plano = cramers_v_corrigido(pd.qcut(num.rank(method="first"), 4, labels=False), df_ref["plano_recomendado"])
        partes.append(f"Plano V={br(v_plano, 2)}")
        partes.append(f"Spearman Conteúdo={rho_cont:+.2f}")
        partes.append(f"Área={rho_area:+.2f}")
        partes.append(f"Renda={rho_renda:+.2f}")

        if (num == 0).mean() > 0.20:
            pos = df_ref[num > 0]
            pos_area = pos[pos["area_cadastrada_m2"] > 0]
            if len(pos) >= 30:
                r_ren_pos = float(pos[col].corr(pos["renda_mensal"], method="spearman"))
                r_are_pos = float(pos_area[col].corr(pos_area["area_cadastrada_m2"], method="spearman")) if len(pos_area) >= 20 else 0.0
                partes.append(f"[nos >0: Renda={r_ren_pos:+.2f}, ÁreaReal={r_are_pos:+.2f}]")

    return "; ".join(partes)


def gerar_tabela_analise_colunas(
    dev: dict[str, pd.DataFrame],
    tst: dict[str, pd.DataFrame],
    full_d: pd.DataFrame,
    bc_full: pd.DataFrame,
) -> pd.DataFrame:
    linhas = []
    for t in TABELAS_DADOS:
        t_up = t.upper()
        df_d, df_t = dev[t], tst[t]
        for col in df_d.columns:
            chave = (t_up, col)
            if chave not in META_COLUNAS:
                raise KeyError(f"Coluna sem metadados: {chave}")
            tipo_sem, uso_atual, ideias, sinal_cob, forca, risco = META_COLUNAS[chave]
            pct_nulos, card, resumo, deriva = _resumo_e_deriva(df_d[col], df_t[col], col)
            assoc = _associacoes_coluna(t_up, col, full_d, bc_full)
            linhas.append({
                "tabela": t_up,
                "campo": col,
                "tipo": tipo_sem,
                "pct_nulos": pct_nulos,
                "cardinalidade": card,
                "resumo": resumo,
                "deriva_dev_teste": deriva,
                "uso_atual": uso_atual,
                "associacoes_principais": assoc,
                "ideias_de_feature": ideias,
                "sinal_para_cobertura": sinal_cob,
                "forca_do_sinal": forca,
                "risco": risco,
            })
    return pd.DataFrame(linhas)


# --------------------------------------------------- segmentacao (K-means e Arquetipos)
def analisar_kmeans(full_d: pd.DataFrame) -> pd.DataFrame:
    cols_num = [
        "idade", "renda_mensal", "indice_maturidade_digital", "frequencia_acesso_app_90d",
        "quantidade_dependentes", "qtd_produtos_seguridade", "area_m2", "conteudo_estimado",
        "valor_aluguel_recorrente", "valor_medio_credito_recorrente", "parcela_financiamento_imobiliario",
        "pagamento_condominio_mensal", "pagamento_iptu_anual", "energia_media_mensal_6m",
        "agua_media_mensal_6m", "internet_mensal", "gastos_material_construcao_24m", "gastos_vidracaria_24m",
    ]
    cols_cat = ["tipo_imovel", "vinculo", "uso_imovel", "possui_pet_informado", "usuario_app", "possui_seguro_residencial"]
    X_completo = StandardScaler().fit_transform(pd.get_dummies(full_d[cols_num + cols_cat], drop_first=True, dtype=float))
    X_continuo = StandardScaler().fit_transform(full_d[cols_num].fillna(0))

    linhas = []
    for k in range(3, 9):
        km_c = KMeans(n_clusters=k, random_state=SEMENTE, n_init=20).fit(X_completo)
        sil_c = float(silhouette_score(X_completo, km_c.labels_))
        aris_c = [
            adjusted_rand_score(km_c.labels_, KMeans(n_clusters=k, random_state=s, n_init=20).fit(X_completo).labels_)
            for s in range(1, 6)
        ]
        km_n = KMeans(n_clusters=k, random_state=SEMENTE, n_init=20).fit(X_continuo)
        sil_n = float(silhouette_score(X_continuo, km_n.labels_))
        aris_n = [
            adjusted_rand_score(km_n.labels_, KMeans(n_clusters=k, random_state=s, n_init=20).fit(X_continuo).labels_)
            for s in range(1, 6)
        ]
        tamanhos = ", ".join(map(str, sorted(np.bincount(km_c.labels_).tolist(), reverse=True)))
        linhas.append({
            "k": k,
            "Silhueta (base completa)": br(sil_c, 3),
            "Estabilidade ARI (completa)": br(float(np.mean(aris_c)), 3),
            "Silhueta (só contínuas)": br(sil_n, 3),
            "Estabilidade ARI (contínuas)": br(float(np.mean(aris_n)), 3),
            "Tamanhos dos grupos (dev, n=2578)": tamanhos,
        })
    return pd.DataFrame(linhas)


def classificar_arquetipos(df: pd.DataFrame) -> pd.Series:
    """Partição exaustiva e mutuamente exclusiva em 7 arquétipos de hiperpersonalização."""
    conds = [
        df["alerta_obra"].isin(["POSSIVEL_OBRA_RELEVANTE", "REFORMA_MODERADA"]),
        df["vinculo"] == "PROPRIETARIO_LOCADOR",
        df["vinculo"] == "INQUILINO",
        df["uso_imovel"] == "TEMPORADA_OU_SEGUNDA_RESIDENCIA",
        df["vinculo"] == "PROPRIETARIO_FINANCIADO",
        (df["vinculo"] == "PROPRIETARIO_QUITADO")
        & ((df["quantidade_dependentes"] > 0) | (df["possui_pet_informado"] == "SIM")),
    ]
    nomes = [
        "1. Imóvel em Reforma ou Obra Relevante",
        "2. Investidor Locador (Proteção de Renda e Prédio)",
        "3. Inquilino Urbano (Conteúdo, Aluguel e RC)",
        "4. Segunda Residência / Veraneio",
        "5. Mutuário Financiado (Complemento DFI + Conteúdo)",
        "6. Família ou Tutor de Pet em Imóvel Quitado",
    ]
    return pd.Series(
        np.select(conds, nomes, default="7. Proprietário Quitado Solo / Casal sem Dependentes"),
        index=df.index,
    )


def resumir_arquetipos(full_d: pd.DataFrame, full_t: pd.DataFrame) -> pd.DataFrame:
    d_arq = classificar_arquetipos(full_d)
    t_arq = classificar_arquetipos(full_t)
    foco_coberturas = {
        "1. Imóvel em Reforma ou Obra Relevante": "Validar elegibilidade (CG 7.1 x/y); após obra: QUEBRA_DE_VIDROS, DANOS_ELETRICOS e INCENDIO com benfeitorias",
        "2. Investidor Locador (Proteção de Renda e Prédio)": "TOTAL: PERDA_PAGAMENTO_ALUGUEL (3 a 6 meses de renda) + INCENDIO (100% prédio, 20% conteúdo, CG 6.1 r)",
        "3. Inquilino Urbano (Conteúdo, Aluguel e RC)": "TOTAL: PERDA_PAGAMENTO_ALUGUEL + ROUBO_FURTO + DANOS_ELETRICOS + RC_FAMILIAR (prédio só 3%-10% benfeitorias)",
        "4. Segunda Residência / Veraneio": "PRATICO ou ESSENCIAL: VENDAVAL_GRANIZO + DANOS_POR_AGUA + DANOS_ELETRICOS (alerta: sem ROUBO se desocupado, CG 2.1 c)",
        "5. Mutuário Financiado (Complemento DFI + Conteúdo)": "PRATICO (+ TOTAL se família/pet): ROUBO_FURTO + DANOS_ELETRICOS + QUEBRA_DE_VIDROS (prédio em 2o risco sobre DFI, CG 15.2)",
        "6. Família ou Tutor de Pet em Imóvel Quitado": "TOTAL ou PRATICO+RC: INCENDIO (100% casa) + RC_FAMILIAR (pet/filhos/vizinhos) + DESPESAS_EMERGENCIAIS + DANOS_POR_AGUA",
        "7. Proprietário Quitado Solo / Casal sem Dependentes": "PRATICO (se conteúdo >= R$ 20 mil / casa) ou ESSENCIAL (compacto): foco em ROUBO_FURTO, DANOS_ELETRICOS e QUEBRA_DE_VIDROS",
    }
    linhas = []
    for nome in foco_coberturas:
        sub_d = full_d[d_arq == nome]
        sub_t = full_t[t_arq == nome]
        linhas.append({
            "Arquétipo": nome,
            "Dev n (%)": f"{len(sub_d)} ({br(100 * len(sub_d) / len(full_d), 1)}%)",
            "Teste n (%)": f"{len(sub_t)} ({br(100 * len(sub_t) / len(full_t), 1)}%)",
            "Renda med (R$)": br(float(sub_d["renda_mensal"].median()), 0),
            "Conteúdo med (R$)": br(float(sub_d["conteudo_estimado"].median()), 0),
            "Plano sugerido e hiperpersonalização de coberturas": foco_coberturas[nome],
        })
    return pd.DataFrame(linhas)


# --------------------------------------------------- geracao do relatorio Markdown
def escrever_relatorio(
    df_colunas: pd.DataFrame,
    df_km: pd.DataFrame,
    df_arq: pd.DataFrame,
    full_d: pd.DataFrame,
    full_t: pd.DataFrame,
    dev: dict[str, pd.DataFrame],
    tempo: float,
) -> Path:
    bc_d = dev["bens_compras"]
    resumo_bens_tipo = (
        bc_d.groupby("tipo_bem")
        .agg(
            itens=("bem_id", "count"),
            pct=("bem_id", lambda s: f"{br(100 * len(s) / len(bc_d), 1)}%"),
            mediana=("valor_cadastrado", lambda s: br(float(s.median()), 0)),
            p90=("valor_cadastrado", lambda s: br(float(s.quantile(0.9)), 0)),
            uso_motor=("tipo_bem", lambda s: "Total + Eletrônicos/Eletro (Danos Elétricos e Prático)"
                       if s.iloc[0] in ("ELETRONICO", "ELETRODOMESTICO")
                       else "Apenas soma geral de conteúdo (sem regra específica hoje)"),
        )
        .reset_index()
        .rename(columns={
            "tipo_bem": "Categoria (tipo_bem)",
            "itens": "Itens (dev)",
            "pct": "% dos bens",
            "mediana": "Valor mediano (R$)",
            "p90": "P90 (R$)",
            "uso_motor": "Tratamento atual no motor",
        })
    )

    full_d_copy = full_d.copy()
    full_d_copy["eh_casa"] = full_d_copy["tipo_imovel"].str.startswith("CASA")
    full_d_copy["iptu_m2"] = full_d_copy["pagamento_iptu_anual"] / full_d_copy["area_m2"]
    terr_df = (
        full_d_copy.groupby(["municipio_real", "uf_real"])
        .agg(
            imoveis=("imovel_id", "count"),
            area_med=("area_m2", lambda s: br(float(s.median()), 0)),
            iptu_m2=("iptu_m2", lambda s: br(float(s.median()), 1)),
            cond_med=("pagamento_condominio_mensal", lambda s: br(float(s[s > 0].median()), 0)),
            aluguel_med=("valor_aluguel_recorrente", lambda s: br(float(s[s > 0].median()), 0)),
            renda_med=("renda_mensal", lambda s: br(float(s.median()), 0)),
            pct_total=("plano_recomendado", lambda s: f"{br(100 * (s == 'TOTAL').mean(), 1)}%"),
        )
        .reset_index()
        .rename(columns={
            "municipio_real": "Município",
            "uf_real": "UF",
            "imoveis": "Imóveis",
            "area_med": "Área med (m²)",
            "iptu_m2": "IPTU/m² med (R$)",
            "cond_med": "Condomínio >0 med (R$)",
            "aluguel_med": "Aluguel >0 med (R$)",
            "renda_med": "Renda med (R$)",
            "pct_total": "% Plano Total",
        })
    )

    top15 = pd.DataFrame([
        ("1", "SINAIS_IMOBILIARIOS", "agua_media_mensal_6m", "IGNORADA_HOJE", "Spearman dep=+0,70; área=+0,50", "ocupacao_hidrica = (agua - 0,5*area)/35; alerta_hidraulico = (agua >= 250)", "DANOS_POR_AGUA, DESPESAS_EMERGENCIAIS e validação de ocupação real"),
        ("2", "CLIENTES", "possui_seguro_residencial", "IGNORADA_HOJE", "16,6% SIM (dev) / 22,5% (teste)", "modo_jornada = 'UPGRADE_ENDOSSO' se SIM senão 'NOVA_APOLICE'", "Muda abordagem inteira: diagnóstico de subseguro/lacunas na apólice vigente"),
        ("3", "BENS_COMPRAS", "tipo_bem (ITEM_LAZER / MOVEL)", "PARCIAL (só total)", "25,5% ITEM_LAZER (med R$ 3.300, P90 R$ 14.250)", "bens_ponderado_item_lazer; flag_lazer_bike = (item_lazer >= 5000)", "ROUBO_FURTO_ARROMBAMENTO, RC_FAMILIAR e cobertura adicional de Bicicleta/Lazer"),
        ("4", "CLIENTES", "renda_mensal", "PROIBIDA_HOJE", "Spearman conteúdo=+0,83; aluguel=+0,79; obra>0=+0,82", "comprometimento_moradia = (aluguel + financ + cond) / renda_mensal", "PERDA_PAGAMENTO_ALUGUEL e DESPESAS_EMERGENCIAIS quando comprometimento >= 30%"),
        ("5", "SINAIS_IMOBILIARIOS", "pagamento_condominio_mensal", "USADA_NA_DECISAO", "Nos >0 (n=983): Spearman área=+0,82; Superior=R$ 10/m²", "condominio_m2 = condominio / area_m2; area_impl_cond = condominio / 6,85", "Melhora estimativa de área/padrão em condomínios e puxa RC_FAMILIAR (vizinhos)"),
        ("6", "SINAIS_IMOBILIARIOS", "valor_medio_credito_recorrente", "USADA_SO_CALCULO", "Nos >0 (n=241): Spearman área=+0,90; renda=+0,02", "area_impl_aluguel_locador = credito_recorrente / aluguel_m2_cidade", "PERDA_PAGAMENTO_ALUGUEL do locador e validação cruzada da área do imóvel"),
        ("7", "SINAIS_IMOBILIARIOS", "gastos_material_construcao_24m", "USADA_NA_DECISAO", "Nos >0 (n=461): Spearman renda=+0,82; área=-0,09", "intensidade_obra = gasto_obra / custo_reconstrucao_predio", "Evita falso positivo de obra estrutural em alta renda; dimensiona benfeitorias"),
        ("8", "CLIENTES", "qtd_produtos_seguridade", "IGNORADA_HOJE", "59,3% têm >=1 produto; 28,1% têm >=2", "tier_relacionamento_seguridade (0, 1, 2+); flag_conflito_apolice", "Define propensão a pacote completo (TOTAL) e argumentação de cross-sell/combo"),
        ("9", "CLIENTES", "frequencia_acesso_app_90d", "IGNORADA_HOJE", "Spearman maturidade=+0,80; máx=161 acessos", "engajamento_app = freq_90d / 90; elegivel_ocb_real = (usuario_app=='SIM' & freq>=30)", "Filtra falsos usuários de app no One Click Buy e ativa gatilho contextual in-app"),
        ("10", "CLIENTES", "indice_maturidade_digital", "IGNORADA_HOJE", "Corte exato: >=35 equivale a 100% de usuario_app=SIM", "complexidade_jornada = 'EXPRESS_1CLICK' (>=70), 'GUIADA' (35-69), 'HUMANA' (<35)", "Personaliza profundidade do texto explicativo e canal de fechamento"),
        ("11", "SINAIS_IMOBILIARIOS", "energia_media_mensal_6m", "USADA_SO_CALCULO", "Spearman área=+0,83; água=+0,61; dep=+0,31", "intensidade_eletrica_m2 = energia / area_m2 (sinal de climatização/carga)", "DANOS_ELETRICOS (53,3% dos sinistros BB Seguros) e estimativa de área"),
        ("12", "SINAIS_IMOBILIARIOS", "gastos_vidracaria_24m", "USADA_NA_DECISAO", "Nos >0 (n=242): independe de renda (+0,02), sobe c/ área (+0,23)", "densidade_vidros_m2 = vidracaria / area_m2; piso de LMI = 1,5x gasto", "QUEBRA_DE_VIDROS (sinal físico puro de envidraçamento de sacada/blindex/espelhos)"),
        ("13", "CLIENTES", "quantidade_dependentes", "USADA_NA_DECISAO", "Plano V=0,29; Spearman água=+0,70; pontos_total=+0,39", "tamanho_familia = 1 + dependentes; escala RC (+R$ 5k-10k/dep) e Despesas Emerg.", "RESPONSABILIDADE_CIVIL_FAMILIAR e DESPESAS_EMERGENCIAIS"),
        ("14", "CLIENTES", "possui_pet_informado", "USADA_NA_DECISAO", "35,0% SIM (dev) / 37,5% (teste); Plano V=0,43", "interacao_pet_condominio = (pet=='SIM' & condominio>0)", "RESPONSABILIDADE_CIVIL_FAMILIAR (+R$ 10k-30k LMI) e assistência veterinária/pet"),
        ("15", "BENS_COMPRAS", "probabilidade_bem_no_imovel_referencia", "USADA_SO_CALCULO", "9 degraus (0,20 a 0,94) derivados de UF, município e financ.", "razao_incerteza_conteudo = bens_valor_cadastrado / bens_valor_ponderado", "Controla largura da faixa de ROUBO_FURTO e DANOS_ELETRICOS e pergunta de bens"),
    ], columns=["#", "Tabela", "Coluna", "Uso atual", "Associação principal", "Feature derivada (fórmula)", "Ganho para hiperpersonalização"])

    sinal_cob = pd.DataFrame([
        ("pagamento_iptu_anual + energia_media_mensal_6m + uf_real + padrao_construtivo", "INCENDIO_RAIO_EXPLOSAO_FUMACA (Fixa: todos)", "Positiva (+)", "FORTE", "Dimensiona reconstrução do prédio (área x CUB da UF x fator Sinduscon x interesse segurável) + conteúdo"),
        ("agua_media_mensal_6m >= R$ 200 + compras_moveis_36m", "DANOS_POR_AGUA (Fixa: todos) + Vazamento de Tubulações (Adicional)", "Positiva (+)", "FORTE", "2ª maior causa de sinistro BB (14,6%); alto consumo de água indica mais banheiros/prumadas hidráulicas e móveis vulneráveis"),
        ("possui_termo_casa == SIM + gastos_vidracaria_24m > 0", "VENDAVAL_GRANIZO e IMPACTO_VEICULOS (Fixas: todos)", "Positiva (+)", "FORTE", "Casas têm telhado, portão, muro e fachada diretamente expostos (11,5% dos sinistros BB são climáticos)"),
        ("compras_eletronicos_36m + compras_eletrodomesticos_36m + energia_media_mensal_6m / area_m2", "DANOS_ELETRICOS (Fixa: todos) + Equipamentos Portáteis/Home Office (Adicional)", "Positiva (+)", "FORTE", "1ª causa de sinistro BB (53,3%); protege TVs, computadores, linha branca inverter e ar-condicionado contra surtos"),
        ("bens_valor_ponderado >= R$ 10 mil + tipo_bem in (ELETRONICO, ITEM_LAZER) + eh_casa", "ROUBO_FURTO_ARROMBAMENTO (Fixa: Prático/Total; Adicional recomendada no Essencial)", "Positiva (+) se ocupado; Negativa (-) se desocupado", "FORTE", "Protege bens portáteis e de lazer; se 2ª residência desocupada, alertar exclusão contratual (CG Roubo 2.1 c)"),
        ("tipo_bem == ITEM_LAZER (soma >= R$ 5 mil)", "Subtração de Bicicleta / Equipamentos Esportivos (Adicional hiperpersonalizada)", "Positiva (+)", "MEDIA", "25,5% dos bens cadastrados são ITEM_LAZER (mediana R$ 3.300, P90 R$ 14.250), hoje sem destaque específico no texto"),
        ("gastos_vidracaria_24m > 0 + area_m2 + pagamento_condominio_mensal > 0", "QUEBRA_DE_VIDROS (Fixa: Prático/Total; Adicional recomendada no Essencial)", "Positiva (+)", "FORTE", "Gasto recente em vidraçaria comprova instalação de cortina de vidro, box, espelhos ou tampos (LMI máx >= 1,5x gasto)"),
        ("possui_pet_informado == SIM + quantidade_dependentes > 0 + tipo_imovel == APARTAMENTO", "RESPONSABILIDADE_CIVIL_FAMILIAR (Fixa: Total; Adicional recomendada no Prático/Essencial)", "Positiva (+)", "FORTE", "Cobre mordida/dano de pet (CG 1.1 c), atos de filhos/empregados (1.1 b) e vazamento/infiltração no apto vizinho (1.1 e)"),
        ("pagamento_aluguel_recorrente == SIM ou credito_recorrente_compativel_aluguel == SIM ou comprometimento_moradia >= 30%", "PERDA_PAGAMENTO_ALUGUEL (Fixa: Total; Adicional crítica para Inquilino/Locador/Alto Comprometimento)", "Positiva (+)", "FORTE", "Protege 3 a 6 meses de aluguel pago pelo inquilino ou recebido pelo locador (até R$ 18 mil medianos em risco)"),
        ("quantidade_dependentes >= 1 + agua_media_mensal_6m >= R$ 150 + comprometimento_moradia >= 30%", "DESPESAS_EMERGENCIAIS (Fixa: Total; Adicional para famílias)", "Positiva (+)", "MEDIA", "Paga 10% nas primeiras 48h + 3% do LMI ao dia para hospedagem, alimentação e transporte da família (CG 1.3)"),
        ("gastos_material_construcao_24m > 0 + vinculo == INQUILINO", "Benfeitorias no Prédio (INCENDIO/AGUA) + Assistência Pequenos Reparos", "Positiva (+) se leve; Bloqueio se estrutural", "MEDIA", "Inquilino com gasto < R$ 30 mil fez benfeitorias que incorpora ao imóvel (segurar 10% do prédio); se obra estrutural, aguardar fim (CG 7.1 x/y)"),
    ], columns=["Sinal observado (colunas / fórmula)", "Cobertura alvo (Fixa do plano ou Adicional)", "Direção", "Força", "Por que faz sentido (argumento hiperpersonalizado)"])

    p = [
        "# Etapa 07: Análise de Colunas e Base para Hiperpersonalização",
        f"_Gerado por `scripts/07_analise_colunas.py` em {date.today():%d/%m/%Y} (semente = {SEMENTE}, tempo = {br(tempo, 1)} s). Inventário completo das 73 colunas em `saidas/analise_colunas.csv`._",
        "",
        "## 1. Resumo executivo: os 10 achados mais úteis para hiperpersonalização",
        "",
        "1. **Consumo de água (`agua_media_mensal_6m`) é um sinal forte hoje ignorado:** apresenta correlação de Spearman **+0,700** com `quantidade_dependentes` e **+0,497** com `area_cadastrada_m2` (mediana sobe de R$ 100 com 0 dependentes para R$ 200 com 3 dependentes). Serve tanto para validar ocupação real de 2ª residência/locação quanto para recomendar e dimensionar `DANOS_POR_AGUA` (2ª maior causa de sinistro BB Seguros, 14,6%) e `DESPESAS_EMERGENCIAIS`.",
        "2. **Paradoxo de Simpson no condomínio (`pagamento_condominio_mensal`):** na base inteira a correlação com a área parece nula (-0,136) porque casas de rua são maiores e têm condomínio zero. Porém, **condicionando em `pagamento_condominio_mensal > 0` (n = 983), a correlação de Spearman com a área real salta para +0,815** (+0,750 em apartamentos e +0,823 em casas em condomínio), e o condomínio por m² separa o padrão `SUPERIOR` (mediana **R$ 10,00/m²**) do `NORMAL` (**R$ 7,00/m²**) e `ECONOMICO` (**R$ 6,33/m²**).",
        "3. **Gasto com material de construção (`gastos_material_construcao_24m > 0`) escala com a renda (+0,819) e não com a área (-0,088):** a presença do gasto (17,9% da base) independe de renda, mas o valor em reais entre os 461 casos positivos acompanha `renda_mensal` (Spearman +0,819). Um corte fixo de R$ 30 mil classifica clientes de alta renda fazendo troca de piso/acabamento como obra estrutural. A feature correta é a razão `gastos_material_construcao_24m / custo_reconstrucao_predio`. Já `gastos_vidracaria_24m > 0` (9,4%) **independe da renda (+0,017) e cresce com a área (+0,231)**, sendo sinal físico puro para `QUEBRA_DE_VIDROS`.",
        "4. **Crédito de aluguel do locador (`valor_medio_credito_recorrente > 0`) reflete a área do imóvel (+0,899) e não a renda do titular (+0,021):** nos 241 locadores, o crédito recebido tem correlação **+0,899** com `area_cadastrada_m2`, permitindo estimar ou auditar a metragem do imóvel alugado mesmo quando a área não está cadastrada.",
        "5. **Lacuna de `ITEM_LAZER` em `bens_compras` (25,5% dos bens):** a tabela `bens_compras` divide-se igualmente entre `ELETRONICO` (25,7%), `ITEM_LAZER` (25,5%, 2.296 itens, mediana R$ 3.300, P90 R$ 14.250), `ELETRODOMESTICO` (24,6%) e `MOVEL` (24,2%). O motor atual destaca `ELETRONICO` e `ELETRODOMESTICO`, mas não menciona `ITEM_LAZER` (bicicletas, equipamentos esportivos/lazer), que é um gatilho direto para `ROUBO_FURTO_ARROMBAMENTO`, `RESPONSABILIDADE_CIVIL_FAMILIAR` e cobertura adicional de Bicicleta.",
        "6. **Engenharia reversa exata da confiança dos bens (`probabilidade_bem_no_imovel_referencia`):** no gerador, a probabilidade segue a fórmula `p = 0,30 + 0,18*[mesma_uf] + 0,28*[mesmo_municipio] + 0,18*[financiado_banco] - 0,10*[ruido_22%]`, e `valor_bem_ponderado_referencia = round(valor_cadastrado * p, -1)` vale em 100% dos 8.988 itens.",
        "7. **Renda mensal (`renda_mensal`) como índice de vulnerabilidade financeira (comprometimento):** embora não deva precificar risco nem negar cobertura, a razão `comprometimento_moradia = (aluguel + financiamento + condominio) / renda_mensal` identifica famílias onde um sinistro sem `PERDA_PAGAMENTO_ALUGUEL` ou `DESPESAS_EMERGENCIAIS` inviabiliza o orçamento mensal.",
        "8. **Clientes que já possuem seguro residencial (`possui_seguro_residencial == SIM`, 16,6% em dev e 22,5% em teste):** no gerador sintético essa flag foi sorteada independentemente (Cramér's V ~ 0 com plano, vínculo e renda) e apresenta inconsistência em 144 clientes que têm `possui_seguro_residencial = SIM` mas `qtd_produtos_seguridade = 0`. Na hiperpersonalização, ela deve mudar o discurso de *contratação inicial* para *revisão de LMI / upgrade de coberturas ausentes (endosso)*.",
        "9. **Régua digital (`usuario_app`, `indice_maturidade_digital`, `frequencia_acesso_app_90d`):** no gerador, `usuario_app == SIM` equivale em 100% dos casos a `indice_maturidade_digital >= 35`. Contudo, 235 clientes com `usuario_app = NAO` têm até 69 acessos ao app em 90 dias, e 17 clientes com `SIM` têm 0 acessos. Combinar `indice_maturidade_digital >= 70` e `frequencia_acesso_app_90d >= 30` refina o One Click Buy.",
        "10. **Múltiplos imóveis e conflitos de endereço principal:** 378 clientes têm 2 imóveis (756 imóveis = 29,3% da base), mas 240 deles estão marcados com `endereco_principal_compativel = SIM` nos dois imóveis (`qtd_principais_cliente = 2`), enquanto 392 clientes de 1 único imóvel têm `endereco_principal_compativel = NAO`. Cruzar esse campo com `agua_media_mensal_6m` e `energia_media_mensal_6m` evita classificar moradia habitual como segunda residência desocupada.",
        "",
        "## 2. As 15 colunas de maior valor para hiperpersonalização",
        "",
        tabela_md(top15),
        "",
        "## 3. Mapa Sinal -> Cobertura (fixa do plano ou adicional hiperpersonalizada)",
        "",
        "Na hiperpersonalização, além de recomendar o plano base (**Essencial**, **Prático** ou **Total**), o motor indica quais coberturas **adicionais avulsas** (do plano superior ou extensões do produto BB Seguros) resolvem uma necessidade específica detectada nos dados:",
        "",
        tabela_md(sinal_cob),
        "",
        "## 4. Análises cruzadas que mudam a personalização",
        "",
        "### 4.1 Padrões de compras (`bens_compras` e `compras_*_36m`)",
        "",
        tabela_md(resumo_bens_tipo),
        "",
        "- **Sobreposição entre tabelas:** a soma de `compras_moveis_36m + compras_eletrodomesticos_36m + compras_eletronicos_36m` (mediana R$ 32.850 por imóvel) é maior que `bens_valor_cadastrado` (mediana R$ 15.650, média de 3,49 itens por imóvel) em 84,2% dos imóveis. Por isso a regra atual de tomar o `max()` (e não a soma) é correta, mas deve incorporar explicitamente a parcela de `ITEM_LAZER` na justificativa de roubo e responsabilidade civil.",
        "",
        "### 4.2 Clientes com `possui_seguro_residencial == SIM` e relacionamento em seguridade",
        "- **Comportamento na base:** 366 clientes (16,6%) em desenvolvimento e 27 (22,5%) em teste já possuem seguro residencial (429 imóveis em dev). Eles apresentam mediana de renda (R$ 7.400 vs R$ 7.675), idade (43 vs 44 anos), área (129 vs 125 m²), conteúdo (R$ 25.200 vs R$ 26.000) e distribuição de planos (Total 45,0% vs 46,8%) estatisticamente idênticas aos não segurados (geração sintética independente).",
        "- **Uso na jornada:** quando `possui_seguro_residencial == SIM`, o motor não deve ofertar uma apólice do zero sem contexto: deve apresentar a Casa Gêmea como **Diagnóstico de Proteção Vigente**, destacando se o cliente que hoje tem cobertura básica possui pets/dependentes (upgrade para RC Familiar), bens eletrônicos/lazer recentes (upgrade de LMI de Roubo e Danos Elétricos) ou 2º imóvel descoberto.",
        "- **Maturidade digital e seguridade:** `qtd_produtos_seguridade` (40,7% com 0; 31,2% com 1; 18,2% com 2; 9,9% com 3) identifica os 28,1% de clientes multissegurados, ideais para oferta do plano **Total** ou pacotes de coberturas adicionais com argumento de consolidação de carteira.",
        "",
        "### 4.3 Sinais físicos (obra, vidraçaria, condomínio, energia, água) e clientes com 2 imóveis",
        "- **Energia e água como prova de ocupação:** imóveis com `uso_imovel = TEMPORADA_OU_SEGUNDA_RESIDENCIA` (144 em dev) têm consumo mediano de água (R$ 150) e energia (R$ 450) igual ao de moradia habitual no gerador sintético. Em produção real, `agua_media_mensal_6m <= R$ 50` + `energia_media_mensal_6m <= R$ 150` em 2º imóvel confirma imóvel fechado (acionando o alerta da CG Roubo 2.1 c e Aluguel 3.1 a sem precisar perguntar).",
        "- **Anatomia dos 378 clientes com 2 imóveis (756 imóveis):** 240 clientes têm `endereco_principal_compativel = SIM` em ambos os imóveis (480 imóveis); 116 têm 1 principal e 1 secundário (232 imóveis); e 22 têm `NAO` em ambos (44 imóveis). Além disso, 392 clientes de imóvel único têm `endereco_principal_compativel = NAO`. Por isso, `sinal_multiplos_imoveis` deve ser cruzado com o vínculo de cada imóvel (ex.: cliente que mora de aluguel no imóvel 1 e é proprietário locador ou financiador do imóvel 2).",
        "",
        "### 4.4 Efeito territorial (10 capitais / UFs)",
        "",
        tabela_md(terr_df),
        "",
        "- **O que o município muda:** o IPTU por m² quase dobra entre Fortaleza/Salvador (~R$ 10/m²) e Rio/São Paulo (R$ 17 a R$ 18/m²), o aluguel mediano varia de R$ 1.225 (Porto Alegre) a R$ 2.475 (São Paulo), e o CUB R8-N vai de R$ 2.218,68/m² (BA) a R$ 2.943,73/m² (RS). Calibrar IPTU/m² e aluguel/m² por cidade é indispensável para não superestimar a área em SP/RJ nem subestimar em CE/BA/GO.",
        "",
        "## 5. Estrutura de segmentos: K-means (k=3 a 8) vs. 7 Arquétipos por Regras",
        "",
        "Testamos o K-means padronizado (semente 42, 20 inicializações) de k=3 a k=8 na base completa codificada e apenas nas variáveis contínuas:",
        "",
        tabela_md(df_km),
        "",
        "- **Diagnóstico do K-means:** a silhueta fica entre **0,106 e 0,133** na matriz completa (e 0,076 a 0,133 nas contínuas), confirmando que a base não forma esferas geométricas densas, pois o gerador sintético sorteou idade, maturidade digital, internet, pet e seguro prévio de forma independente. Apenas **k=3 é totalmente estável** (ARI = 0,998 na completa e 0,999 nas contínuas), separando (1) Locadores (n=241), (2) Inquilinos/Financiados e (3) Casas de maior metragem.",
        "- **7 Arquétipos por Regras (100% de cobertura, mutuamente exclusivos e auditáveis):** para hiperpersonalizar com explicabilidade total, propomos 7 arquétipos acionáveis:",
        "",
        tabela_md(df_arq),
        "",
        "## 6. Problemas de qualidade encontrados, deriva dev->teste e limitações",
        "",
        "- **Inconsistências de qualidade nos dados brutos (dev):** (1) **144 clientes** têm `possui_seguro_residencial = SIM` mas `qtd_produtos_seguridade = 0`; (2) **235 clientes** têm `usuario_app = NAO` mas `frequencia_acesso_app_90d > 0` (mediana 23 acessos, máximo 69), enquanto **17 clientes** com `usuario_app = SIM` têm 0 acessos; (3) **186 de 241 locadores (77,2%)** recebem crédito de aluguel no imóvel marcado como seu `endereco_principal_compativel = SIM`; (4) **397 de 1.118 apartamentos (35,5%)** têm `pagamento_condominio_mensal = 0`; (5) **240 clientes com 2 imóveis** têm `endereco_principal_compativel = SIM` nos dois endereços, e **392 clientes com 1 imóvel** têm `NAO`; (6) `complemento = LOTE 04` (286 imóveis, 11,1%) tem `possui_termo_casa = SIM` sem conter a palavra `CASA`; (7) `territorio.csv` duplica 4 colunas de `enderecos_imoveis.csv` (`codigo_ibge_municipio`, `municipio_real`, `uf_real`, `cep_agregado`).",
        "- **Deriva entre desenvolvimento e teste (`deriva_dev_teste`):** as distribuições são globalmente estáveis (|SMD| < 0,15 em 95% das numéricas). Os únicos desvios dignos de nota na amostra de teste (n=138) são: menor proporção de `area_cadastrada_m2 > 0` (39,4% em dev vs. **33,3% em teste**, -6,1 pp) e maior presença de `credito_recorrente_compativel_aluguel = SIM` (9,3% em dev vs. **15,2% em teste**, +5,9 pp, o que eleva a fatia do plano Total de 46,5% em dev para 50,0% em teste).",
        "- **Honestidade analítica (gerador sintético vs. mundo real):** na base do datathon, `idade`, `internet_mensal`, `possui_seguro_residencial` e `qtd_produtos_seguridade` foram gerados quase sem correlação com o imóvel, e `area_cadastrada_m2` não correlaciona com `renda_mensal` (Spearman -0,020). Em operação real no Banco do Brasil, esses sinais terão correlação comportamental mais forte, mas as fórmulas de interesse segurável, comprometimento de renda, ocupação hídrica/elétrica e os 7 arquétipos permanecem válidos e diretamente auditáveis.",
    ]

    caminho = PASTA_DOCS / "07_analise_colunas.md"
    texto = "\n".join(p) + "\n"
    texto = texto.replace("\u2014", "-").replace("\u2013", "-")
    caminho.write_text(texto, encoding="utf-8")
    return caminho


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    inicio = time.perf_counter()

    dev = ler_base("desenvolvimento")
    tst = ler_base("teste")

    tab_d = montar_tabela_imoveis(dev)
    tab_t = montar_tabela_imoveis(tst)
    casa_d = pd.read_csv(PASTA_SAIDAS / "casa_gemea_desenvolvimento.csv", encoding=ENCODING)
    rec_d = pd.read_csv(PASTA_SAIDAS / "recomendacao_desenvolvimento.csv", encoding=ENCODING)
    casa_t = pd.read_csv(PASTA_SAIDAS / "casa_gemea_teste.csv", encoding=ENCODING)
    rec_t = pd.read_csv(PASTA_SAIDAS / "recomendacao_teste.csv", encoding=ENCODING)

    full_d = (
        tab_d.merge(casa_d, on=["cliente_id", "imovel_id"], suffixes=("", "_cg"))
        .merge(rec_d, on=["cliente_id", "imovel_id"], suffixes=("", "_rec"))
    )
    full_t = (
        tab_t.merge(casa_t, on=["cliente_id", "imovel_id"], suffixes=("", "_cg"))
        .merge(rec_t, on=["cliente_id", "imovel_id"], suffixes=("", "_rec"))
    )

    bc_full = dev["bens_compras"].merge(
        full_d[["imovel_id", "plano_recomendado", "semaforo", "conteudo_estimado", "area_m2", "area_cadastrada_m2", "renda_mensal"]],
        left_on="imovel_id_referencia",
        right_on="imovel_id",
        how="left",
    )

    df_colunas = gerar_tabela_analise_colunas(dev, tst, full_d, bc_full)
    for c in df_colunas.select_dtypes(include="object").columns:
        df_colunas[c] = df_colunas[c].str.replace("\u2014", "-", regex=False).str.replace("\u2013", "-", regex=False)

    caminho_csv = PASTA_SAIDAS / "analise_colunas.csv"
    df_colunas.to_csv(caminho_csv, index=False, encoding=ENCODING)
    print(f"✔ saidas/{caminho_csv.name}: {len(df_colunas)} colunas analisadas")

    df_km = analisar_kmeans(full_d)
    df_arq = resumir_arquetipos(full_d, full_t)

    tempo = time.perf_counter() - inicio
    caminho_md = escrever_relatorio(df_colunas, df_km, df_arq, full_d, full_t, dev, tempo)
    print(f"✔ docs/{caminho_md.name} ({tempo:.1f}s)")


if __name__ == "__main__":
    main()
