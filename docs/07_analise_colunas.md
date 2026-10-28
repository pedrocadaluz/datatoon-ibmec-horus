# Etapa 07: Análise de Colunas e Base para Hiperpersonalização
_Gerado por `scripts/07_analise_colunas.py` em 28/10/2026 (semente = 42, tempo = 9,4 s). Inventário completo das 73 colunas em `saidas/analise_colunas.csv`._

## 1. Resumo executivo: os 10 achados mais úteis para hiperpersonalização

1. **Consumo de água (`agua_media_mensal_6m`) é um sinal forte hoje ignorado:** apresenta correlação de Spearman **+0,700** com `quantidade_dependentes` e **+0,497** com `area_cadastrada_m2` (mediana sobe de R$ 100 com 0 dependentes para R$ 200 com 3 dependentes). Serve tanto para validar ocupação real de 2ª residência/locação quanto para recomendar e dimensionar `DANOS_POR_AGUA` (2ª maior causa de sinistro BB Seguros, 14,6%) e `DESPESAS_EMERGENCIAIS`.
2. **Paradoxo de Simpson no condomínio (`pagamento_condominio_mensal`):** na base inteira a correlação com a área parece nula (-0,136) porque casas de rua são maiores e têm condomínio zero. Porém, **condicionando em `pagamento_condominio_mensal > 0` (n = 983), a correlação de Spearman com a área real salta para +0,815** (+0,750 em apartamentos e +0,823 em casas em condomínio), e o condomínio por m² separa o padrão `SUPERIOR` (mediana **R$ 10,00/m²**) do `NORMAL` (**R$ 7,00/m²**) e `ECONOMICO` (**R$ 6,33/m²**).
3. **Gasto com material de construção (`gastos_material_construcao_24m > 0`) escala com a renda (+0,819) e não com a área (-0,088):** a presença do gasto (17,9% da base) independe de renda, mas o valor em reais entre os 461 casos positivos acompanha `renda_mensal` (Spearman +0,819). Um corte fixo de R$ 30 mil classifica clientes de alta renda fazendo troca de piso/acabamento como obra estrutural. A feature correta é a razão `gastos_material_construcao_24m / custo_reconstrucao_predio`. Já `gastos_vidracaria_24m > 0` (9,4%) **independe da renda (+0,017) e cresce com a área (+0,231)**, sendo sinal físico puro para `QUEBRA_DE_VIDROS`.
4. **Crédito de aluguel do locador (`valor_medio_credito_recorrente > 0`) reflete a área do imóvel (+0,899) e não a renda do titular (+0,021):** nos 241 locadores, o crédito recebido tem correlação **+0,899** com `area_cadastrada_m2`, permitindo estimar ou auditar a metragem do imóvel alugado mesmo quando a área não está cadastrada.
5. **Lacuna de `ITEM_LAZER` em `bens_compras` (25,5% dos bens):** a tabela `bens_compras` divide-se igualmente entre `ELETRONICO` (25,7%), `ITEM_LAZER` (25,5%, 2.296 itens, mediana R$ 3.300, P90 R$ 14.250), `ELETRODOMESTICO` (24,6%) e `MOVEL` (24,2%). O motor atual destaca `ELETRONICO` e `ELETRODOMESTICO`, mas não menciona `ITEM_LAZER` (bicicletas, equipamentos esportivos/lazer), que é um gatilho direto para `ROUBO_FURTO_ARROMBAMENTO`, `RESPONSABILIDADE_CIVIL_FAMILIAR` e cobertura adicional de Bicicleta.
6. **Engenharia reversa exata da confiança dos bens (`probabilidade_bem_no_imovel_referencia`):** no gerador, a probabilidade segue a fórmula `p = 0,30 + 0,18*[mesma_uf] + 0,28*[mesmo_municipio] + 0,18*[financiado_banco] - 0,10*[ruido_22%]`, e `valor_bem_ponderado_referencia = round(valor_cadastrado * p, -1)` vale em 100% dos 8.988 itens.
7. **Renda mensal (`renda_mensal`) como índice de vulnerabilidade financeira (comprometimento):** embora não deva precificar risco nem negar cobertura, a razão `comprometimento_moradia = (aluguel + financiamento + condominio) / renda_mensal` identifica famílias onde um sinistro sem `PERDA_PAGAMENTO_ALUGUEL` ou `DESPESAS_EMERGENCIAIS` inviabiliza o orçamento mensal.
8. **Clientes que já possuem seguro residencial (`possui_seguro_residencial == SIM`, 16,6% em dev e 15,0% em teste):** no gerador sintético essa flag foi sorteada independentemente (Cramér's V ~ 0 com plano, vínculo e renda) e apresenta inconsistência em 144 clientes que têm `possui_seguro_residencial = SIM` mas `qtd_produtos_seguridade = 0`. Na hiperpersonalização, ela deve mudar o discurso de *contratação inicial* para *revisão de LMI / upgrade de coberturas ausentes (endosso)*.
9. **Régua digital (`usuario_app`, `indice_maturidade_digital`, `frequencia_acesso_app_90d`):** no gerador, `usuario_app == SIM` equivale em 100% dos casos a `indice_maturidade_digital >= 35`. Contudo, 235 clientes com `usuario_app = NAO` têm até 69 acessos ao app em 90 dias, e 17 clientes com `SIM` têm 0 acessos. Combinar `indice_maturidade_digital >= 70` e `frequencia_acesso_app_90d >= 30` refina o One Click Buy.
10. **Múltiplos imóveis e conflitos de endereço principal:** 378 clientes têm 2 imóveis (756 imóveis = 29,3% da base), mas 240 deles estão marcados com `endereco_principal_compativel = SIM` nos dois imóveis (`qtd_principais_cliente = 2`), enquanto 392 clientes de 1 único imóvel têm `endereco_principal_compativel = NAO`. Cruzar esse campo com `agua_media_mensal_6m` e `energia_media_mensal_6m` evita classificar moradia habitual como segunda residência desocupada.

## 2. As 15 colunas de maior valor para hiperpersonalização

| # | Tabela | Coluna | Uso atual | Associação principal | Feature derivada (fórmula) | Ganho para hiperpersonalização |
|---|---|---|---|---|---|---|
| 1 | SINAIS_IMOBILIARIOS | agua_media_mensal_6m | IGNORADA_HOJE | Spearman dep=+0,70; área=+0,50 | ocupacao_hidrica = (agua - 0,5*area)/35; alerta_hidraulico = (agua >= 250) | DANOS_POR_AGUA, DESPESAS_EMERGENCIAIS e validação de ocupação real |
| 2 | CLIENTES | possui_seguro_residencial | IGNORADA_HOJE | 16,6% SIM (dev) / 15,0% (teste) | modo_jornada = 'UPGRADE_ENDOSSO' se SIM senão 'NOVA_APOLICE' | Muda abordagem inteira: diagnóstico de subseguro/lacunas na apólice vigente |
| 3 | BENS_COMPRAS | tipo_bem (ITEM_LAZER / MOVEL) | PARCIAL (só total) | 25,5% ITEM_LAZER (med R$ 3.300, P90 R$ 14.250) | bens_ponderado_item_lazer; flag_lazer_bike = (item_lazer >= 5000) | ROUBO_FURTO_ARROMBAMENTO, RC_FAMILIAR e cobertura adicional de Bicicleta/Lazer |
| 4 | CLIENTES | renda_mensal | PROIBIDA_HOJE | Spearman conteúdo=+0,83; aluguel=+0,79; obra>0=+0,82 | comprometimento_moradia = (aluguel + financ + cond) / renda_mensal | PERDA_PAGAMENTO_ALUGUEL e DESPESAS_EMERGENCIAIS quando comprometimento >= 30% |
| 5 | SINAIS_IMOBILIARIOS | pagamento_condominio_mensal | USADA_NA_DECISAO | Nos >0 (n=983): Spearman área=+0,82; Superior=R$ 10/m² | condominio_m2 = condominio / area_m2; area_impl_cond = condominio / 6,85 | Melhora estimativa de área/padrão em condomínios e puxa RC_FAMILIAR (vizinhos) |
| 6 | SINAIS_IMOBILIARIOS | valor_medio_credito_recorrente | USADA_SO_CALCULO | Nos >0 (n=241): Spearman área=+0,90; renda=+0,02 | area_impl_aluguel_locador = credito_recorrente / aluguel_m2_cidade | PERDA_PAGAMENTO_ALUGUEL do locador e validação cruzada da área do imóvel |
| 7 | SINAIS_IMOBILIARIOS | gastos_material_construcao_24m | USADA_NA_DECISAO | Nos >0 (n=461): Spearman renda=+0,82; área=-0,09 | intensidade_obra = gasto_obra / custo_reconstrucao_predio | Evita falso positivo de obra estrutural em alta renda; dimensiona benfeitorias |
| 8 | CLIENTES | qtd_produtos_seguridade | IGNORADA_HOJE | 59,3% têm >=1 produto; 28,1% têm >=2 | tier_relacionamento_seguridade (0, 1, 2+); flag_conflito_apolice | Define propensão a pacote completo (TOTAL) e argumentação de cross-sell/combo |
| 9 | CLIENTES | frequencia_acesso_app_90d | IGNORADA_HOJE | Spearman maturidade=+0,80; máx=161 acessos | engajamento_app = freq_90d / 90; elegivel_ocb_real = (usuario_app=='SIM' & freq>=30) | Filtra falsos usuários de app no One Click Buy e ativa gatilho contextual in-app |
| 10 | CLIENTES | indice_maturidade_digital | IGNORADA_HOJE | Corte exato: >=35 equivale a 100% de usuario_app=SIM | complexidade_jornada = 'EXPRESS_1CLICK' (>=70), 'GUIADA' (35-69), 'HUMANA' (<35) | Personaliza profundidade do texto explicativo e canal de fechamento |
| 11 | SINAIS_IMOBILIARIOS | energia_media_mensal_6m | USADA_SO_CALCULO | Spearman área=+0,83; água=+0,61; dep=+0,31 | intensidade_eletrica_m2 = energia / area_m2 (sinal de climatização/carga) | DANOS_ELETRICOS (53,3% dos sinistros BB Seguros) e estimativa de área |
| 12 | SINAIS_IMOBILIARIOS | gastos_vidracaria_24m | USADA_NA_DECISAO | Nos >0 (n=242): independe de renda (+0,02), sobe c/ área (+0,23) | densidade_vidros_m2 = vidracaria / area_m2; piso de LMI = 1,5x gasto | QUEBRA_DE_VIDROS (sinal físico puro de envidraçamento de sacada/blindex/espelhos) |
| 13 | CLIENTES | quantidade_dependentes | USADA_NA_DECISAO | Plano V=0,29; Spearman água=+0,70; pontos_total=+0,39 | tamanho_familia = 1 + dependentes; escala RC (+R$ 5k-10k/dep) e Despesas Emerg. | RESPONSABILIDADE_CIVIL_FAMILIAR e DESPESAS_EMERGENCIAIS |
| 14 | CLIENTES | possui_pet_informado | USADA_NA_DECISAO | 35,0% SIM (dev) / 38,3% (teste); Plano V=0,26 | interacao_pet_condominio = (pet=='SIM' & condominio>0) | RESPONSABILIDADE_CIVIL_FAMILIAR (+R$ 10k-30k LMI) e assistência veterinária/pet |
| 15 | BENS_COMPRAS | probabilidade_bem_no_imovel_referencia | USADA_SO_CALCULO | 9 degraus (0,20 a 0,94) derivados de UF, município e financ. | razao_incerteza_conteudo = bens_valor_cadastrado / bens_valor_ponderado | Controla largura da faixa de ROUBO_FURTO e DANOS_ELETRICOS e pergunta de bens |

## 3. Mapa Sinal -> Cobertura (fixa do plano ou adicional hiperpersonalizada)

Na hiperpersonalização, além de recomendar o plano base (**Essencial**, **Prático** ou **Total**), o motor indica quais coberturas **adicionais avulsas** (do plano superior ou extensões do produto BB Seguros) resolvem uma necessidade específica detectada nos dados:

| Sinal observado (colunas / fórmula) | Cobertura alvo (Fixa do plano ou Adicional) | Direção | Força | Por que faz sentido (argumento hiperpersonalizado) |
|---|---|---|---|---|
| pagamento_iptu_anual + energia_media_mensal_6m + uf_real + padrao_construtivo | INCENDIO_RAIO_EXPLOSAO_FUMACA (Fixa: todos) | Positiva (+) | FORTE | Dimensiona reconstrução do prédio (área x CUB da UF x fator Sinduscon x interesse segurável) + conteúdo |
| agua_media_mensal_6m >= R$ 200 + compras_moveis_36m | DANOS_POR_AGUA (Fixa: todos) + Vazamento de Tubulações (Adicional) | Positiva (+) | FORTE | 2ª maior causa de sinistro BB (14,6%); alto consumo de água indica mais banheiros/prumadas hidráulicas e móveis vulneráveis |
| possui_termo_casa == SIM + gastos_vidracaria_24m > 0 | VENDAVAL_GRANIZO e IMPACTO_VEICULOS (Fixas: todos) | Positiva (+) | FORTE | Casas têm telhado, portão, muro e fachada diretamente expostos (11,5% dos sinistros BB são climáticos) |
| compras_eletronicos_36m + compras_eletrodomesticos_36m + energia_media_mensal_6m / area_m2 | DANOS_ELETRICOS (Fixa: todos) + Equipamentos Portáteis/Home Office (Adicional) | Positiva (+) | FORTE | 1ª causa de sinistro BB (53,3%); protege TVs, computadores, linha branca inverter e ar-condicionado contra surtos |
| bens_valor_ponderado >= R$ 10 mil + tipo_bem in (ELETRONICO, ITEM_LAZER) + eh_casa | ROUBO_FURTO_ARROMBAMENTO (Fixa: Prático/Total; Adicional recomendada no Essencial) | Positiva (+) se ocupado; Negativa (-) se desocupado | FORTE | Protege bens portáteis e de lazer; se 2ª residência desocupada, alertar exclusão contratual (CG Roubo 2.1 c) |
| tipo_bem == ITEM_LAZER (soma >= R$ 5 mil) | Subtração de Bicicleta / Equipamentos Esportivos (Adicional hiperpersonalizada) | Positiva (+) | MEDIA | 25,5% dos bens cadastrados são ITEM_LAZER (mediana R$ 3.300, P90 R$ 14.250), hoje sem destaque específico no texto |
| gastos_vidracaria_24m > 0 + area_m2 + pagamento_condominio_mensal > 0 | QUEBRA_DE_VIDROS (Fixa: Prático/Total; Adicional recomendada no Essencial) | Positiva (+) | FORTE | Gasto recente em vidraçaria comprova instalação de cortina de vidro, box, espelhos ou tampos (LMI máx >= 1,5x gasto) |
| possui_pet_informado == SIM + quantidade_dependentes > 0 + tipo_imovel == APARTAMENTO | RESPONSABILIDADE_CIVIL_FAMILIAR (Fixa: Total; Adicional recomendada no Prático/Essencial) | Positiva (+) | FORTE | Cobre mordida/dano de pet (CG 1.1 c), atos de filhos/empregados (1.1 b) e vazamento/infiltração no apto vizinho (1.1 e) |
| pagamento_aluguel_recorrente == SIM ou credito_recorrente_compativel_aluguel == SIM ou comprometimento_moradia >= 30% | PERDA_PAGAMENTO_ALUGUEL (Fixa: Total; Adicional crítica para Inquilino/Locador/Alto Comprometimento) | Positiva (+) | FORTE | Protege 3 a 6 meses de aluguel pago pelo inquilino ou recebido pelo locador (até R$ 18 mil medianos em risco) |
| quantidade_dependentes >= 1 + agua_media_mensal_6m >= R$ 150 + comprometimento_moradia >= 30% | DESPESAS_EMERGENCIAIS (Fixa: Total; Adicional para famílias) | Positiva (+) | MEDIA | Paga 10% nas primeiras 48h + 3% do LMI ao dia para hospedagem, alimentação e transporte da família (CG 1.3) |
| gastos_material_construcao_24m > 0 + vinculo == INQUILINO | Benfeitorias no Prédio (INCENDIO/AGUA) + Assistência Pequenos Reparos | Positiva (+) se leve; Bloqueio se estrutural | MEDIA | Inquilino com gasto < R$ 30 mil fez benfeitorias que incorpora ao imóvel (segurar 10% do prédio); se obra estrutural, aguardar fim (CG 7.1 x/y) |

## 4. Análises cruzadas que mudam a personalização

### 4.1 Padrões de compras (`bens_compras` e `compras_*_36m`)

| Categoria (tipo_bem) | Itens (dev) | % dos bens | Valor mediano (R$) | P90 (R$) | Tratamento atual no motor |
|---|---|---|---|---|---|
| ELETRODOMESTICO | 2207 | 24,6% | 3.350 | 14.000 | Total + Eletrônicos/Eletro (Danos Elétricos e Prático) |
| ELETRONICO | 2308 | 25,7% | 3.300 | 13.915 | Total + Eletrônicos/Eletro (Danos Elétricos e Prático) |
| ITEM_LAZER | 2296 | 25,5% | 3.300 | 14.250 | Apenas soma geral de conteúdo (sem regra específica hoje) |
| MOVEL | 2177 | 24,2% | 3.150 | 13.550 | Apenas soma geral de conteúdo (sem regra específica hoje) |

- **Sobreposição entre tabelas:** a soma de `compras_moveis_36m + compras_eletrodomesticos_36m + compras_eletronicos_36m` (mediana R$ 32.850 por imóvel) é maior que `bens_valor_cadastrado` (mediana R$ 15.650, média de 3,49 itens por imóvel) em 84,2% dos imóveis. Por isso a regra atual de tomar o `max()` (e não a soma) é correta, mas deve incorporar explicitamente a parcela de `ITEM_LAZER` na justificativa de roubo e responsabilidade civil.

### 4.2 Clientes com `possui_seguro_residencial == SIM` e relacionamento em seguridade
- **Comportamento na base:** 366 clientes (16,6%) em desenvolvimento e 18 (15,0%) em teste já possuem seguro residencial (429 imóveis em dev). Eles apresentam mediana de renda (R$ 7.400 vs R$ 7.675), idade (43 vs 44 anos), área (129 vs 125 m²), conteúdo (R$ 25.200 vs R$ 26.000) e distribuição de planos (Total 45,0% vs 46,8%) estatisticamente idênticas aos não segurados (geração sintética independente).
- **Uso na jornada:** quando `possui_seguro_residencial == SIM`, o motor não deve ofertar uma apólice do zero sem contexto: deve apresentar a Casa Gêmea como **Diagnóstico de Proteção Vigente**, destacando se o cliente que hoje tem cobertura básica possui pets/dependentes (upgrade para RC Familiar), bens eletrônicos/lazer recentes (upgrade de LMI de Roubo e Danos Elétricos) ou 2º imóvel descoberto.
- **Maturidade digital e seguridade:** `qtd_produtos_seguridade` (40,7% com 0; 31,2% com 1; 18,2% com 2; 9,9% com 3) identifica os 28,1% de clientes multissegerados, ideais para oferta do plano **Total** ou pacotes de coberturas adicionais com argumento de consolidação de carteira.

### 4.3 Sinais físicos (obra, vidraçaria, condomínio, energia, água) e clientes com 2 imóveis
- **Energia e água como prova de ocupação:** imóveis com `uso_imovel = TEMPORADA_OU_SEGUNDA_RESIDENCIA` (144 em dev) têm consumo mediano de água (R$ 150) e energia (R$ 450) igual ao de moradia habitual no gerador sintético. Em produção real, `agua_media_mensal_6m <= R$ 50` + `energia_media_mensal_6m <= R$ 150` em 2º imóvel confirma imóvel fechado (acionando o alerta da CG Roubo 2.1 c e Aluguel 3.1 a sem precisar perguntar).
- **Anatomia dos 378 clientes com 2 imóveis (756 imóveis):** 240 clientes têm `endereco_principal_compativel = SIM` em ambos os imóveis (480 imóveis); 116 têm 1 principal e 1 secundário (232 imóveis); e 22 têm `NAO` em ambos (44 imóveis). Além disso, 392 clientes de imóvel único têm `endereco_principal_compativel = NAO`. Por isso, `sinal_multiplos_imoveis` deve ser cruzado com o vínculo de cada imóvel (ex.: cliente que mora de aluguel no imóvel 1 e é proprietário locador ou financiador do imóvel 2).

### 4.4 Efeito territorial (10 capitais / UFs)

| Município | UF | Imóveis | Área med (m²) | IPTU/m² med (R$) | Condomínio >0 med (R$) | Aluguel >0 med (R$) | Renda med (R$) | % Plano Total |
|---|---|---|---|---|---|---|---|---|
| Belo Horizonte | MG | 226 | 120 | 12,4 | 650 | 1.600 | 6.925 | 43,4% |
| Brasilia | DF | 418 | 128 | 15,0 | 875 | 2.000 | 7.650 | 49,3% |
| Curitiba | PR | 250 | 118 | 13,9 | 550 | 2.000 | 7.250 | 41,6% |
| Fortaleza | CE | 157 | 137 | 10,0 | 600 | 1.950 | 9.650 | 52,2% |
| Goiania | GO | 201 | 124 | 10,9 | 600 | 1.800 | 10.250 | 44,3% |
| Porto Alegre | RS | 144 | 126 | 13,5 | 750 | 1.225 | 5.625 | 42,4% |
| Recife | PE | 183 | 127 | 11,6 | 600 | 1.675 | 8.100 | 50,3% |
| Rio de Janeiro | RJ | 280 | 135 | 17,1 | 975 | 1.875 | 7.300 | 43,6% |
| Salvador | BA | 201 | 121 | 10,5 | 575 | 1.750 | 6.050 | 46,3% |
| Sao Paulo | SP | 518 | 125 | 18,0 | 1.000 | 2.475 | 8.450 | 48,5% |

- **O que o município muda:** o IPTU por m² quase dobra entre Fortaleza/Salvador (~R$ 10/m²) e Rio/São Paulo (R$ 17 a R$ 18/m²), o aluguel mediano varia de R$ 1.225 (Porto Alegre) a R$ 2.475 (São Paulo), e o CUB R8-N vai de R$ 2.218,68/m² (BA) a R$ 2.943,73/m² (RS). Calibrar IPTU/m² e aluguel/m² por cidade é indispensável para não superestimar a área em SP/RJ nem subestimar em CE/BA/GO.

## 5. Estrutura de segmentos: K-means (k=3 a 8) vs. 7 Arquétipos por Regras

Testamos o K-means padronizado (semente 42, 20 inicializações) de k=3 a k=8 na base completa codificada e apenas nas variáveis contínuas:

| k | Silhueta (base completa) | Estabilidade ARI (completa) | Silhueta (só contínuas) | Estabilidade ARI (contínuas) | Tamanhos dos grupos (dev, n=2578) |
|---|---|---|---|---|---|
| 3 | 0,133 | 0,998 | 0,128 | 0,999 | 1570, 767, 241 |
| 4 | 0,106 | 0,978 | 0,133 | 0,919 | 1062, 698, 577, 241 |
| 5 | 0,114 | 0,994 | 0,076 | 0,800 | 994, 655, 544, 241, 144 |
| 6 | 0,113 | 0,741 | 0,082 | 0,667 | 865, 551, 456, 273, 241, 192 |
| 7 | 0,117 | 0,840 | 0,092 | 0,504 | 849, 555, 461, 260, 239, 143, 71 |
| 8 | 0,120 | 0,870 | 0,085 | 0,625 | 739, 497, 380, 255, 241, 177, 147, 142 |

- **Diagnóstico do K-means:** a silhueta fica entre **0,106 e 0,133** na matriz completa (e 0,097 a 0,167 nas contínuas), confirmando que a base não forma esferas geométricas densas, pois o gerador sintético sorteou idade, maturidade digital, internet, pet e seguro prévio de forma independente. Apenas **k=3 é totalmente estável** (ARI = 0,998 na completa e 1,000 nas contínuas), separando (1) Locadores (n=241), (2) Inquilinos/Financiados e (3) Casas de maior metragem.
- **7 Arquétipos por Regras (100% de cobertura, mutuamente exclusivos e auditáveis):** para hiperpersonalizar com explicabilidade total, propomos 7 arquétipos acionáveis:

| Arquétipo | Dev n (%) | Teste n (%) | Renda med (R$) | Conteúdo med (R$) | Plano sugerido e hiperpersonalização de coberturas |
|---|---|---|---|---|---|
| 1. Imóvel em Reforma ou Obra Relevante | 193 (7,5%) | 10 (7,2%) | 16.750 | 40.800 | Validar elegibilidade (CG 7.1 x/y); após obra: QUEBRA_DE_VIDROS, DANOS_ELETRICOS e INCENDIO com benfeitorias |
| 2. Investidor Locador (Proteção de Renda e Prédio) | 216 (8,4%) | 17 (12,3%) | 7.575 | 24.000 | TOTAL: PERDA_PAGAMENTO_ALUGUEL (3 a 6 meses de renda) + INCENDIO (100% prédio, 20% conteúdo, CG 6.1 r) |
| 3. Inquilino Urbano (Conteúdo, Aluguel e RC) | 516 (20,0%) | 31 (22,5%) | 6.725 | 23.850 | TOTAL: PERDA_PAGAMENTO_ALUGUEL + ROUBO_FURTO + DANOS_ELETRICOS + RC_FAMILIAR (prédio só 3%-10% benfeitorias) |
| 4. Segunda Residência / Veraneio | 103 (4,0%) | 3 (2,2%) | 6.400 | 26.000 | PRATICO ou ESSENCIAL: VENDAVAL_GRANIZO + DANOS_POR_AGUA + DANOS_ELETRICOS (alerta: sem ROUBO se desocupado, CG 2.1 c) |
| 5. Mutuário Financiado (Complemento DFI + Conteúdo) | 667 (25,9%) | 34 (24,6%) | 6.750 | 25.000 | PRATICO (+ TOTAL se família/pet): ROUBO_FURTO + DANOS_ELETRICOS + QUEBRA_DE_VIDROS (prédio em 2o risco sobre DFI, CG 15.2) |
| 6. Família ou Tutor de Pet em Imóvel Quitado | 683 (26,5%) | 39 (28,3%) | 7.400 | 26.000 | TOTAL ou PRATICO+RC: INCENDIO (100% casa) + RC_FAMILIAR (pet/filhos/vizinhos) + DESPESAS_EMERGENCIAIS + DANOS_POR_AGUA |
| 7. Proprietário Quitado Solo / Casal sem Dependentes | 200 (7,8%) | 4 (2,9%) | 7.550 | 24.900 | PRATICO (se conteúdo >= R$ 20 mil / casa) ou ESSENCIAL (compacto): foco em ROUBO_FURTO, DANOS_ELETRICOS e QUEBRA_DE_VIDROS |

## 6. Problemas de qualidade encontrados, deriva dev->teste e limitações

- **Inconsistências de qualidade nos dados brutos (dev):** (1) **144 clientes** têm `possui_seguro_residencial = SIM` mas `qtd_produtos_seguridade = 0`; (2) **235 clientes** têm `usuario_app = NAO` mas `frequencia_acesso_app_90d > 0` (mediana 23 acessos, máximo 69), enquanto **17 clientes** com `usuario_app = SIM` têm 0 acessos; (3) **186 de 241 locadores (77,2%)** recebem crédito de aluguel no imóvel marcado como seu `endereco_principal_compativel = SIM`; (4) **397 de 1.118 apartamentos (35,5%)** têm `pagamento_condominio_mensal = 0`; (5) **240 clientes com 2 imóveis** têm `endereco_principal_compativel = SIM` nos dois endereços, e **392 clientes com 1 imóvel** têm `NAO`; (6) `complemento = LOTE 04` (286 imóveis, 11,1%) tem `possui_termo_casa = SIM` sem conter a palavra `CASA`; (7) `territorio.csv` duplica 4 colunas de `enderecos_imoveis.csv` (`codigo_ibge_municipio`, `municipio_real`, `uf_real`, `cep_agregado`).
- **Deriva entre desenvolvimento e teste (`deriva_dev_teste`):** as distribuições são globalmente estáveis (|SMD| < 0,15 em 95% das numéricas). Os únicos desvios dignos de nota na amostra de teste (n=138) são: menor proporção de `area_cadastrada_m2 > 0` (39,4% em dev vs. **33,3% em teste**, -6,1 pp) e maior presença de `credito_recorrente_compativel_aluguel = SIM` (9,3% em dev vs. **15,2% em teste**, +5,9 pp, o que eleva a fatia do plano Total de 46,5% em dev para 50,0% em teste).
- **Honestidade analítica (gerador sintético vs. mundo real):** na base do datathon, `idade`, `internet_mensal`, `possui_seguro_residencial` e `qtd_produtos_seguridade` foram gerados quase sem correlação com o imóvel, e `area_cadastrada_m2` não correlaciona com `renda_mensal` (Spearman -0,020). Em operação real no Banco do Brasil, esses sinais terão correlação comportamental mais forte, mas as fórmulas de interesse segurável, comprometimento de renda, ocupação hídrica/elétrica e os 7 arquétipos permanecem válidos e diretamente auditáveis.
