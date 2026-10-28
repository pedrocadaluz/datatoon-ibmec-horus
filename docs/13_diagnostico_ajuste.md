# Diagnóstico de ajuste: o modelo generaliza ou decora? (28/10/2026)

Reprodução: `python scripts/09_diagnostico_ajuste.py` (semente 42, ~1 min). Métricas em `saidas/diagnostico_ajuste.csv`. Só agregados. Nada em `src/` foi alterado: as propostas estão no fim.

## Veredito

1. **Não há overfitting nem vazamento relevante.** Modelo de área: erro de treino 13,1% e de validação 13,2%; com rótulo embaralhado o erro sobe de 13% para 44% e o R² vai a zero. A validação cruzada das faixas (`validacao.py`) não vaza: 97,15% passa para 97,05% quando as dobras são por cliente e a referência sai da dobra.
2. **Não há underfitting relevante.** Dar mais capacidade (colunas extras, interações, boosting) reduz o erro em no máximo 1,4 ponto percentual (13,2% para 11,9%).
3. **Teste cego: 16,2% de erro mediano (IC 95%: 12,8% a 21,8%, n = 46)** contra 13,3% na validação cruzada. A diferença está dentro do ruído (em 15% das subamostras de 46 imóveis do desenvolvimento o erro é igual ou pior), mas há viés leve: o modelo superestima a área do teste em cerca de 8% (p = 0,03, n = 46).
4. **Pontos fracos reais, pequenos:** a faixa de 80% cobre só 73% a 76% dos imóveis pequenos (e 88% dos grandes), e o padrão construtivo é um indício fraco (acerto balanceado 0,61), já tratado como confiança BAIXA.
5. **Números do README:** erro mediano de área 13,4% (desenvolvimento) fica; acrescentar "16,2% no teste cego (n = 46)". Cobertura da faixa ~89% e a estabilidade do plano não mudam. Os 98% de planos certos com 1 pergunta (script 08, E4) não foram recalculados.

## V1. Teste cego e deriva entre bases

| Medida | Desenvolvimento (validação cruzada por cliente, n = 1.016) | Teste cego (treino só no desenvolvimento, n = 46) |
|---|---|---|
| Erro percentual mediano | 13,3% | 16,2% (IC 95%: 12,8% a 21,8%) |
| R² (log) | 0,862 | 0,797 |
| Cobertura da faixa de 80% | 79,9% | 78,3% (IC 95%: 65% a 89%) |
| Viés (média do resíduo em log) | 0,000 | -0,077 (erro-padrão 0,035, p = 0,03) |
| Padrão pela regra de IPTU/m²: acerto balanceado | 0,608 (n = 273) | 0,628 (n = 12) |
| Aluguel/m² dentro do intervalo p25 a p75 da calibração (esperado ~50%) | 45% (calibração fora da dobra) | 75% (n = 12) |

Deriva das entradas (desenvolvimento contra teste): log IPTU (KS p = 0,41), log energia (p = 0,28), log água (p = 1,00), IPTU por m² (p = 0,28), casa ou apartamento (p = 0,66), tipo (p = 0,79) e vínculo (p = 0,82) são compatíveis. **Município difere (qui-quadrado p = 0,01):** as dez cidades são as mesmas, mas com pesos diferentes; o modelo tem efeito de cidade, então isso pesa pouco. Fração com área real: 39% contra 33%.

Leitura: o desvio do resíduo no teste (0,235) é 11% maior que no desenvolvimento (0,211), compatível com n pequeno. Com 46 imóveis não dá para afirmar overfitting nem descartá-lo; o viés de -8% merece atenção, não alarme.

## V2. Curvas de aprendizado e de complexidade

Erro percentual mediano, média de 3 repetições × 5 dobras por cliente. Treino é o erro nos próprios dados de ajuste.

| Modelo (amostra de treino 100%, n = 813) | Treino | Validação | Diagnóstico |
|---|---|---|---|
| Só a média (constante) | 43,1% | 43,5% | underfitting extremo (referência) |
| OLS só com IPTU | 19,7% | 19,7% | simples demais |
| **OLS atual** (IPTU, energia, casa, município) | **13,1%** | **13,2%** | ajustado |
| OLS proposto (+ água, dependentes, pet, condomínio, financiamento, aluguel, compras, bens) | 12,0% | 12,4% | ajustado |
| OLS com interações e termos quadráticos | 11,5% | 11,9% | ajustado, ganho de 1,3 p.p. |
| Boosting, profundidade 3 | 8,9% | 12,4% | começa a decorar (lacuna de 3,5 p.p.) |
| Boosting, profundidade 6 | 2,8% | 12,7% | decora (lacuna de 9,9 p.p.), sem ganho |

