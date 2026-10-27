# Etapa 02 — Regras do seguro
_Gerado por `scripts/02_aplicar_regras.py` em 27/10/2026. Tempo de execução: 1,6 s para 2716 imóveis._

Na base de teste, **138 de 138 imóveis** receberam elegibilidade, plano, 1283 linhas de cobertura com faixa em reais, confiança, justificativa e comparação com os planos vizinhos.

## Fontes

| Fonte | Uso |
|---|---|
| Guia dos Times, seção 9 | Elegibilidade, planos e coberturas fixas |
| [Condições Gerais do Seguro Residencial BB Seguros, Processo SUSEP 15414.606453/2020-10, v1.3](https://assets-bbsegurosportal.bbseguros.com.br/2024-10/SEGURO_RESIDENCIAL_V-1.3_0.pdf) | Exclusões, bens não cobertos, Primeiro Risco Absoluto, regras de aluguel e despesas emergenciais (citadas como "CG") |
| CUB R8-N por UF (Sinduscons, ago–set/2026) | Custo de reconstrução por m² (`dados_externos/cub_r8n_por_uf.csv`) |
| Tabela CUB Sinduscon-MG (abr/2025) | Fatores de tipo e padrão (`dados_externos/fatores_cub_padrao.csv`) |
| [Monitor Mercantil, 21/07/2026](https://monitormercantil.com.br/?p=332625) | Distribuição de sinistros da carteira residencial BB Seguros |

Detalhes de cada fonte em `docs/fontes_externas.md`.

## 1. Elegibilidade

Aplicada antes de recomendar (guia, seção 2).

| Resultado | Quando | Base |
|---|---|---|
| INELEGIVEL | Situação cadastral diferente de REGULAR; parede de material combustível | Guia 9.1 |
| ELEGIVEL_CONDICIONADO | Possível obra relevante (material de construção ≥ R$ 30 mil, ou ≥ R$ 10 mil + vidraçaria); tipo não identificado | Guia 9.1; CG 7.1 x/y excluem imóveis em reforma ou construção |
| ELEGIVEL | Demais casos, sujeitos à declaração do cliente (área urbana, alvenaria, sem obra estrutural, não tombado) | CG 11.1.2 e 12.2: declaração inexata faz perder o direito |

| valor | imóveis | % |
|---|---|---|
| ELEGIVEL | 135 | 97,8 |
| ELEGIVEL_CONDICIONADO | 3 | 2,2 |

## 2. Interesse segurável (quanto do imóvel é do cliente)

| Situação | Prédio | Conteúdo | Base |
|---|---|---|---|
| Inquilino | 0% a 10% (benfeitorias) | 100% | CG 10.1: beneficiário é o proprietário |
| Apartamento (proprietário) | 10% a 30% (partes privativas) | 100% | CG 5.4 e 15.2: estrutura no seguro do condomínio |
| Casa financiada | 50% a 100% | 100% | CG 15.2: com seguro habitacional, o residencial complementa |
| Casa em condomínio | 80% a 100% | 100% | Estrutura própria; áreas comuns no seguro do condomínio |
| Casa própria | 100% | 100% | — |
| Locador | conforme o tipo | até 20% | CG 6.1 r: bens de terceiros não são cobertos |

## 3. Escolha do plano

Pontuação por sinais; nenhum sinal decide sozinho. Idade e renda não entram.

| Sinal | Pontos | Puxa para |
|---|---|---|
| Bens do cliente ≥ R$ 20.000 (≥ R$ 10.000) | 2 (1) | Prático |
| Eletrônicos e eletrodomésticos ≥ R$ 15.000 | 1 | Prático |
| Gasto com vidraçaria em 24 meses | 1 | Prático |
| Casa (mais acessos expostos) | 1 | Prático |
| Paga aluguel (inquilino) | 2 | Total |
| Recebe aluguel (locador) | 2 | Total |
| Pet | 1 | Total |
| Dependentes | 1 | Total |

**Decisão:** Total se pontos do Total ≥ 3, ou ≥ 2 com pelo menos 1 ponto do Prático; senão Prático se pontos do Prático ≥ 2; senão Essencial.

### Resultado na base de teste

| valor | imóveis | % |
|---|---|---|
| TOTAL | 69 | 50,0 |
| PRATICO | 55 | 39,9 |
| ESSENCIAL | 14 | 10,1 |

| vinculo | ESSENCIAL | PRATICO | TOTAL |
|---|---|---|---|
| INQUILINO | 0 | 0 | 31 |
| PROPRIETARIO_FINANCIADO | 5 | 27 | 7 |
| PROPRIETARIO_LOCADOR | 0 | 0 | 21 |
| PROPRIETARIO_QUITADO | 9 | 28 | 10 |

Inquilinos e locadores vão ao Total porque a cobertura de aluguel protege diretamente o que eles pagam ou recebem (CG, Perda de Aluguel 1.1).

### Estabilidade

| cenário | planos que mudam | % da base |
|---|---|---|
| limiares de bens -20% | 5 | 3,6 |
| limiares de bens +20% | 2 | 1,4 |

## 4. Faixas de cada cobertura

O seguro é a **Primeiro Risco Absoluto** (CG 15.1): paga até o LMI de cada cobertura, sem rateio. A faixa sugerida é o LMI que cobre a perda plausível do evento.

| Cobertura | Fórmula | Origem |
|---|---|---|
| Incêndio, raio, explosão e fumaça | prédio + conteúdo | Perda total possível |
| Danos por água | 10% do prédio + 30% do conteúdo | Premissa |
| Vendaval e granizo | casa 20% / apto 3% do prédio + 10% do conteúdo | Premissa |
| Impacto de veículos | casa 10% / apto 3% do prédio | Premissa |
| Queda de aeronave | 20% de prédio + conteúdo | Premissa |
| Danos elétricos | 50% de eletrônicos e eletrodomésticos | Premissa |
| Roubo e furto mediante arrombamento | 50% do conteúdo | Premissa |
| Quebra de vidros | R$ 50/m² de área; máx ≥ 1,5× gasto com vidraçaria | Premissa |
| Responsabilidade civil familiar | R$ 20–50 mil; R$ 30–100 mil com pet ou dependentes | Referência da equipe |
| Perda ou pagamento de aluguel | 3 a 6 meses do aluguel pago/recebido; proprietário morador: área × aluguel por m² da cidade | CG: até 6 meses, aluguel ≤ LMI/6 |
| Despesas emergenciais | LMI em que 3% ao dia pagam R$ 150–300 por pessoa | CG: 10% nas 48h + 3%/dia |

**Prédio** = área × CUB R8-N da UF × fator de tipo e padrão × interesse segurável. Casa usa o projeto R-1 (1,21× o R8-N); padrão desconhecido vai do meio econômico-normal ao meio normal-superior.

**Largura da faixa.** As incertezas (área, padrão, interesse) são combinadas pela raiz da soma dos quadrados em escala log. Multiplicar todos os extremos suporia que tudo dá errado ao mesmo tempo e gerava faixas de até 3×.

| Cobertura | Mín mediano (R$) | Máx mediano (R$) | Máx/mín mediano | Linhas |
|---|---|---|---|---|
| DANOS_ELETRICOS | 4.850 | 9.750 | 2,0 | 138 |
| DANOS_POR_AGUA | 12.200 | 25.000 | 2,3 | 138 |
| DESPESAS_EMERGENCIAIS | 15.000 | 40.000 | 2,7 | 69 |
| IMPACTO_VEICULOS_TERRESTRES | 900 | 4.450 | 2,8 | 138 |
| INCENDIO_RAIO_EXPLOSAO_FUMACA | 56.400 | 151.600 | 2,4 | 138 |
| PERDA_PAGAMENTO_ALUGUEL | 6.600 | 18.900 | 2,0 | 69 |
| QUEBRA_DE_VIDROS | 5.900 | 8.750 | 1,7 | 124 |
| QUEDA_AERONAVE | 11.300 | 30.300 | 2,4 | 138 |
| RESPONSABILIDADE_CIVIL_FAMILIAR | 30.000 | 100.000 | 3,3 | 69 |
| ROUBO_FURTO_ARROMBAMENTO | 9.400 | 18.400 | 2,0 | 124 |
| VENDAVAL_GRANIZO | 4.000 | 12.450 | 2,4 | 138 |

<details><summary>CUB R8-N usado por UF</summary>

| UF | CUB R8-N (R$/m²) |
|---|---|
| BA | 2.218,68 |
| CE | 2.458,13 |
| DF | 2.416,71 |
| GO | 2.416,71 |
| MG | 2.561,78 |
| PE | 2.240,23 |
| PR | 2.738,93 |
| RJ | 2.476,31 |
| RS | 2.943,73 |
| SP | 2.238,58 |

Goiás usa o valor do DF: o Sinduscon-GO publica como principal a categoria R16-A.

</details>

<details><summary>Parâmetros calibrados na base de desenvolvimento</summary>

| municipio | iptu_anual_por_m2_mediana | aluguel_mensal_por_m2_p25 | aluguel_mensal_por_m2_p75 |
|---|---|---|---|
| Belo Horizonte | 12,0 | 14,4 | 27,4 |
| Brasilia | 15,2 | 7,8 | 23,0 |
| Curitiba | 13,8 | 13,1 | 32,0 |
| Fortaleza | 10,0 | 6,2 | 20,2 |
| Goiania | 11,2 | 14,9 | 23,3 |
| Porto Alegre | 14,1 | 6,9 | 21,0 |
| Recife | 11,3 | 7,7 | 19,8 |
| Rio de Janeiro | 16,7 | 6,6 | 32,6 |
| Salvador | 10,5 | 10,0 | 20,6 |
| Sao Paulo | 18,4 | 13,2 | 32,7 |

IPTU por m² vem de imóveis com área real; aluguel por m² vem de inquilinos com área real.

</details>

## 5. Confiança e canal

- **Confiança de cada cobertura:** média da confiança dos dados que ela usa (alta = 0, média = 1, baixa = 2). Até 0,5 é alta, até 1,2 é média, acima é baixa.
- **Confiança geral:** alta com até 1 campo a confirmar e nenhum conflito; baixa se condicionado, com 4+ campos a confirmar ou 2+ conflitos; média nos demais.
- **Semáforo:** vermelho se condicionado, vínculo a confirmar ou obra a confirmar (vai ao gerente); verde com confiança alta; amarelo nos demais.
- **Canal:** verde + usuário de app = One Click Buy. Dados de app só escolhem o canal, nunca o plano.

| valor | imóveis | % |
|---|---|---|
| AMARELO | 68 | 49,3 |
| VERDE | 47 | 34,1 |
| VERMELHO | 23 | 16,7 |

| valor | imóveis | % |
|---|---|---|
| APP_COM_CONFIRMACAO | 60 | 43,5 |
| ONE_CLICK_BUY | 40 | 29,0 |
| GERENTE | 23 | 16,7 |
| ATENDIMENTO_ASSISTIDO | 15 | 10,9 |

## 6. Casos contrastantes (base de teste)

#### IMO_CASO_00021_01 — Essencial (amarelo)

- **Casa Gêmea:** apartamento em Sao Paulo/SP, proprietário com financiamento, moradia habitual; área 93 m² (estimado); padrão normal (a confirmar).
- **Elegibilidade:** ELEGIVEL
- **Por que este plano:** poucos sinais de necessidade além da proteção básica.
- **Por que não o de baixo:** É o plano de entrada.
- **Por que não o de cima:** O Prático acrescenta roubo e quebra de vidros, mas os sinais de bens de valor são baixos (bens estimados em R$ 7.600 a R$ 15.300).
- **Confiança geral:** MEDIA · **canal:** APP_COM_CONFIRMACAO

| Cobertura | Mín (R$) | Máx (R$) | Confiança |
|---|---|---|---|
| INCENDIO_RAIO_EXPLOSAO_FUMACA | 27.700 | 83.900 | MEDIA |
| DANOS_POR_AGUA | 4.300 | 11.400 | MEDIA |
| VENDAVAL_GRANIZO | 1.400 | 3.600 | MEDIA |
| IMPACTO_VEICULOS_TERRESTRES | 600 | 2.100 | MEDIA |
| QUEDA_AERONAVE | 5.500 | 16.800 | MEDIA |
| DANOS_ELETRICOS | 2.600 | 5.200 | ALTA |

#### IMO_CASO_00010_01 — Essencial (amarelo)

- **Casa Gêmea:** apartamento em Salvador/BA, proprietário quitado, temporada ou segunda residência; área 96 m² (estimado); padrão normal (a confirmar).
- **Elegibilidade:** ELEGIVEL
- **Por que este plano:** poucos sinais de necessidade além da proteção básica.
- **Por que não o de baixo:** É o plano de entrada.
- **Por que não o de cima:** O Prático acrescenta roubo e quebra de vidros, mas os sinais de bens de valor são baixos (bens estimados em R$ 9.100 a R$ 18.200). Alternativa: com pet ou dependentes, o Total vale a pena se o cliente quiser proteção contra danos a terceiros.
- **Confiança geral:** MEDIA · **canal:** APP_COM_CONFIRMACAO

| Cobertura | Mín (R$) | Máx (R$) | Confiança |
|---|---|---|---|
| INCENDIO_RAIO_EXPLOSAO_FUMACA | 29.600 | 88.400 | MEDIA |
| DANOS_POR_AGUA | 4.800 | 12.500 | MEDIA |
| VENDAVAL_GRANIZO | 1.500 | 3.900 | MEDIA |
| IMPACTO_VEICULOS_TERRESTRES | 600 | 2.100 | MEDIA |
| QUEDA_AERONAVE | 5.900 | 17.700 | MEDIA |
| DANOS_ELETRICOS | 3.500 | 7.000 | MEDIA |

#### IMO_CASO_00013_01 — Prático (amarelo)

- **Casa Gêmea:** apartamento em Porto Alegre/RS, proprietário com financiamento, moradia habitual; área 95 m² (observado); padrão superior (estimado).
- **Elegibilidade:** ELEGIVEL
- **Por que este plano:** bens estimados em R$ 14.000 a R$ 28.000; eletrônicos e eletrodomésticos de até R$ 17.600.
- **Por que não o de baixo:** O Essencial não cobre roubo nem quebra de vidros, e há bens estimados em R$ 14.000 a R$ 28.000; eletrônicos e eletrodomésticos de até R$ 17.600.
- **Por que não o de cima:** O Total acrescenta aluguel, RC familiar e despesas emergenciais, mas não paga nem recebe aluguel, então a cobertura de aluguel teria pouco uso. Alternativa: com pet ou dependentes, o Total vale a pena se o cliente quiser proteção contra danos a terceiros.
- **Confiança geral:** MEDIA · **canal:** APP_COM_CONFIRMACAO · **conflitos:** área cadastrada diverge do IPTU e da energia

| Cobertura | Mín (R$) | Máx (R$) | Confiança |
|---|---|---|---|
| INCENDIO_RAIO_EXPLOSAO_FUMACA | 44.700 | 121.700 | MEDIA |
| DANOS_POR_AGUA | 7.300 | 17.800 | MEDIA |
| VENDAVAL_GRANIZO | 2.300 | 5.600 | MEDIA |
| IMPACTO_VEICULOS_TERRESTRES | 900 | 2.800 | ALTA |
| QUEDA_AERONAVE | 8.900 | 24.300 | MEDIA |
| DANOS_ELETRICOS | 4.400 | 8.800 | ALTA |
| ROUBO_FURTO_ARROMBAMENTO | 7.000 | 14.000 | ALTA |
| QUEBRA_DE_VIDROS | 4.800 | 4.800 | ALTA |

#### IMO_CASO_00001_01 — Prático (amarelo)

- **Casa Gêmea:** casa em condomínio em Recife/PE, proprietário quitado, moradia habitual; área 263 m² (estimado); padrão normal (a confirmar).
- **Elegibilidade:** ELEGIVEL
- **Por que este plano:** bens estimados em R$ 22.700 a R$ 45.400; eletrônicos e eletrodomésticos de até R$ 27.200; casa: mais portas e janelas expostas a arrombamento.
- **Por que não o de baixo:** O Essencial não cobre roubo nem quebra de vidros, e há bens estimados em R$ 22.700 a R$ 45.400; eletrônicos e eletrodomésticos de até R$ 27.200; casa: mais portas e janelas expostas a arrombamento.
- **Por que não o de cima:** O Total acrescenta aluguel, RC familiar e despesas emergenciais, mas não paga nem recebe aluguel, então a cobertura de aluguel teria pouco uso. Alternativa: com pet ou dependentes, o Total vale a pena se o cliente quiser proteção contra danos a terceiros.
- **Confiança geral:** MEDIA · **canal:** APP_COM_CONFIRMACAO

| Cobertura | Mín (R$) | Máx (R$) | Confiança |
|---|---|---|---|
| INCENDIO_RAIO_EXPLOSAO_FUMACA | 498.100 | 923.800 | MEDIA |
| DANOS_POR_AGUA | 54.300 | 101.500 | MEDIA |
| VENDAVAL_GRANIZO | 97.300 | 180.200 | MEDIA |
| IMPACTO_VEICULOS_TERRESTRES | 47.500 | 87.800 | MEDIA |
| QUEDA_AERONAVE | 99.600 | 184.800 | MEDIA |
| DANOS_ELETRICOS | 6.800 | 13.600 | MEDIA |
| ROUBO_FURTO_ARROMBAMENTO | 11.400 | 22.700 | MEDIA |
| QUEBRA_DE_VIDROS | 10.100 | 17.200 | ALTA |

#### IMO_CASO_00008_01 — Total (amarelo)

- **Casa Gêmea:** apartamento em Fortaleza/CE, inquilino, moradia habitual; área 125 m² (observado); padrão superior (estimado).
- **Elegibilidade:** ELEGIVEL
- **Por que este plano:** paga aluguel de R$ 1.500: se o imóvel ficar inabitável, continua devendo o aluguel; tem pet: danos a terceiros causados pelo animal; 3 dependente(s): danos a terceiros e despesas de hospedagem da família; bens estimados em R$ 9.300 a R$ 18.600.
- **Por que não o de baixo:** O Prático não cobre aluguel, RC familiar nem despesas emergenciais, e o cliente paga aluguel de R$ 1.500: se o imóvel ficar inabitável, continua devendo o aluguel; tem pet: danos a terceiros causados pelo animal; 3 dependente(s): danos a terceiros e despesas de hospedagem da família.
- **Por que não o de cima:** É o plano mais completo.
- **Confiança geral:** MEDIA · **canal:** APP_COM_CONFIRMACAO · **conflitos:** apartamento sem condomínio pago

| Cobertura | Mín (R$) | Máx (R$) | Confiança |
|---|---|---|---|
| INCENDIO_RAIO_EXPLOSAO_FUMACA | 9.300 | 56.200 | MEDIA |
| DANOS_POR_AGUA | 2.800 | 9.300 | MEDIA |
| VENDAVAL_GRANIZO | 900 | 3.000 | MEDIA |
| IMPACTO_VEICULOS_TERRESTRES | 500 | 1.100 | MEDIA |
| QUEDA_AERONAVE | 1.900 | 11.200 | MEDIA |
| DANOS_ELETRICOS | 3.500 | 6.000 | ALTA |
| ROUBO_FURTO_ARROMBAMENTO | 4.600 | 9.300 | ALTA |
| QUEBRA_DE_VIDROS | 6.200 | 6.200 | ALTA |
| RESPONSABILIDADE_CIVIL_FAMILIAR | 30.000 | 100.000 | BAIXA |
| PERDA_PAGAMENTO_ALUGUEL | 4.500 | 9.000 | ALTA |
| DESPESAS_EMERGENCIAIS | 20.000 | 50.000 | MEDIA |

#### IMO_CASO_00006_01 — Total (amarelo)

- **Casa Gêmea:** apartamento em Goiania/GO, proprietário com financiamento, moradia habitual; área 145 m² (observado); padrão normal (estimado).
- **Elegibilidade:** ELEGIVEL
- **Por que este plano:** tem pet: danos a terceiros causados pelo animal; 1 dependente(s): danos a terceiros e despesas de hospedagem da família; bens estimados em R$ 11.100 a R$ 22.200; eletrônicos e eletrodomésticos de até R$ 15.400.
- **Por que não o de baixo:** O Prático não cobre aluguel, RC familiar nem despesas emergenciais, e o cliente tem pet: danos a terceiros causados pelo animal; 1 dependente(s): danos a terceiros e despesas de hospedagem da família.
- **Por que não o de cima:** É o plano mais completo.
- **Confiança geral:** MEDIA · **canal:** APP_COM_CONFIRMACAO · **conflitos:** apartamento sem condomínio pago

| Cobertura | Mín (R$) | Máx (R$) | Confiança |
|---|---|---|---|
| INCENDIO_RAIO_EXPLOSAO_FUMACA | 46.100 | 127.300 | MEDIA |
| DANOS_POR_AGUA | 6.800 | 17.200 | MEDIA |
| VENDAVAL_GRANIZO | 2.200 | 5.400 | MEDIA |
| IMPACTO_VEICULOS_TERRESTRES | 1.100 | 3.200 | MEDIA |
| QUEDA_AERONAVE | 9.200 | 25.500 | MEDIA |
| DANOS_ELETRICOS | 3.800 | 7.700 | ALTA |
| ROUBO_FURTO_ARROMBAMENTO | 5.600 | 11.100 | ALTA |
| QUEBRA_DE_VIDROS | 7.200 | 7.200 | ALTA |
| RESPONSABILIDADE_CIVIL_FAMILIAR | 30.000 | 100.000 | BAIXA |
| PERDA_PAGAMENTO_ALUGUEL | 6.500 | 20.300 | ALTA |
| DESPESAS_EMERGENCIAIS | 10.000 | 30.000 | MEDIA |

#### IMO_CASO_00038_01 — Total (amarelo)

- **Casa Gêmea:** apartamento em Salvador/BA, proprietário que aluga a terceiros, alugado a terceiros; área 79 m² (estimado); padrão normal (a confirmar).
- **Elegibilidade:** ELEGIVEL
- **Por que este plano:** recebe cerca de R$ 1.000/mês de aluguel: renda que pararia após um sinistro; 2 dependente(s): danos a terceiros e despesas de hospedagem da família; bens estimados em R$ 8.600 a R$ 17.100.
- **Por que não o de baixo:** O Prático não cobre aluguel, RC familiar nem despesas emergenciais, e o cliente recebe cerca de R$ 1.000/mês de aluguel: renda que pararia após um sinistro; 2 dependente(s): danos a terceiros e despesas de hospedagem da família.
- **Por que não o de cima:** É o plano mais completo.
- **Confiança geral:** MEDIA · **canal:** APP_COM_CONFIRMACAO

| Cobertura | Mín (R$) | Máx (R$) | Confiança |
|---|---|---|---|
| INCENDIO_RAIO_EXPLOSAO_FUMACA | 25.500 | 74.800 | MEDIA |
| DANOS_POR_AGUA | 4.300 | 10.900 | MEDIA |
| VENDAVAL_GRANIZO | 1.400 | 3.400 | MEDIA |
| IMPACTO_VEICULOS_TERRESTRES | 500 | 1.700 | MEDIA |
| QUEDA_AERONAVE | 5.100 | 15.000 | MEDIA |
| DANOS_ELETRICOS | 2.600 | 5.200 | BAIXA |
| ROUBO_FURTO_ARROMBAMENTO | 4.300 | 8.600 | BAIXA |
| QUEBRA_DE_VIDROS | 3.000 | 5.200 | ALTA |
| RESPONSABILIDADE_CIVIL_FAMILIAR | 30.000 | 100.000 | BAIXA |
| PERDA_PAGAMENTO_ALUGUEL | 3.000 | 6.000 | MEDIA |
| DESPESAS_EMERGENCIAIS | 15.000 | 40.000 | MEDIA |

#### IMO_CASO_00007_01 — Total (amarelo)

- **Casa Gêmea:** casa em Sao Paulo/SP, proprietário quitado, moradia habitual; área 122 m² (estimado); padrão normal (a confirmar).
- **Elegibilidade:** ELEGIVEL
- **Por que este plano:** tem pet: danos a terceiros causados pelo animal; 1 dependente(s): danos a terceiros e despesas de hospedagem da família; bens estimados em R$ 19.700 a R$ 39.400; eletrônicos e eletrodomésticos de até R$ 22.000; casa: mais portas e janelas expostas a arrombamento.
- **Por que não o de baixo:** O Prático não cobre aluguel, RC familiar nem despesas emergenciais, e o cliente tem pet: danos a terceiros causados pelo animal; 1 dependente(s): danos a terceiros e despesas de hospedagem da família.
- **Por que não o de cima:** É o plano mais completo.
- **Confiança geral:** MEDIA · **canal:** APP_COM_CONFIRMACAO

| Cobertura | Mín (R$) | Máx (R$) | Confiança |
|---|---|---|---|
| INCENDIO_RAIO_EXPLOSAO_FUMACA | 271.000 | 485.800 | MEDIA |
| DANOS_POR_AGUA | 31.000 | 56.500 | MEDIA |
| VENDAVAL_GRANIZO | 52.200 | 93.200 | MEDIA |
| IMPACTO_VEICULOS_TERRESTRES | 25.100 | 44.600 | BAIXA |
| QUEDA_AERONAVE | 54.200 | 97.200 | MEDIA |
| DANOS_ELETRICOS | 5.500 | 11.000 | MEDIA |
| ROUBO_FURTO_ARROMBAMENTO | 9.800 | 19.700 | MEDIA |
| QUEBRA_DE_VIDROS | 4.700 | 8.000 | MEDIA |
| RESPONSABILIDADE_CIVIL_FAMILIAR | 30.000 | 100.000 | BAIXA |
| PERDA_PAGAMENTO_ALUGUEL | 3.700 | 31.600 | MEDIA |
| DESPESAS_EMERGENCIAIS | 10.000 | 30.000 | MEDIA |

#### IMO_CASO_00058_02 — Essencial (amarelo)

- **Casa Gêmea:** apartamento em Porto Alegre/RS, proprietário com financiamento, moradia habitual; área 135 m² (estimado); padrão normal (a confirmar).
- **Elegibilidade:** ELEGIVEL
- **Por que este plano:** poucos sinais de necessidade além da proteção básica.
- **Por que não o de baixo:** É o plano de entrada.
- **Por que não o de cima:** O Prático acrescenta roubo e quebra de vidros, mas os sinais de bens de valor são baixos (bens estimados em R$ 8.900 a R$ 17.800). Alternativa: com pet ou dependentes, o Total vale a pena se o cliente quiser proteção contra danos a terceiros.
- **Confiança geral:** MEDIA · **canal:** APP_COM_CONFIRMACAO · **conflitos:** apartamento sem condomínio pago

| Cobertura | Mín (R$) | Máx (R$) | Confiança |
|---|---|---|---|
| INCENDIO_RAIO_EXPLOSAO_FUMACA | 47.100 | 149.000 | MEDIA |
| DANOS_POR_AGUA | 6.500 | 18.500 | MEDIA |
| VENDAVAL_GRANIZO | 2.000 | 5.700 | MEDIA |
| IMPACTO_VEICULOS_TERRESTRES | 1.100 | 3.900 | MEDIA |
| QUEDA_AERONAVE | 9.400 | 29.800 | MEDIA |
| DANOS_ELETRICOS | 2.800 | 5.700 | MEDIA |

#### IMO_CASO_00080_01 — Essencial (amarelo)

- **Casa Gêmea:** apartamento em Sao Paulo/SP, proprietário com financiamento, moradia habitual; área 125 m² (estimado); padrão normal (a confirmar).
- **Elegibilidade:** ELEGIVEL
- **Por que este plano:** poucos sinais de necessidade além da proteção básica.
- **Por que não o de baixo:** É o plano de entrada.
- **Por que não o de cima:** O Prático acrescenta roubo e quebra de vidros, mas os sinais de bens de valor são baixos (bens estimados em R$ 11.000 a R$ 22.100).
- **Confiança geral:** MEDIA · **canal:** APP_COM_CONFIRMACAO · **conflitos:** apartamento sem condomínio pago

| Cobertura | Mín (R$) | Máx (R$) | Confiança |
|---|---|---|---|
| INCENDIO_RAIO_EXPLOSAO_FUMACA | 37.900 | 114.400 | MEDIA |
| DANOS_POR_AGUA | 6.000 | 15.900 | MEDIA |
| VENDAVAL_GRANIZO | 1.900 | 5.000 | MEDIA |
| IMPACTO_VEICULOS_TERRESTRES | 800 | 2.800 | MEDIA |
| QUEDA_AERONAVE | 7.600 | 22.900 | MEDIA |
| DANOS_ELETRICOS | 3.200 | 6.500 | ALTA |

## Limitações

- Os percentuais de perda por evento (danos por água, vendaval, impacto, aeronave, elétricos, roubo) e as faixas de RC familiar são premissas da equipe, sem dado de sinistro por imóvel.
- O CUB vem de agregador secundário (myside.com.br) que cita os Sinduscons; meses de referência diferem entre UFs (ago e set/2026). Goiás usa o DF como proxy.
- Os fatores de padrão vêm da tabela de Minas Gerais (abr/2025) e foram aplicados a todas as UFs.
- O CUB não inclui fundações, elevadores e áreas externas; a reconstrução real pode ser maior.
- A base não informa se o financiamento tem seguro habitacional; por isso a faixa do prédio financiado começa em 50%.
- Os nomes Essencial, Prático e Total não aparecem nas Condições Gerais; a composição de cada plano segue o catálogo do datathon.
