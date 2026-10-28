# Etapa 02 — Regras do seguro
<<<<<<< Updated upstream
_Gerado por `scripts/02_aplicar_regras.py` em 28/10/2026. Tempo de execução: 4,4 s para 2716 imóveis._
=======
_Gerado por `scripts/02_aplicar_regras.py` em 28/10/2026. Tempo de execução: 3,1 s para 2716 imóveis._
>>>>>>> Stashed changes

Na base de teste, **138 de 138 imóveis** receberam elegibilidade, plano, 1283 linhas de cobertura com faixa em reais, confiança, justificativa e comparação com os planos vizinhos.

## Fontes

| Fonte | Uso |
|---|---|
| Guia dos Times, seção 9 | Elegibilidade, planos e coberturas fixas |
| [Condições Gerais do Seguro Residencial BB Seguros, Processo SUSEP 15414.606453/2020-10, V1.6 (vigência desde 11/08/2026)](https://www.bbseguros.com.br/seguros/seguro-residencial) | Exclusões, bens não cobertos, Primeiro Risco Absoluto, regras de aluguel e despesas emergenciais (citadas como "CG") |
| CUB R8-N por UF (Sinduscons, ago–set/2026) | Custo de reconstrução por m² (`dados_externos/cub_r8n_por_uf.csv`) |
| Tabela CUB Sinduscon-MG (abr/2025) | Fatores de tipo e padrão (`dados_externos/fatores_cub_padrao.csv`) |
| [Monitor Mercantil, 21/07/2026](https://monitormercantil.com.br/?p=332625) | Distribuição de sinistros da carteira residencial BB Seguros |

Detalhes de cada fonte em `docs/fontes_externas.md`.

## 1. Elegibilidade

Aplicada antes de recomendar (guia, seção 2).

| Resultado | Quando | Base |
|---|---|---|
| INELEGIVEL | Situação cadastral diferente de REGULAR; parede de material combustível | Guia 9.1 |
| ELEGIVEL_CONDICIONADO | Possível obra relevante (material de construção ≥ R$ 30 mil, ou ≥ R$ 10 mil + vidraçaria); tipo não identificado | Guia 9.1; CG 7.1 w/x excluem imóveis em reforma ou construção |
| ELEGIVEL | Demais casos, sujeitos à declaração do cliente (área urbana, alvenaria, sem obra estrutural, não tombado) | CG 11, alínea a, e 12.2: declaração inexata faz perder o direito |

| valor | imóveis | % |
|---|---|---|
| ELEGIVEL | 135 | 97,8 |
| ELEGIVEL_CONDICIONADO | 3 | 2,2 |

## 2. Interesse segurável (quanto do imóvel é do cliente)

| Situação | Prédio | Conteúdo | Base |
|---|---|---|---|
| Inquilino | 3% a 10% (benfeitorias) | 100% | CG 10: beneficiário é o proprietário |
| Apartamento (proprietário) | 10% a 30% (partes privativas) | 100% | CG 5.3 e 15.2.1: estrutura no seguro do condomínio |
| Casa financiada | 50% a 100% | 100% | CG 15.2.1: com seguro habitacional, o residencial atua primeiro no conteúdo e complementa a estrutura |
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
| Quebra de vidros | R$ 40 a R$ 60/m² de área; máx ≥ 1,5× gasto com vidraçaria | Premissa |
| Responsabilidade civil familiar | R$ 20–50 mil, mais R$ 10–30 mil com pet e R$ 5–10 mil por dependente (até 3) | Referência da equipe |
| Perda ou pagamento de aluguel | 3 a 6 meses do aluguel pago/recebido; proprietário morador: área × aluguel por m² da cidade | CG: até 6 meses, aluguel ≤ LMI/6 |
| Despesas emergenciais | LMI em que 3% ao dia pagam R$ 150–300 por pessoa | CG: 10% nas 48h + 3%/dia |

**Prédio** = área × CUB R8-N da UF × fator de tipo e padrão × interesse segurável. Casa usa o projeto R-1 (1,21× o R8-N); padrão desconhecido vai do meio econômico-normal ao meio normal-superior.

**Largura da faixa.** As incertezas (área, padrão, interesse) são combinadas pela raiz da soma dos quadrados em escala log. Multiplicar todos os extremos suporia que tudo dá errado ao mesmo tempo e gerava faixas de até 3×.

| Cobertura | Mín mediano (R$) | Máx mediano (R$) | Máx/mín mediano | Linhas |
|---|---|---|---|---|
| DANOS_ELETRICOS | 4.850 | 9.750 | 2,0 | 138 |
| DANOS_POR_AGUA | 12.350 | 24.800 | 2,2 | 138 |
| DESPESAS_EMERGENCIAIS | 15.000 | 40.000 | 2,7 | 69 |
| IMPACTO_VEICULOS_TERRESTRES | 1.300 | 4.050 | 2,6 | 138 |
| INCENDIO_RAIO_EXPLOSAO_FUMACA | 59.050 | 149.300 | 2,4 | 138 |
| PERDA_PAGAMENTO_ALUGUEL | 6.900 | 17.700 | 2,0 | 69 |
| QUEBRA_DE_VIDROS | 4.750 | 10.500 | 2,5 | 124 |
| QUEDA_AERONAVE | 11.800 | 29.850 | 2,4 | 138 |
| RESPONSABILIDADE_CIVIL_FAMILIAR | 35.000 | 80.000 | 2,5 | 69 |
| ROUBO_FURTO_ARROMBAMENTO | 9.400 | 18.400 | 2,0 | 124 |
| VENDAVAL_GRANIZO | 5.100 | 12.450 | 2,3 | 138 |

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
- **Confiança geral:** mede a chance de o plano mudar depois das perguntas (ver seção 7). Alta: nenhuma resposta plausível muda o plano. Média: um campo pode mudar o plano. Baixa: dois ou mais campos podem mudar o plano, ou a elegibilidade depende de confirmação.
- **Semáforo:** vermelho se condicionado, vínculo a confirmar ou obra a confirmar (vai ao gerente); verde com confiança alta; amarelo nos demais.
- **Canal:** verde + usuário de app = One Click Buy. Dados de app só escolhem o canal, nunca o plano.

| valor | imóveis | % |
|---|---|---|
| VERDE | 100 | 72,5 |
| VERMELHO | 23 | 16,7 |
| AMARELO | 15 | 10,9 |

| valor | imóveis | % |
|---|---|---|
| ONE_CLICK_BUY | 88 | 63,8 |
| GERENTE | 23 | 16,7 |
| ATENDIMENTO_ASSISTIDO | 15 | 10,9 |
| APP_COM_CONFIRMACAO | 12 | 8,7 |

## 6. Personalização: coberturas adicionais

O produto permite incluir coberturas além do plano, pagas à parte (CG 4.1). O motor sugere só as que têm sinal nos dados do cliente (`src/casa_gemea/adicionais.py`); elas não entram no template de coberturas, que segue o catálogo dos planos.

| Adicional | Quando é sugerido | Por quê |
|---|---|---|
| Responsabilidade Civil Familiar (CG 4.1 m) | Pet ou dependentes, plano Essencial ou Prático | Quem não precisa do Total inteiro ainda pode cobrir danos a terceiros |
| Equipamentos Portáteis (CG 4.1 g) | Eletrônicos do cliente ≥ 15.000 reais | Cobre queda e quebra acidental, que nenhum plano cobre |
| Bicicleta (CG 4.1 b) | Itens de lazer ≥ 5.000 reais | Roubo também fora de casa; sugerida como pergunta ("se houver bicicleta") |
| Desocupação Temporária (CG 4.1 f) | Segunda residência ou imóvel vazio | Mantém a proteção em períodos de 30 a 60 dias sem moradores |

Alagamento, Danos por Chuva e Rompimento de Tubulações não são sugeridos: Danos por Água, presente nos três planos, já os contempla (CG 4.3). Os limiares de valor ficam no quinto superior da base de teste, para sugerir só onde há valor em jogo.

Adicionais sugeridos por imóvel (base de teste):

| valor | imóveis | % |
|---|---|---|
| 0 | 56 | 40,6 |
| 1 | 55 | 39,9 |
| 2 | 23 | 16,7 |
| 3 | 4 | 2,9 |

## 7. Perguntas que mudam o resultado

Para cada campo incerto, o motor simula as respostas plausíveis e refaz a recomendação (`src/casa_gemea/perguntas.py`).

| Campo | Respostas simuladas | Efeito medido |
|---|---|---|
| Obra | — | define a elegibilidade (sempre perguntada se houver sinal) |
| Vínculo | locador → proprietário sem renda do imóvel | plano |
| Tipo | apartamento ↔ casa (quando a confiança não é alta) | plano |
| Ocupação | segunda residência desocupada por longos períodos (sem cobertura de roubo) | plano |
| Bens | valor no mínimo e no máximo da faixa | plano e faixa |
| Área | área confirmada no valor estimado | faixa |
| Padrão | padrão confirmado | faixa |

**Regra de parada:** pergunta-se só o que muda o plano, define a elegibilidade ou estreita a faixa de incêndio em pelo menos 25%, enquanto a faixa tiver máximo mais de 30% acima do mínimo. Ordem: elegibilidade → plano → faixa. No fim, uma **declaração única** (área urbana, alvenaria, sem obra estrutural, não tombado) substitui várias perguntas de elegibilidade.

Perguntas por imóvel (base de teste, sem contar a declaração):

| valor | imóveis | % |
|---|---|---|
| 1 | 79 | 57,2 |
| 0 | 44 | 31,9 |
| 2 | 12 | 8,7 |
| 3 | 3 | 2,2 |

Campos que podem mudar o plano (base de desenvolvimento, imóveis):

| valor | imóveis | % |
|---|---|---|
| conteudo | 328 | 46,6 |
| vinculo | 188 | 26,7 |
| ocupacao | 100 | 14,2 |
| tipo_imovel | 88 | 12,5 |

## 8. Validação das faixas escondendo dados reais

Nos 1016 imóveis da base de desenvolvimento com área cadastrada, o motor foi rodado escondendo a área e o padrão construtivo, com o modelo de área retreinado em validação cruzada (5 dobras: nenhum imóvel é avaliado por um modelo que o viu). Valor real = centro da faixa calculada com os dados cadastrados (`src/casa_gemea/validacao.py`).

| Cobertura | Imóveis | Faixa contém o real (%) | Erro mediano do centro (%) |
|---|---|---|---|
| INCENDIO_RAIO_EXPLOSAO_FUMACA | 1016 | 97,2 | 8,0 |
| DANOS_POR_AGUA | 1016 | 98,1 | 5,4 |
| VENDAVAL_GRANIZO | 1016 | 96,9 | 6,4 |
| IMPACTO_VEICULOS_TERRESTRES | 1016 | 96,1 | 10,3 |
| QUEDA_AERONAVE | 1016 | 97,2 | 8,0 |
| QUEBRA_DE_VIDROS | 1016 | 97,3 | 13,3 |

No total, a faixa contém o valor real em **97,1%** dos casos. As faixas de prédio são conservadoras porque também carregam a incerteza do interesse segurável (ex.: partes privativas de apartamento de 10% a 30%), que não é testada aqui. Quebra de vidros depende só da área e acompanha o intervalo de 80% do modelo de área. **Atenção:** aqui o "valor real" é o centro da faixa calculada com os dados cadastrados (inclusive o padrão estimado pelo IPTU), então este número é otimista. Contra o custo de reconstrução verdadeiro (área real × CUB × fator do padrão real), a cobertura medida em `docs/12_avaliacao_modelo.md` (E3) é de cerca de 89%.

## 9. Testado e descartado

| Ideia | Resultado na base de desenvolvimento | Decisão |
|---|---|---|
| Padrão construtivo pelo condomínio por m² (apartamentos) | Acerto de 48% a 54% contra 58% de chutar NORMAL; aponta SUPERIOR com 44% de acerto (frequência real 23%) | Não entra: pior que a referência |
| Locador mais preciso (aluguel recebido × aluguel por m² da cidade; regularidade dos créditos) | Distribuições iguais entre locadores com e sem conflito de endereço (razão mediana 1,44 × 1,59; mesma regularidade) | Não entra: o sinal não separa os grupos; o vínculo vira pergunta |
| Ajuste de RC familiar para clientes com 2 imóveis | CG, RC Familiar 1.1: a cobertura é ligada ao imóvel segurado | Sem mudança: não há duplicidade |
| Confiança geral por contagem de campos a confirmar | Marcava como média campos que não mudam nada (ex.: área de quem já é Total) | Substituída pela análise de impacto |

## 10. Casos contrastantes (base de teste)

#### IMO_CASO_00058_02 — Essencial (amarelo)

- **Casa Gêmea:** apartamento em Porto Alegre/RS, proprietário com financiamento, moradia habitual; área 135 m² (estimado); padrão normal (a confirmar).
- **Elegibilidade:** ELEGIVEL
- **Por que este plano:** poucos sinais de necessidade além da proteção básica.
- **Por que não o de baixo:** É o plano de entrada.
- **Por que não o de cima:** O Prático acrescenta roubo e quebra de vidros, mas os sinais de bens de valor são baixos (bens estimados em R$ 8.900 a R$ 17.800). Como o cliente tem 2 dependentes, a RC familiar pode ser incluída como opcional, sem migrar para o Total.
- **Confiança geral:** MEDIA · **canal:** APP_COM_CONFIRMACAO · **conflitos:** apartamento sem condomínio pago

| Cobertura | Mín (R$) | Máx (R$) | Confiança |
|---|---|---|---|
| INCENDIO_RAIO_EXPLOSAO_FUMACA | 47.100 | 149.000 | MEDIA |
| DANOS_POR_AGUA | 6.500 | 18.500 | MEDIA |
| VENDAVAL_GRANIZO | 2.000 | 5.700 | MEDIA |
| IMPACTO_VEICULOS_TERRESTRES | 1.100 | 3.900 | MEDIA |
| QUEDA_AERONAVE | 9.400 | 29.800 | MEDIA |
| DANOS_ELETRICOS | 2.800 | 5.700 | MEDIA |

#### IMO_CASO_00109_01 — Essencial (amarelo)

- **Casa Gêmea:** apartamento em Rio de Janeiro/RJ, proprietário quitado, moradia habitual; área 95 m² (observado); padrão normal (observado).
- **Elegibilidade:** ELEGIVEL
- **Por que este plano:** poucos sinais de necessidade além da proteção básica.
- **Por que não o de baixo:** É o plano de entrada.
- **Por que não o de cima:** O Prático acrescenta roubo e quebra de vidros, mas os sinais de bens de valor são baixos (bens estimados em R$ 9.500 a R$ 19.000). Como o cliente tem 1 dependente, a RC familiar pode ser incluída como opcional, sem migrar para o Total.
- **Confiança geral:** MEDIA · **canal:** ATENDIMENTO_ASSISTIDO · **conflitos:** apartamento sem condomínio pago

| Cobertura | Mín (R$) | Máx (R$) | Confiança |
|---|---|---|---|
| INCENDIO_RAIO_EXPLOSAO_FUMACA | 33.000 | 89.600 | ALTA |
| DANOS_POR_AGUA | 5.200 | 12.800 | ALTA |
| VENDAVAL_GRANIZO | 1.700 | 4.000 | ALTA |
| IMPACTO_VEICULOS_TERRESTRES | 700 | 2.100 | ALTA |
| QUEDA_AERONAVE | 6.600 | 17.900 | ALTA |
| DANOS_ELETRICOS | 2.300 | 4.600 | ALTA |

#### IMO_CASO_00013_01 — Prático (amarelo)

- **Casa Gêmea:** apartamento em Porto Alegre/RS, proprietário com financiamento, moradia habitual; área 95 m² (observado); padrão superior (estimado).
- **Elegibilidade:** ELEGIVEL
- **Por que este plano:** bens estimados em R$ 14.000 a R$ 28.000; eletrônicos e eletrodomésticos de até R$ 17.600.
- **Por que não o de baixo:** O Essencial não cobre roubo nem quebra de vidros, que protegem os bens e os acessos citados acima.
- **Por que não o de cima:** O Total acrescenta aluguel, RC familiar e despesas emergenciais, mas o cliente não paga nem recebe aluguel: a cobertura de aluguel só pagaria uma moradia temporária se o imóvel ficasse inabitável, sem perda de renda. São proteções úteis, mas não prioritárias para este perfil. Como o cliente tem 1 dependente, a RC familiar pode ser incluída como opcional, sem migrar para o Total.
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
| QUEBRA_DE_VIDROS | 3.800 | 5.700 | ALTA |

#### IMO_CASO_00045_01 — Prático (amarelo)

- **Casa Gêmea:** apartamento em Fortaleza/CE, proprietário quitado, moradia habitual; área 107 m² (estimado); padrão normal (a confirmar).
- **Elegibilidade:** ELEGIVEL
- **Por que este plano:** bens estimados em R$ 18.600 a R$ 37.100; eletrônicos e eletrodomésticos de até R$ 23.800.
- **Por que não o de baixo:** O Essencial não cobre roubo nem quebra de vidros, que protegem os bens e os acessos citados acima.
- **Por que não o de cima:** O Total acrescenta aluguel, RC familiar e despesas emergenciais, mas o cliente não paga nem recebe aluguel: a cobertura de aluguel só pagaria uma moradia temporária se o imóvel ficasse inabitável, sem perda de renda. São proteções úteis, mas não prioritárias para este perfil. Como o cliente tem 3 dependentes, a RC familiar pode ser incluída como opcional, sem migrar para o Total.
- **Confiança geral:** MEDIA · **canal:** ATENDIMENTO_ASSISTIDO

| Cobertura | Mín (R$) | Máx (R$) | Confiança |
|---|---|---|---|
| INCENDIO_RAIO_EXPLOSAO_FUMACA | 43.900 | 124.000 | MEDIA |
| DANOS_POR_AGUA | 8.100 | 19.800 | MEDIA |
| VENDAVAL_GRANIZO | 2.600 | 6.300 | MEDIA |
| IMPACTO_VEICULOS_TERRESTRES | 800 | 2.600 | MEDIA |
| QUEDA_AERONAVE | 8.800 | 24.800 | MEDIA |
| DANOS_ELETRICOS | 6.000 | 11.900 | MEDIA |
| ROUBO_FURTO_ARROMBAMENTO | 9.300 | 18.600 | MEDIA |
| QUEBRA_DE_VIDROS | 3.300 | 8.500 | MEDIA |

#### IMO_CASO_00008_01 — Total (verde)

- **Casa Gêmea:** apartamento em Fortaleza/CE, inquilino, moradia habitual; área 125 m² (observado); padrão superior (estimado).
- **Elegibilidade:** ELEGIVEL
- **Por que este plano:** paga aluguel de R$ 1.500: se o imóvel ficar inabitável, continua devendo o aluguel; tem pet: danos a terceiros causados pelo animal; 3 dependentes: danos a terceiros e despesas de hospedagem da família; bens estimados em R$ 9.300 a R$ 18.600.
- **Por que não o de baixo:** O Prático não cobre aluguel, RC familiar nem despesas emergenciais, que respondem aos sinais citados acima. Em reais: o cliente paga cerca de R$ 1.500/mês de aluguel, então até R$ 4.500 a R$ 9.000 ficariam sem proteção se o imóvel ficasse inabitável.
- **Por que não o de cima:** É o plano mais completo.
- **Confiança geral:** ALTA · **canal:** ONE_CLICK_BUY · **conflitos:** apartamento sem condomínio pago

| Cobertura | Mín (R$) | Máx (R$) | Confiança |
|---|---|---|---|
| INCENDIO_RAIO_EXPLOSAO_FUMACA | 19.400 | 52.900 | MEDIA |
| DANOS_POR_AGUA | 3.800 | 9.000 | MEDIA |
| VENDAVAL_GRANIZO | 1.200 | 2.900 | MEDIA |
| IMPACTO_VEICULOS_TERRESTRES | 500 | 1.000 | MEDIA |
| QUEDA_AERONAVE | 3.900 | 10.600 | MEDIA |
| DANOS_ELETRICOS | 3.500 | 6.000 | ALTA |
| ROUBO_FURTO_ARROMBAMENTO | 4.600 | 9.300 | ALTA |
| QUEBRA_DE_VIDROS | 5.000 | 7.500 | ALTA |
| RESPONSABILIDADE_CIVIL_FAMILIAR | 45.000 | 110.000 | BAIXA |
| PERDA_PAGAMENTO_ALUGUEL | 4.500 | 9.000 | ALTA |
| DESPESAS_EMERGENCIAIS | 20.000 | 50.000 | MEDIA |

#### IMO_CASO_00004_01 — Total (verde)

- **Casa Gêmea:** apartamento em Brasilia/DF, proprietário com financiamento, moradia habitual; área 105 m² (observado); padrão econômico (observado).
- **Elegibilidade:** ELEGIVEL
- **Por que este plano:** tem pet: danos a terceiros causados pelo animal; 1 dependente: danos a terceiros e despesas de hospedagem da família; bens estimados em R$ 23.400 a R$ 46.800; eletrônicos e eletrodomésticos de até R$ 27.400.
- **Por que não o de baixo:** O Prático não cobre aluguel, RC familiar nem despesas emergenciais, que respondem aos sinais citados acima.
- **Por que não o de cima:** É o plano mais completo.
- **Confiança geral:** ALTA · **canal:** ATENDIMENTO_ASSISTIDO

| Cobertura | Mín (R$) | Máx (R$) | Confiança |
|---|---|---|---|
| INCENDIO_RAIO_EXPLOSAO_FUMACA | 46.300 | 115.500 | ALTA |
| DANOS_POR_AGUA | 9.300 | 20.900 | ALTA |
| VENDAVAL_GRANIZO | 3.000 | 6.700 | ALTA |
| IMPACTO_VEICULOS_TERRESTRES | 700 | 2.100 | ALTA |
| QUEDA_AERONAVE | 9.300 | 23.100 | ALTA |
| DANOS_ELETRICOS | 6.800 | 13.700 | ALTA |
| ROUBO_FURTO_ARROMBAMENTO | 11.700 | 23.400 | ALTA |
| QUEBRA_DE_VIDROS | 4.200 | 6.300 | ALTA |
| RESPONSABILIDADE_CIVIL_FAMILIAR | 35.000 | 90.000 | BAIXA |
| PERDA_PAGAMENTO_ALUGUEL | 2.400 | 14.500 | ALTA |
| DESPESAS_EMERGENCIAIS | 10.000 | 30.000 | MEDIA |

#### IMO_CASO_00038_01 — Total (amarelo)

- **Casa Gêmea:** apartamento em Salvador/BA, proprietário que aluga a terceiros, alugado a terceiros; área 79 m² (estimado); padrão normal (a confirmar).
- **Elegibilidade:** ELEGIVEL
- **Por que este plano:** recebe cerca de R$ 1.000/mês de aluguel: renda que pararia após um sinistro; 2 dependentes: danos a terceiros e despesas de hospedagem da família; bens estimados em R$ 8.600 a R$ 17.100.
- **Por que não o de baixo:** O Prático não cobre aluguel, RC familiar nem despesas emergenciais, que respondem aos sinais citados acima. Em reais: o cliente recebe cerca de R$ 1.000/mês de aluguel, então até R$ 3.000 a R$ 6.000 ficariam sem proteção se o imóvel ficasse inabitável.
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
| QUEBRA_DE_VIDROS | 2.400 | 6.200 | MEDIA |
| RESPONSABILIDADE_CIVIL_FAMILIAR | 30.000 | 70.000 | BAIXA |
| PERDA_PAGAMENTO_ALUGUEL | 3.000 | 6.000 | MEDIA |
| DESPESAS_EMERGENCIAIS | 15.000 | 40.000 | MEDIA |

#### IMO_CASO_00007_01 — Total (verde)

- **Casa Gêmea:** casa em Sao Paulo/SP, proprietário quitado, moradia habitual; área 122 m² (estimado); padrão normal (a confirmar).
- **Elegibilidade:** ELEGIVEL
- **Por que este plano:** tem pet: danos a terceiros causados pelo animal; 1 dependente: danos a terceiros e despesas de hospedagem da família; bens estimados em R$ 19.700 a R$ 39.400; eletrônicos e eletrodomésticos de até R$ 22.000; casa: mais portas e janelas expostas a arrombamento.
- **Por que não o de baixo:** O Prático não cobre aluguel, RC familiar nem despesas emergenciais, que respondem aos sinais citados acima.
- **Por que não o de cima:** É o plano mais completo.
- **Confiança geral:** ALTA · **canal:** ONE_CLICK_BUY

| Cobertura | Mín (R$) | Máx (R$) | Confiança |
|---|---|---|---|
| INCENDIO_RAIO_EXPLOSAO_FUMACA | 271.000 | 485.800 | MEDIA |
| DANOS_POR_AGUA | 31.000 | 56.500 | MEDIA |
| VENDAVAL_GRANIZO | 52.200 | 93.200 | MEDIA |
| IMPACTO_VEICULOS_TERRESTRES | 25.100 | 44.600 | BAIXA |
| QUEDA_AERONAVE | 54.200 | 97.200 | MEDIA |
| DANOS_ELETRICOS | 5.500 | 11.000 | MEDIA |
| ROUBO_FURTO_ARROMBAMENTO | 9.800 | 19.700 | MEDIA |
| QUEBRA_DE_VIDROS | 3.800 | 9.700 | MEDIA |
| RESPONSABILIDADE_CIVIL_FAMILIAR | 35.000 | 90.000 | BAIXA |
| PERDA_PAGAMENTO_ALUGUEL | 4.500 | 25.700 | MEDIA |
| DESPESAS_EMERGENCIAIS | 10.000 | 30.000 | MEDIA |

#### IMO_CASO_00080_01 — Essencial (amarelo)

- **Casa Gêmea:** apartamento em Sao Paulo/SP, proprietário com financiamento, moradia habitual; área 125 m² (estimado); padrão normal (a confirmar).
- **Elegibilidade:** ELEGIVEL
- **Por que este plano:** poucos sinais de necessidade além da proteção básica.
- **Por que não o de baixo:** É o plano de entrada.
- **Por que não o de cima:** O Prático acrescenta roubo e quebra de vidros, mas os sinais de bens de valor são baixos (bens estimados em R$ 11.000 a R$ 22.100).
- **Confiança geral:** BAIXA · **canal:** APP_COM_CONFIRMACAO · **conflitos:** apartamento sem condomínio pago

| Cobertura | Mín (R$) | Máx (R$) | Confiança |
|---|---|---|---|
| INCENDIO_RAIO_EXPLOSAO_FUMACA | 37.900 | 114.400 | MEDIA |
| DANOS_POR_AGUA | 6.000 | 15.900 | MEDIA |
| VENDAVAL_GRANIZO | 1.900 | 5.000 | MEDIA |
| IMPACTO_VEICULOS_TERRESTRES | 800 | 2.800 | MEDIA |
| QUEDA_AERONAVE | 7.600 | 22.900 | MEDIA |
| DANOS_ELETRICOS | 3.200 | 6.500 | ALTA |

#### IMO_CASO_00083_01 — Essencial (vermelho)

- **Casa Gêmea:** apartamento em Brasilia/DF, proprietário com financiamento, moradia habitual; área 61 m² (estimado); padrão normal (a confirmar).
- **Elegibilidade:** ELEGIVEL
- **Por que este plano:** poucos sinais de necessidade além da proteção básica.
- **Por que não o de baixo:** É o plano de entrada.
- **Por que não o de cima:** O Prático acrescenta roubo e quebra de vidros, mas os sinais de bens de valor são baixos (bens estimados em R$ 12.600 a R$ 25.200). Como o cliente tem pet, a RC familiar pode ser incluída como opcional, sem migrar para o Total.
- **Confiança geral:** BAIXA · **canal:** GERENTE · **conflitos:** apartamento sem condomínio pago

| Cobertura | Mín (R$) | Máx (R$) | Confiança |
|---|---|---|---|
| INCENDIO_RAIO_EXPLOSAO_FUMACA | 26.800 | 73.800 | MEDIA |
| DANOS_POR_AGUA | 5.200 | 12.400 | MEDIA |
| VENDAVAL_GRANIZO | 1.700 | 4.000 | MEDIA |
| IMPACTO_VEICULOS_TERRESTRES | 500 | 1.500 | MEDIA |
| QUEDA_AERONAVE | 5.400 | 14.800 | MEDIA |
| DANOS_ELETRICOS | 3.600 | 7.100 | ALTA |

## Limitações

- Os percentuais de perda por evento (danos por água, vendaval, impacto, aeronave, elétricos, roubo) e as faixas de RC familiar são premissas da equipe, sem dado de sinistro por imóvel.
- O CUB vem de agregador secundário (myside.com.br) que cita os Sinduscons; meses de referência diferem entre UFs (ago e set/2026). Goiás usa o DF como proxy.
- Os fatores de padrão vêm da tabela de Minas Gerais (abr/2025) e foram aplicados a todas as UFs.
- O CUB não inclui fundações, elevadores e áreas externas; a reconstrução real pode ser maior.
- A base não informa se o financiamento tem seguro habitacional; por isso a faixa do prédio financiado começa em 50%.
- Os nomes Essencial, Prático e Total não aparecem nas Condições Gerais; a composição de cada plano segue o catálogo do datathon.