Curva do OLS atual (validação): 10% da amostra (81 imóveis) 15,7%; 25% 14,3%; 50% 13,6%; 75% 13,5%; 100% 13,2%. Treino e validação se encontram e a curva achatou: **mais dados quase não ajudam** e **mais capacidade quase não ajuda**. O piso de erro parece ser ruído do gerador dos dados. Com 10% da amostra o OLS com interações já piora (16,7% contra 15,7%): o modelo mais simples é o mais seguro quando há pouco dado.

## V3. Vazamento na validação cruzada

Leitura do código: `calibracao.calibrar` e `area.treinar` são refeitos dentro de cada dobra em `validacao.validar` (a área do imóvel avaliado é zerada antes), então o IPTU/m² por cidade, o aluguel/m² e os coeficientes **não** usam o imóvel avaliado. Dois pontos mais fracos: as dobras eram sorteadas por imóvel (72 clientes têm 2 imóveis com área real, 144 imóveis) e a referência "real" usava a calibração global. Refeitos:

| Variante | Faixa contém o valor de referência | Erro mediano do centro |
|---|---|---|
| A. Original (dobras por imóvel, referência global) | 97,15% | 8,2% |
| B. Dobras por cliente | 97,05% | 8,5% |
| C. Dobras por cliente + referência com calibração da dobra | 97,05% | 8,5% |

Área: erro mediano 13,4% com dobras por imóvel (`area.treinar`) e 13,3% por cliente. **Vazamento desprezível.** O "97%" continua otimista pelo motivo já documentado em `docs/12_avaliacao_modelo.md` (E3: a referência é o centro da própria faixa); citar ~89% a 90%.

## V4. Rótulo embaralhado

| Teste | Real | Embaralhado |
|---|---|---|
| Área, erro mediano (30 sorteios) | 13,3% | 43,6% (dentro do município: 43,5%) |
| Área, R² (log) | 0,862 | -0,017 (máx. p95: -0,006) |
| Padrão, acerto balanceado (regra com mediana fora da dobra) | 0,608 | 0,332 (p95: 0,386; p < 0,001 em 2.000 sorteios) |

Sem sinal no embaralhado: não há vazamento no pipeline. Para o padrão, a regra não aprende rótulo, mas os limiares 1,25 e 0,85 foram escolhidos olhando a base. Reestimá-los (grade, metade para escolher, outra metade para avaliar, 40 divisões): escolhe em média 1,19 (dp 0,10) e 0,88 (dp 0,04), parecidos com os atuais; acerto 0,639 na metade de escolha e **0,592 na outra** (0,607 com os limiares atuais). Com rótulo embaralhado, a escolha de limiares infla o acerto em 5,9 pontos (0,392 contra 0,336): é esse o tamanho do otimismo possível ao "escolher olhando". Conclusão: os limiares atuais não estão sobreajustados.

## V5. Resíduos e viés (modelo de área, previsões fora da amostra)

| Subgrupo | Viés (log) | Erro mediano | Cobertura da faixa de 80% |
|---|---|---|---|
| Casa / Apartamento / Casa em condomínio | +0,001 / +0,001 / -0,005 | 13,3% / 13,5% / 12,9% | 80,0% / 78,8% / 84,6% |
| Cidades (10) | -0,002 a +0,009 (todas < 0,35 erro-padrão) | 9,8% (Goiânia) a 17,6% (Porto Alegre) | 69,6% (Fortaleza, n = 56) a 84,6% |
| Área prevista, quartil menor → maior | -0,005 / -0,010 / +0,017 / -0,001 | 14,4% / 16,4% / 13,7% / 9,9% | 75,6% / 74,8% / 81,5% / 87,8% |
| IPTU, quartil menor → maior | -0,017 / +0,001 / +0,027 / -0,010 | 14,7% / 15,8% / 12,8% / 10,7% | 72,6% / 77,4% / 81,6% / 88,5% |

- **Nenhum subgrupo é sistematicamente subestimado.** O único desvio acima de 2 erros-padrão (IPTU Q3, +2,7%) é pequeno e esperado entre 24 grupos testados. (Agrupar pela área real criaria um viés artificial, regressão à média; por isso o quartil usa a área prevista.)
- **Heterocedasticidade existe** (Breusch-Pagan p = 0,0001; correlação de Spearman entre previsão e |resíduo| = -0,13): em log, imóveis pequenos erram mais. A faixa única de -23%/+31% cobre pouco os pequenos e demais os grandes. É o ponto mais concreto de melhoria.
- Cauda: p95 do erro 42%, p99 71%, máximo 92%. Os 10 piores têm erro médio de 80%, todos **superestimados**, nenhum com área acima do p90; 40% são apartamentos sem condomínio pago (grupo já sinalizado como ambíguo) e estão em 7 cidades.

## V6. Limiares escolhidos olhando os dados

Percentil que cada limiar ocupa (entre quem gastou, para obra; em todos os imóveis, para conteúdo e eletrônicos):

