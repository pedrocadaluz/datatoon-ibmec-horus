# Avaliação do modelo da Casa Gêmea (28/10/2026)

Reprodução: `python scripts/08_avaliar_modelo.py` (semente 42, ~30 s). Métricas em `saidas/avaliacao_modelo.csv`. Base de desenvolvimento, validação cruzada de 5 dobras **agrupada por cliente**. Só agregados.

## Resumo executivo e recomendação

1. **O modelo atual é suficiente para entregar.** Nenhum experimento revelou falha que mude o resultado do pitch ou dos CSVs.
2. **Área:** usar mais colunas reduz o erro mediano de 13,3% para 12,5% (R² 0,862 para 0,885) e a faixa de 80% fica 9% mais estreita. Ganho real (IC 95% da diferença: -2,1 a -0,1 ponto percentual), mas pequeno. Vem de dependentes/pet, água, financiamento/aluguel e compras/bens. **Idade, renda, app, coordenadas, internet e UF não acrescentam nada.** Vale mudar só se sobrar tempo (10 linhas em `area.py`).
3. **Padrão construtivo:** nenhuma combinação de colunas supera a regra atual de IPTU/m². Manter como indício de confiança BAIXA.
4. **Faixas:** a faixa de reconstrução atual já é **calibrada em ~90%** (cobertura empírica 89%), não apenas larga. Dá para oferecer um nível de 80% com faixa 17% mais estreita. O "97%" de `validacao.py` é otimista (ver E3).
5. **Perguntas:** a ordem do motor atual acerta o plano com menos perguntas (98% com 1 pergunta). A ordem por valor esperado da informação estreita mais a faixa, mas não vale trocar. **Aviso para o pitch:** o plano depende muito de pet, dependentes e do limiar do Total (E5); são premissas, não parâmetros estimados.

## E1. Modelo de área (1.016 imóveis com área real)

| Modelo | Erro % mediano | MAE (m²) | R² (log) | Cobertura do intervalo de 80% | Largura do intervalo (log) |
|---|---|---|---|---|---|
| **Atual** (OLS: IPTU, energia, casa, município) | 13,3% | 22,9 | 0,862 | 79,6% | 0,539 |
| Gradient boosting, mesmas colunas | 13,6% | 22,1 | 0,867 | 79,7% | 0,518 |
| Regressão quantílica (boosting, 10%/50%/90%) | 13,6% | 22,2 | 0,867 | 76,4% | 0,516 |
| **Proposto** (OLS: atual + água, dependentes, pet, condomínio, financiamento, aluguel, compras, bens) | **12,5%** | 20,7 | 0,885 | 79,8% | 0,489 |
| Todas as colunas, OLS | 12,1% | 20,6 | 0,891 | 79,6% | 0,475 |
| Todas as colunas, Ridge | 12,0% | 20,5 | 0,891 | 79,3% | 0,475 |
| Todas as colunas, gradient boosting | 11,8% | 20,3 | 0,891 | 79,9% | 0,475 |

Ablação (OLS). Colunas somadas ao modelo atual, uma por vez: variação do erro % mediano (R² entre parênteses). Colunas tiradas do modelo completo: variação em relação a 12,1%.

| Grupo de colunas | Somado ao atual | Tirado do completo |
|---|---|---|
| Dependentes e pet | -0,06 p.p. (R² 0,872) | **+0,77 p.p.** (R² 0,878) |
| Água | -0,01 p.p. | **+0,42 p.p.** |
| Financiamento e aluguel | +0,19 p.p. | **+0,32 p.p.** |
| Compras e bens | -0,30 p.p. (R² 0,869) | +0,04 p.p. (R² 0,880) |
| Condomínio | -0,05 p.p. | +0,14 p.p. |
| Renda | +0,02 p.p. | -0,19 p.p. (R² cai 0,006) |
| Idade, internet, coordenadas, UF, app/maturidade digital | de -0,08 a +0,21 p.p. | de -0,04 a +0,08 p.p. |

- Diferença completo (OLS) menos atual, bootstrap por imóvel (1.000 reamostras): -1,1 p.p. (IC 95%: -2,1 a -0,1).
- Correlação com log(área): IPTU 0,86, energia 0,80, água 0,50, condomínio -0,19, renda 0,01.
- **O que é gerador sintético:** a área é quase função do IPTU e da energia (R² 0,86 com 3 variáveis). O ganho de dependentes/pet e água parece reproduzir regras do gerador (domicílio maior, consumo maior) e não um padrão de mundo real. Renda sozinha não explica área (0,01) e só ajuda em conjunto com compras, sinal típico de relação construída pelo gerador. Em dados reais não espere o mesmo ganho.
- Boosting não ajuda com poucas colunas: os dados são quase log-lineares.

## E2. Padrão construtivo (700 imóveis com padrão cadastrado; 273 também com área real)

