# Etapa 06: Auditoria de privacidade e teste de proxy (idade e renda)
_Gerado por `scripts/06_auditoria_proxy.py` em 28/10/2026 (semente fixa = 42, tempo = 42,8 s)._

## Veredito executivo

**Veredito: SEM VAZAMENTO DIRETO (0 divergências no teste contrafactual) E SEM PROXY ETÁRIO; ASSOCIAÇÃO COM RENDA RESTRITA AO VALOR DE CONTEÚDO E INTEGRALMENTE EXPLICADA POR INTERESSE SEGURÁVEL LEGÍTIMO.**

1. **Uso direto zero (varredura + contrafactual):** Nenhuma linha de `src/` ou `scripts/` usa `idade`, `renda_mensal`, `origem_renda` ou `confianca_renda` em inferências ou regras. Embaralhar aleatoriamente ou substituir essas quatro colunas por constantes antes de rodar o pipeline produz **0 divergências** nos 2.578 imóveis e nas 23.690 coberturas da base de desenvolvimento.
2. **Idade sem efeito direto nem indireto:** Todas as correlações de Spearman com `idade` ficam dentro de **[-0,026; +0,039]**, o Cramér's V corrigido com o plano é **0,000** (IC 95%: 0,000 a 0,061), e a tentativa de prever o quartil de idade a partir do motor e da Casa Gêmea resulta em **AUC de 0,479 a 0,503** (acurácia de 23,2% a 26,6%, idêntica aos 25,0% do acaso).
3. **IPTU, energia, condomínio e área não são proxy de renda:** Na base de desenvolvimento, `area_m2` (Spearman **-0,020**), `pagamento_iptu_anual` (**-0,028**), `energia_media_mensal_6m` (**-0,015**) e `pagamento_condominio_mensal` (**-0,005**) têm correlação nula com `renda_mensal`. O modelo de área e o custo de reconstrução do prédio não carregam viés de renda.
4. **Por que existe associação com renda e por que ela é legítima:** Na base sintética, o valor dos bens e compras de 36 meses foi gerado proporcionalmente à renda (`conteudo_estimado` tem Spearman **+0,831** com `renda_mensal`). Como o plano **Prático** adiciona **roubo/furto de conteúdo** ao **Essencial**, imóveis do 1º quartil de renda com menos de R$ 10 mil em bens recebem o Essencial (evitando cobrar cobertura de roubo sem bens móveis relevantes). Já o plano mais completo (**Total**) tem frequência plana nos quatro quartis de renda (**47,0%, 44,6%, 45,9% e 48,4%**), com renda mediana **menor** no Total (R$ 7.750) que no Prático (R$ 10.000). Controlando por tipo, vínculo, área e conteúdo, a correlação parcial entre plano e renda cai de **+0,116** para **+0,010** (redução de 91%) e o ganho $\Delta R^2$ de adicionar idade e renda ao modelo é **0,0002**.

## A. Varredura estática (`src/` e `scripts/`)

Foram inspecionados todos os arquivos Python do repositório em busca de `idade`, `renda`, `renda_mensal`, `origem_renda`, `confianca_renda` e `data_nascimento`. **Ocorrências de uso em decisão: 0.**

| Arquivo | Linha | Termos | Classificação |
|---|---|---|---|
| src/casa_gemea/area.py | 11 | renda | NENHUMA (docstring ou texto de relatório) |
| src/casa_gemea/config.py | 35 | idade, renda_mensal, origem_renda, confianca_renda | NENHUMA (declaração de CAMPOS_PROIBIDOS) |
| src/casa_gemea/entrega.py | 171 | idade, renda | NENHUMA (teste automatizado de bloqueio no texto) |
| src/casa_gemea/entrega.py | 172 | renda, renda | NENHUMA (teste automatizado de bloqueio no texto) |
| src/casa_gemea/inferencias.py | 13 | idade, renda | NENHUMA (docstring ou texto de relatório) |
| src/casa_gemea/motor.py | 23 | idade, renda | NENHUMA (docstring ou texto de relatório) |
| src/casa_gemea/perguntas.py | 67 | renda | NENHUMA (texto/comentário sobre aluguel do imóvel) |
| src/casa_gemea/regras.py | 14 | idade, renda | NENHUMA (docstring ou texto de relatório) |
| src/casa_gemea/regras.py | 122 | renda | NENHUMA (texto/comentário sobre aluguel do imóvel) |
| src/casa_gemea/regras.py | 424 | renda | NENHUMA (texto/comentário sobre aluguel do imóvel) |
| scripts/01_construir_casa_gemea.py | 115 | idade, renda, renda | NENHUMA (docstring ou texto de relatório) |
| scripts/01_construir_casa_gemea.py | 132 | renda | NENHUMA (docstring ou texto de relatório) |
| scripts/02_aplicar_regras.py | 174 | Idade, renda | NENHUMA (docstring ou texto de relatório) |
| scripts/02_aplicar_regras.py | 259 | renda | NENHUMA (texto/comentário sobre aluguel do imóvel) |
| src/casa_gemea/carregar.py | 58 | clientes (merge) | APENAS_CARGA_DE_DADOS (descartada em COLUNAS_CASA_GEMEA) |