| Limiar | Percentil no desenvolvimento | Entre metades aleatórias (p5 a p95) | No teste | Fração acima: dev / teste (p) |
|---|---|---|---|---|
| Obra R$ 10 mil | 0,53 | 0,49 a 0,56 | 0,52 | 47% / 48% (0,90) |
| Obra R$ 30 mil | 0,86 | 0,83 a 0,88 | 0,90 | 14% / 10% (0,55) |
| Conteúdo moderado R$ 10 mil | 0,10 | 0,09 a 0,10 | 0,12 | 90% / 88% (0,28) |
| Conteúdo relevante R$ 20 mil | 0,39 | 0,38 a 0,41 | 0,38 | 61% / 62% (0,85) |
| Eletrônicos R$ 15 mil | 0,36 | 0,34 a 0,37 | 0,38 | 64% / 62% (0,67) |

Reestimar os cinco limiares (mesmo percentil) em uma metade e aplicar na outra (60 divisões): **o plano muda em 0,23% dos imóveis (p95: 0,55%)** e a bandeira "obra a confirmar" em 0,25% (p95: 0,94%). Reestimados no próprio teste: nenhum plano muda (0 de 138). Para comparação, mexer ±20% nos limiares de conteúdo muda 3,7% a 3,8% dos planos: a escolha dos valores importa mais que a amostra usada para estimá-los. Os pesos da pontuação (pet, dependentes, Total ≥ 3) são premissas sem rótulo: não há como medir over ou underfitting delas; ver E5 de `docs/12_avaliacao_modelo.md`.

## V7. Estabilidade do plano entre bases (qui-quadrado)

| Variável | Desenvolvimento | Teste | p |
|---|---|---|---|
| Plano: Total / Prático / Essencial | 46,5% / 43,3% / 10,2% | 50,0% / 39,9% / 10,1% | 0,70 |
| Confiança: alta / média / baixa | 69,0% / 21,6% / 9,4% | 74,6% / 16,7% / 8,7% | 0,34 |
| Semáforo: verde / amarelo / vermelho | 67,7% / 17,5% / 14,8% | 72,5% / 10,9% / 16,7% | 0,13 |
| Perguntas: 0 / 1 / 2 / 3+ | 32,6% / 54,5% / 12,0% / 1,0% | 31,9% / 57,3% / 8,7% / 2,2% | 0,36 |
| Média de perguntas | 0,81 | 0,81 | 0,89 (Mann-Whitney) |

Distribuições compatíveis (menor p = 0,13; o teste tem 138 imóveis, então diferenças de até ~7 pontos não são detectáveis).

## Veredito por componente

| Componente | Situação | O que fazer |
|---|---|---|
| Modelo de área | **Ajustado** (sem lacuna treino/validação; mais capacidade rende ≤ 1,4 p.p.). Atenção ao viés de -8% no teste (n = 46) | Manter. Opcional: modelo "proposto" (docs/12). Citar 13% (dev) e 16% (teste cego, n = 46) |
| Faixa de 80% da área | **Leve underfitting de forma** (cobertura 73% a 76% nos pequenos, 88% nos grandes) | Faixa por terço de área prevista (trecho abaixo). Não urgente |
| Calibração IPTU/m² e aluguel/m² | **Ajustada** (aluguel p25 a p75: 45% fora da dobra contra 50% nominal) | Manter |
| Padrão construtivo | **Sem overfitting**, indício fraco (0,61 balanceado contra 0,33 do acaso) | Manter com confiança BAIXA |
| Limiares de obra, conteúdo, eletrônicos | **Estáveis** (plano muda 0,2%) | Manter |
| Pontuação do plano e regra de parada | **Sem rótulo**: só estabilidade medida (±20% muda ~3,7%; distribuições iguais entre bases) | Declarar como premissa |
| Validação das faixas | **Sem vazamento** (97,15% para 97,05%); otimista por outro motivo | Citar ~89% a 90% |

Trecho proposto para a faixa por tamanho (em `area.treinar`, após calcular `residuos` e `previsto`):

```python
terco = pd.qcut(previsto, 3, labels=False)
faixas = {k: np.quantile(residuos[terco == k], QUANTIS_FAIXA) for k in range(3)}
# em prever(): escolher (residuo_min, residuo_max) pelo terço da área prevista
```

## Limitações

- Teste cego com 46 imóveis (12 com padrão cadastrado): o intervalo é largo e a deriva de município (p = 0,01) pode explicar parte do viés.
- Dados sintéticos: a área é quase função do IPTU e da energia, então o piso de erro e a ausência de overfitting podem não valer em dados reais.
- Não existe rótulo de sinistro: pontuação do plano e regra de parada só têm teste de estabilidade, não de acerto.
- Múltiplos testes (24 subgrupos, 7 deriva): um p entre 0,01 e 0,05 isolado não é conclusivo.