| Método | Acurácia (todos) | Acur. balanceada (todos) | Acurácia (com área) | Acur. balanceada (com área) | F1 macro (com área) |
|---|---|---|---|---|---|
| Sempre NORMAL (61% da base) | 61,0% | 0,333 | 63,4% | 0,333 | 0,259 |
| **Regra atual** (IPTU/m² contra a cidade) | 59,1% | 0,425 | 58,6% | **0,599** | 0,562 |
| Logística: IPTU/m² e energia relativos à cidade | 38,3% | 0,490 | 49,5% | 0,570 | 0,491 |
| Logística: todas as colunas | 46,3% | 0,541 | 52,0% | 0,599 | 0,518 |
| Boosting: todas as colunas | 62,1% | 0,415 | 65,6% | 0,472 | 0,481 |

Leitura: "sempre NORMAL" tem a maior acurácia bruta, mas nunca acerta os extremos (que são o que importa para o custo). A regra atual tem a mesma acurácia balanceada da logística com todas as colunas (0,599). Nenhuma combinação supera a regra atual. Em "todos", a regra usa NORMAL nos imóveis sem área real (como no motor).

## E3. Calibração das faixas de reconstrução (273 imóveis com área e padrão reais, ambos escondidos)

Verdade: área real × CUB da UF × fator do padrão real. Faixa: a combinação de incertezas de `regras.faixa_combinada`. Conformal split: o escore |log(verdade/centro)| / meia-largura é calibrado nas dobras de treino e a faixa é multiplicada por k.

| Faixa | Cobertura nominal | Cobertura empírica | Razão máx/mín mediana | Estreitamento (largura log) |
|---|---|---|---|---|
| Atual (k = 1) | sem nível declarado | 89,0% | 1,77 | 0% |
| Conformal 50% | 50% | 50,5% | 1,29 | -55% |
| Conformal 80% | 80% | 79,9% | 1,60 | -17% |
| Conformal 90% | 90% | 90,5% | 1,80 | +3% |

- A curva nominal contra empírica fica sobre a diagonal (50,5%, 79,9%, 90,5%). A faixa atual equivale a um nível de ~89%: **calibrada**, não só larga. Estreitar para 80% custa 10 pontos de cobertura; não recomendo trocar o padrão, e sim declarar "faixa de cerca de 90%" no pitch.
- Só a área, conformal separado por casa e apartamento: cobertura 48,4%, 78,8% e 88,3% para 50%, 80% e 90% (largura log 0,25, 0,52 e 0,66). Levemente abaixo do nominal; a amostra é pequena.
- **Por que 97% em `validacao.py`:** lá o "valor real" é o centro da faixa calculada com os dados cadastrados (inclusive o padrão estimado pelo IPTU, não verdadeiro) e as faixas incluem conteúdo. Contra a verdade de reconstrução, a cobertura medida aqui é 89%. Os 97% não devem ser citados como cobertura de erro real.

## E4. Estratégia de perguntas (600 imóveis, área e padrão escondidos)

Campos simulados: área, padrão, conteúdo, vínculo (locador ambíguo) e tipo (confiança abaixo de ALTA); 3,3 campos incertos por imóvel em média. Obra e ocupação não entram. Verdade: área e padrão reais da base; padrão ausente sorteado pela frequência da base; conteúdo sorteado entre mín e máx; vínculo e tipo certos com probabilidade 50% e 70% (**premissas declaradas**, a base não tem rótulo). "Plano certo" = igual ao plano com todos os campos confirmados. "Contém" = a faixa de incêndio contém o centro da faixa com tudo confirmado.

| Perguntas (k) | Motor atual: plano certo | Motor atual: razão máx/mín | Aleatória: plano certo | Aleatória: razão | Valor esperado: plano certo | Valor esperado: razão |
|---|---|---|---|---|---|---|
| 0 | 92,0% | 2,44 | 92,0% | 2,44 | 92,0% | 2,44 |
| 1 | **98,2%** | 2,01 | 93,8% | 2,22 | 96,2% | 1,96 |
| 2 | 99,5% | 1,96 | 96,0% | 2,00 | 97,7% | 1,81 |
| 3 | 99,5% | 1,96 | 98,0% | 1,81 | 97,8% | 1,76 |
| 4 | 99,5% | 1,96 | 99,7% | 1,78 | 99,8% | 1,76 |
| 5 | 99,5% | 1,96 | 100% | 1,78 | 99,8% | 1,76 |

- O motor atual faz **0,85 pergunta em média** (para sozinho pela regra de parada) e já acerta 98% dos planos com uma. Planos mudam pouco: 92% já estão certos sem perguntar.
- A ordem por valor esperado (chance de mudar o plano + redução esperada da largura) obtém a faixa mais estreita com 2 a 3 perguntas, mas faz 3,3 perguntas e acerta menos o plano nas primeiras. A aleatória precisa de 3 a 4 perguntas para igualar.
- Cobertura do centro verdadeiro: 88,3% (k=0), 86,0% (motor, k=1), 95,0% (valor esperado, k=3), 99% (k=4). O motor atual para antes de estreitar tudo e deixa a faixa mais larga (1,96), por escolha de projeto.
- Conclusão: para o objetivo "acertar o plano com poucas perguntas" o motor atual já é o melhor. Para "faixa mais estreita" o valor esperado ganha ~10%, ao custo de mais perguntas.