## B. Teste contrafactual (2.200 clientes, 2.578 imóveis, 23.690 coberturas)

O pipeline completo (treino do modelo de área, calibração de IPTU e aluguel por m², construção da Casa Gêmea, recomendação de plano, análise de impacto e cálculo das faixas) foi executado três vezes sobre a base de desenvolvimento: (1) base original; (2) colunas proibidas permutadas aleatoriamente entre clientes; (3) colunas proibidas substituídas por constantes.

| Cenário contrafactual | Imóveis | Coberturas | Div. Plano | Div. Elegib. | Div. Semáforo | Div. Casa Gêmea | Div. Faixas |
|---|---|---|---|---|---|---|---|
| Permutação aleatória (semente 42) | 2578 | 23690 | 0 | 0 | 0 | 0 | 0 |
| Substituição por constantes | 2578 | 23690 | 0 | 0 | 0 | 0 | 0 |

## C. Teste de proxy e associação na base de desenvolvimento

### C.1 Correlação de Spearman com variáveis numéricas (IC 95% por bootstrap)

| Variável | Spearman × Renda (IC 95%) | Spearman × Idade (IC 95%) |
|---|---|---|
| Centro da faixa de incêndio (R$) | 0,202 (0,165 a 0,240) | 0,039 (0,002 a 0,072) |
| Mínimo da faixa de incêndio (R$) | 0,227 (0,190 a 0,263) | 0,039 (0,001 a 0,072) |
| Máximo da faixa de incêndio (R$) | 0,172 (0,134 a 0,210) | 0,039 (0,002 a 0,073) |
| Valor estimado do conteúdo (R$) | 0,831 (0,816 a 0,843) | -0,017 (-0,053 a 0,019) |
| Área do imóvel (m²) | -0,020 (-0,058 a 0,020) | 0,024 (-0,014 a 0,063) |
| Pontuação para o plano Prático | 0,453 (0,419 a 0,483) | -0,017 (-0,057 a 0,019) |
| Pontuação para o plano Total | -0,022 (-0,061 a 0,016) | -0,021 (-0,058 a 0,018) |
| Quantidade de perguntas | 0,179 (0,145 a 0,215) | -0,026 (-0,063 a 0,015) |
| IPTU anual (entrada do modelo de área) | -0,028 (-0,066 a 0,013) | 0,026 (-0,011 a 0,063) |
| Energia mensal (entrada do modelo de área) | -0,015 (-0,048 a 0,022) | 0,013 (-0,025 a 0,049) |
| Condomínio mensal (entrada de tipo) | -0,005 (-0,042 a 0,036) | -0,007 (-0,042 a 0,029) |

### C.2 Associação com variáveis categóricas (Cramér's V corrigido e razão de médias)

| Saída categórica | Cramér's V × Quartil Renda (IC 95%) | Razão médias Renda (máx/mín) | Cramér's V × Quartil Idade (IC 95%) | Razão médias Idade (máx/mín) |
|---|---|---|---|---|
| Plano recomendado | 0,241 (0,221 a 0,264) | 3,41x | 0,000 (0,000 a 0,060) | 1,02x |
| Semáforo de canal | 0,195 (0,175 a 0,219) | 2,25x | 0,000 (0,000 a 0,047) | 1,00x |
| Confiança geral | 0,161 (0,138 a 0,185) | 1,94x | 0,000 (0,000 a 0,050) | 1,01x |
| Elegibilidade | 0,200 (0,163 a 0,240) | 2,13x | 0,000 (0,000 a 0,063) | 1,01x |
| Canal sugerido | 0,154 (0,139 a 0,178) | 2,21x | 0,000 (0,000 a 0,041) | 1,01x |
| Confiança da faixa de incêndio | 0,023 (0,000 a 0,069) | 1,10x | 0,000 (0,000 a 0,061) | 1,04x |

### C.3 Distribuição dos planos por quartil de renda e de idade

| Quartil de renda | Renda mediana (R$) | Essencial (%) | Prático (%) | Total (%) |
|---|---|---|---|---|
| Q1 | 2.500 | 24,9% | 28,1% | 47,0% |
| Q2 | 5.300 | 13,6% | 41,8% | 44,6% |
| Q3 | 11.400 | 2,3% | 51,8% | 45,9% |
| Q4 | 24.600 | 0,0% | 51,6% | 48,4% |

| Quartil de idade | Idade mediana (anos) | Essencial (%) | Prático (%) | Total (%) |
|---|---|---|---|---|
| Q1 | 28 | 9,2% | 44,7% | 46,1% |
| Q2 | 40 | 10,5% | 42,9% | 46,5% |
| Q3 | 49 | 10,6% | 40,2% | 49,2% |
| Q4 | 60 | 10,7% | 45,0% | 44,3% |

### C.4 Teste de previsibilidade (validação cruzada de 5 dobras agrupada por cliente)

Modelos treinados apenas com `numpy` (Regressão Logística Multinomial L2 e Árvore de Decisão de profundidade 3) para prever os 4 quartis de renda e os 4 quartis de idade (referência de acaso: **AUC = 0,500**, **Acurácia = 25,0%**):