## E5. Robustez das regras de plano (cada peso ou limiar ±1)

Imóveis que mudam de plano (desenvolvimento 2.578 / teste 138). Distribuição atual (dev / teste): Essencial 10% / 10%, Prático 43% / 40%, Total 46% / 50%.

| Parâmetro | -1 (dev / teste) | +1 (dev / teste) |
|---|---|---|
| Limiar combinado do Total (Total ≥2 com Prático ≥1) | **35,1% / 39,9%** | 23,7% / 18,1% |
| Dependentes (1 ponto) | 17,4% / 13,8% | **27,7% / 29,7%** |
| Pet (1 ponto) | 17,0% / 12,3% | 8,3% / 10,1% |
| Conteúdo médio (1 ponto) | 9,7% / 3,6% | 6,3% / 8,0% |
| Limiar do Prático (2 pontos) | 7,5% / 8,7% | 7,6% / 4,4% |
| Casa (1 ponto) | 5,7% / 2,9% | 1,1% / 0,7% |
| Inquilino (2 pontos) | 4,9% / 6,5% | 0,2% / 0% |
| Limiar combinado do Prático | 0,9% / 0% | 4,3% / 0,7% |
| Locador, eletro, vidros, conteúdo alto, limiar do Total | até 2,5% | até 1,5% |

- Todos os pesos com ruído aleatório de -1, 0 ou +1 (60 sorteios): mediana de 32% (dev) e 31% (teste) dos imóveis mudam de plano; percentil 95 em 46% e 45%.
- O plano é **robusto** ao conteúdo, vidros, eletrônicos e vínculo. Fica **sensível** a pet, dependentes e à regra "um ponto de Total junto com um de Prático vira Total". Isso é lógico: são as proteções (RC familiar) que separam o Prático do Total, e não há rótulo para calibrá-las. Declarar como premissa de negócio no README e no pitch.

## Decisão: o que mudar até amanhã 10h

| Mudança | Ganho esperado | Esforço | Recomendação |
|---|---|---|---|
| Manter modelo de área atual | nenhum | 0 | **Padrão.** Basta para a entrega |
| Modelo de área "proposto" (+água, dependentes, pet, financiamento, aluguel, condomínio, compras, bens) | erro -0,8 p.p.; faixa -9% | ~1 h + regerar CSVs e retestar | Só se sobrar tempo; sem risco de privacidade (não usa idade nem renda) |
| Usar idade, renda, app, coordenadas | nenhum | baixo | **Não vale:** não melhora e agrava a narrativa de privacidade |
| ML para o padrão construtivo | nenhum | médio | **Não vale** |
| Faixa conformal 80% | faixa -17% | baixo | **Não vale** como padrão; citar que a atual é ~90% calibrada |
| Ordem por valor esperado nas perguntas | faixa -10% com +2 perguntas | médio | **Não vale** trocar |
| Citar 97% de cobertura | n/a | 0 | **Corrigir:** citar 89% a 90% (E3) |
| Texto de premissas do plano | transparência | 15 min | **Fazer:** declarar pesos de pet/dependentes como premissa e mostrar sensibilidade (E5) |

Trecho para o modelo proposto (não aplicado em `src/`), em `area._matriz`:

```python
colunas += [np.log1p(df["agua_media_mensal_6m"]), df["quantidade_dependentes"],
            (df["possui_pet_informado"] == "SIM").astype(float),
            np.log1p(df["pagamento_condominio_mensal"]), (df["pagamento_condominio_mensal"] > 0).astype(float),
            np.log1p(df["parcela_financiamento_imobiliario"]), np.log1p(df["valor_aluguel_recorrente"]),
            np.log1p(df["compras_moveis_36m"] + df["compras_eletrodomesticos_36m"] + df["compras_eletronicos_36m"]),
            np.log1p(df["bens_valor_cadastrado"])]
```

## Limitações

- Base sintética: ganhos de colunas refletem o gerador. Não há rótulo de sinistro, então nada aqui mede risco, só área, custo de reconstrução e coerência do plano.
- E3 usa só os 273 imóveis com área e padrão reais; a verdade do custo é CUB × área × fator (não é o custo de obra real). Os fatores de padrão têm incerteza própria.
- E4: vínculo, tipo, conteúdo e parte dos padrões têm verdade sorteada por premissas; as diferenças entre ordens de 1 a 2 pontos estão dentro do ruído (600 imóveis, uma semente).
- E5 mede mudança de plano, não erro de plano: sem rótulo, não dá para dizer qual configuração é a correta.
- O experimento E1 usa colunas de renda e idade apenas para teste; a regra do projeto (guardrail) as mantém fora de risco, plano e valor.