| Conjunto de preditores | AUC Renda (Log / Árv) | Acurácia Renda (Log / Árv) | AUC Idade (Log / Árv) | Acurácia Idade (Log / Árv) |
|---|---|---|---|---|
| 1. Apenas plano recomendado | 0,563 / 0,563 | 29,7% / 29,7% | 0,479 / 0,482 | 25,0% / 25,8% |
| 2. Decisões categóricas do motor (plano, semáforo, confiança, elegibilidade, nº perguntas) | 0,655 / 0,619 | 39,3% / 34,3% | 0,482 / 0,481 | 25,1% / 26,2% |
| 3. Estrutura física da Casa Gêmea (tipo, vínculo, uso, área, padrão, município) | 0,508 / 0,483 | 26,2% / 23,9% | 0,486 / 0,494 | 23,4% / 26,6% |
| 4. Apenas valor estimado de conteúdo (bens + compras 36m) | 0,838 / 0,826 | 57,1% / 55,7% | 0,494 / 0,503 | 24,4% / 25,4% |
| 5. Todas as saídas do motor + Casa Gêmea completa (inclui conteúdo, faixas e aluguel/financiamento) | 0,928 / 0,846 | 74,2% / 63,8% | 0,483 / 0,497 | 23,2% / 25,3% |

A partir do `plano_recomendado` isolado, a previsibilidade do quartil de renda é baixa (**AUC = 0,563**, acurácia **29,7%** contra 25,0% do acaso) e a da estrutura física da Casa Gêmea (`tipo`, `vinculo`, `uso`, `area_m2`, `padrao`, `municipio`) é nula (**AUC = 0,508 / 0,483**). O AUC de renda só sobe quando se incluem as grandezas patrimoniais em reais (`conteudo_estimado` e compromissos mensais de aluguel/financiamento), que medem diretamente o valor em risco segurável.

### C.5 Controle por variáveis legítimas de risco e interesse segurável

Para testar se resta efeito de renda além da exposição patrimonial legítima (CG 15.1, Primeiro Risco Absoluto), calculamos a correlação parcial de Spearman controlando por `(tipo_imovel, vinculo, area_m2, conteudo_estimado)` e pelos sinais de cobertura, além do ganho $\Delta R^2$ ao acrescentar `renda_mensal` e `idade`:

| Saída do motor | Spearman bruto × Renda | Parcial (tipo, vínculo, área, conteúdo) | Parcial (todos os sinais legítimos) | Ganho ΔR² ao somar Idade+Renda |
|---|---|---|---|---|
| Plano recomendado (codificado 0/1/2) | 0,116 (0,072 a 0,155) | 0,010 (-0,024 a 0,047) | 0,018 (-0,019 a 0,052) | 0,0002 |
| Pontos do plano Prático | 0,453 (0,419 a 0,483) | -0,083 (-0,125 a -0,046) | -0,047 (-0,080 a -0,010) | 0,0001 |
| Pontos do plano Total | -0,022 (-0,061 a 0,016) | 0,006 (-0,030 a 0,042) | -0,011 (-0,048 a 0,024) | 0,0001 |
| Centro da faixa de incêndio (R$) | 0,202 (0,165 a 0,240) | -0,066 (-0,100 a -0,028) | -0,069 (-0,103 a -0,032) | 0,0000 |
| Quantidade de perguntas | 0,179 (0,145 a 0,215) | 0,053 (0,021 a 0,087) | 0,043 (0,011 a 0,079) | 0,0029 |

Nos estratos de mesmo vínculo, tipo de imóvel e quintil de conteúdo, o Cramér's V corrigido médio entre plano e quartil de renda cai de **0,241** para **0,055**, e chega a **0,000** nos 1.515 imóveis cujo conteúdo do cliente é de pelo menos R$ 20 mil.

## D. Conclusão, limitações e recomendação mínima

- **Conclusão:** O motor respeita integralmente a proibição de uso de idade e renda. A associação observada entre `conteudo_estimado` e `renda_mensal` decorre da própria geração sintética da base (onde compras e bens cadastrados escalam com a renda) e reflete necessidade securitária real: dimensionar o LMI de conteúdo e recomendar cobertura de roubo apenas a quem possui bens móveis expostos.
- **Limitações da auditoria:** (1) A base é sintética; em dados reais de mercado, área construída e IPTU costumam ter correlação positiva maior com renda do que na base do desafio (onde é próxima de zero). (2) O teste controla pelas variáveis patrimoniais observadas no banco; se o cadastro de bens subestimar sistematicamente o patrimônio de clientes que compram fora do banco, a pergunta de confirmação de conteúdo corrige essa lacuna na jornada.
- **Recomendação mínima (defesa em profundidade, sem necessidade de alterar as regras atuais):** Em `src/casa_gemea/carregar.py`, remover explicitamente `CAMPOS_PROIBIDOS` no momento da leitura de `clientes.csv` (`df.drop(columns=CAMPOS_PROIBIDOS, errors='ignore')`), garantindo que tais colunas sequer transitem em memória durante a montagem da tabela intermediária.
