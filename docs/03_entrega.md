# Etapa 03 — Entrega dos templates
_Gerado por `scripts/03_gerar_entrega.py` em 28/10/2026._

Arquivos em `entrega/`, com o mesmo nome, colunas e ordem de linhas dos templates oficiais da base Teste Comum.

| Arquivo | Linhas |
|---|---|
| `template_resultado_times.csv` | 138 imóveis |
| `template_coberturas_times.csv` | 1393 coberturas |

## Testes de formato e coerência

| teste | ok | detalhe |
|---|---|---|
| Mesmas colunas e ordem do template de resultado | ✅ |  |
| Todos os imóveis do template, na mesma ordem | ✅ | 138 imóveis |
| cliente_id igual ao do template | ✅ |  |
| Campos obrigatórios preenchidos | ✅ |  |
| Motivo preenchido quando não é elegível sem ressalvas | ✅ |  |
| Coberturas fixas de cada imóvel = coberturas do plano no catálogo | ✅ | 1393 linhas de cobertura |
| Nomes de cobertura iguais ao catálogo (fixas) ou às Condições Gerais (adicionais) | ✅ | 110 linhas de adicionais em 90 imóveis |
| Coberturas listadas no resultado = coberturas detalhadas | ✅ |  |
| Sem cobertura duplicada por imóvel | ✅ |  |
| Faixas são números inteiros positivos | ✅ |  |
| Mínimo ≤ máximo em todas as faixas | ✅ |  |
| Toda cobertura tem confiança, dados, regra e justificativa | ✅ |  |
| Nenhum texto com quebra de linha | ✅ |  |
| Nenhum texto cita idade ou renda do cliente | ✅ |  |

## Convenções dos campos

Os campos dos templates são de formato livre e documentado (dicionário de dados).

| Campo | Valores |
|---|---|
| `elegivel` | `SIM` · `PENDENTE_VALIDACAO` (plano provisório; vai ao gerente) · `NAO` |
| `motivo_inelegibilidade` | Vazio quando `SIM`; senão, o motivo e a cláusula |
| `tipo_imovel_sugerido` | `APARTAMENTO` · `CASA` · `CASA_EM_CONDOMINIO` · `INDEFINIDO` |
| `uso_imovel_sugerido` | `MORADIA_HABITUAL` · `TEMPORADA_OU_SEGUNDA_RESIDENCIA` · `ALUGADO_A_TERCEIROS` |
| `tipo_vinculo_sugerido` | `INQUILINO` · `PROPRIETARIO_FINANCIADO` · `PROPRIETARIO_QUITADO` (sem financiamento ativo) · `PROPRIETARIO_LOCADOR` |
| `plano_recomendado` | `ESSENCIAL` · `PRATICO` · `TOTAL` (nomes do catálogo) |
| `coberturas_recomendadas` | Coberturas fixas do plano e, depois delas, os adicionais opcionais com faixa (CG 4.1), separados por ` \| ` |
| `confianca_geral` | `ALTA` (nenhuma resposta plausível muda o plano) · `MEDIA` (um campo pode mudar) · `BAIXA` (dois ou mais, ou elegibilidade pendente) |
| `justificativa_recomendacao` | Recomendação inicial → Casa Gêmea com selos → por que este plano → por que não o de baixo → por que não o de cima → adicionais opcionais sugeridos → assistências do plano → o que pode mudar o plano |
| `perguntas_confirmacao` | Perguntas fechadas em ordem de impacto, com opções e o porquê, separadas por ` \| `; a última é sempre a declaração única de elegibilidade |
| `fontes_publicas_adicionais` | Condições Gerais BB, CUB da UF do imóvel, fatores Sinduscon-MG e dado de sinistros, com link |
| `faixa_valor_min` / `faixa_valor_max` | Reais inteiros, sem "R$" e sem separador de milhar |
| `confianca_estimativa` | `ALTA` · `MEDIA` · `BAIXA` (confiança dos dados que a faixa usa) |

A recomendação é **inicial**: usa só os dados que o banco já tem. As perguntas confirmam ou ajustam o plano e estreitam as faixas.

## Resumo

### Elegibilidade

| valor | imóveis | % |
|---|---|---|
| SIM | 135 | 97,8 |
| PENDENTE_VALIDACAO | 3 | 2,2 |

### Plano

| valor | imóveis | % |
|---|---|---|
| TOTAL | 69 | 50,0 |
| PRATICO | 55 | 39,9 |
| ESSENCIAL | 14 | 10,1 |

### Confiança geral

| valor | imóveis | % |
|---|---|---|
| ALTA | 103 | 74,6 |
| MEDIA | 23 | 16,7 |
| BAIXA | 12 | 8,7 |

### Perguntas por imóvel (sem contar a declaração única)

| valor | imóveis | % |
|---|---|---|
| 1 | 79 | 57,2 |
| 0 | 44 | 31,9 |
| 2 | 12 | 8,7 |
| 3 | 3 | 2,2 |

### Confiança das faixas

| valor | coberturas | % |
|---|---|---|
| MEDIA | 740 | 53,1 |
| ALTA | 355 | 25,5 |
| BAIXA | 298 | 21,4 |

## Exemplos (um por nível de confiança)

### IMO_CASO_00001_01 — PRATICO · confiança ALTA · elegível: SIM

**Justificativa:** Recomendação inicial com os dados do banco: plano Prático, confiança alta. Casa Gêmea: casa em condomínio (estimado), proprietário sem financiamento [estimado: sem aluguel pago, sem financiamento e sem aluguel recebido (ausência de sinais)], moradia habitual; área 263 m² (estimada pelo IPTU e pela energia: 202–345 m²); padrão normal (a confirmar). Por que o Prático: bens estimados em R$ 22.700 a R$ 45.400; eletrônicos e eletrodomésticos de até R$ 27.200; casa: mais portas e janelas expostas a arrombamento. Por que não o Essencial: O Essencial não cobre roubo nem quebra de vidros, que protegem os bens e os acessos citados acima. Por que não o Total: O Total acrescenta aluguel, RC familiar e despesas emergenciais, mas o cliente não paga nem recebe aluguel: a cobertura de aluguel só pagaria uma moradia temporária se o imóvel ficasse inabitável, sem perda de renda. São proteções úteis, mas não prioritárias para este perfil. Como o cliente tem pet, o Total vale a pena se ele quiser proteção contra danos a terceiros. Adicionais opcionais sugeridos, pagos à parte: Indenização a valor de novo (CG V1.6, itens 24.2 e 25.1): Você renovou cerca de R$ 45.400 em eletrônicos, eletrodomésticos e móveis nos últimos 36 meses. Sem esta opção, a indenização desconta a depreciação (tabela da CG). Sem linha de faixa: não tem limite próprio ou depende de declaração do cliente. Equipamentos portáteis (CG V1.6, item 4.1 g): Você comprou cerca de R$ 7.575 em eletrônicos. Danos elétricos não cobrem queda nem dano mecânico de notebook, tablet ou câmera; esta cobertura sim, dentro de casa. Assistências do plano (não entram no detalhamento de coberturas): Casa em Apuros, Casa Funcionando, Casa Arrumada, Casa Limpa; em destaque para este cliente: Casa Funcionando, conserta eletrodoméstico, ar-condicionado e TV; você tem até R$ 27.200 em aparelhos; Casa Limpa, limpeza de calhas e caixa d'água evita infiltração (que a cobertura não paga). Nenhuma resposta plausível muda o plano; as perguntas só ajustam as faixas.

**Perguntas de confirmação:**

-   1) A área construída do imóvel fica entre 202 e 345 m²? (Sim / Menor / Maior / Não sei) [por quê: área define o custo de reconstrução]
-   2) Confirmo que o imóvel fica em área urbana, tem paredes de alvenaria, não está em obra estrutural e não é tombado. (Sim / Não — o atendimento segue com o gerente)

| Cobertura | Mín (R$) | Máx (R$) | Confiança |
|---|---|---|---|
| INCENDIO_RAIO_EXPLOSAO_FUMACA | 498.100 | 923.800 | MEDIA |
| DANOS_POR_AGUA | 54.300 | 101.500 | MEDIA |
| VENDAVAL_GRANIZO | 97.300 | 180.200 | MEDIA |
| IMPACTO_VEICULOS_TERRESTRES | 47.500 | 87.800 | MEDIA |
| QUEDA_AERONAVE | 99.600 | 184.800 | MEDIA |
| DANOS_ELETRICOS | 6.800 | 13.600 | MEDIA |
| ROUBO_FURTO_ARROMBAMENTO | 11.400 | 22.700 | MEDIA |
| QUEBRA_DE_VIDROS | 8.100 | 20.700 | MEDIA |
| EQUIPAMENTOS_PORTATEIS | 1.900 | 4.500 | BAIXA |

### IMO_CASO_00013_01 — PRATICO · confiança MEDIA · elegível: SIM

**Justificativa:** Recomendação inicial com os dados do banco: plano Prático, confiança média. Casa Gêmea: apartamento (estimado), proprietário com financiamento [estimado: parcela de financiamento de R$ 1.800/mês], moradia habitual; área 95 m² (cadastro); padrão superior (estimado). Por que o Prático: bens estimados em R$ 14.000 a R$ 28.000; eletrônicos e eletrodomésticos de até R$ 17.600. Por que não o Essencial: O Essencial não cobre roubo nem quebra de vidros, que protegem os bens e os acessos citados acima. Por que não o Total: O Total acrescenta aluguel, RC familiar e despesas emergenciais, mas o cliente não paga nem recebe aluguel: a cobertura de aluguel só pagaria uma moradia temporária se o imóvel ficasse inabitável, sem perda de renda. São proteções úteis, mas não prioritárias para este perfil. Como o cliente tem 1 dependente, o Total vale a pena se ele quiser proteção contra danos a terceiros. Adicionais opcionais sugeridos, pagos à parte: Indenização a valor de novo (CG V1.6, itens 24.2 e 25.1): Você renovou cerca de R$ 27.950 em eletrônicos, eletrodomésticos e móveis nos últimos 36 meses. Sem esta opção, a indenização desconta a depreciação (tabela da CG). Sem linha de faixa: não tem limite próprio ou depende de declaração do cliente. Equipamentos portáteis (CG V1.6, item 4.1 g): Você comprou cerca de R$ 4.725 em eletrônicos. Danos elétricos não cobrem queda nem dano mecânico de notebook, tablet ou câmera; esta cobertura sim, dentro de casa. Assistências do plano (não entram no detalhamento de coberturas): Casa em Apuros, Casa Funcionando, Casa Arrumada, Casa Limpa; em destaque para este cliente: Casa Funcionando, conserta eletrodoméstico, ar-condicionado e TV; você tem até R$ 17.600 em aparelhos; Casa Arrumada, montagem e instalação dos móveis e itens que você tem comprado. O plano pode mudar conforme a confirmação do valor dos bens.

**Perguntas de confirmação:**

-   1) Somando móveis, eletrônicos e eletrodomésticos, quanto valem os bens neste imóvel? Estimamos entre R$ 14.000 e R$ 28.000. (Menos que isso / Nessa faixa / Mais que isso / Não sei) [por quê: valor dos bens define a necessidade de cobertura de roubo e a faixa de incêndio]
-   2) Confirmo que o imóvel fica em área urbana, tem paredes de alvenaria, não está em obra estrutural e não é tombado. (Sim / Não — o atendimento segue com o gerente)

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
| EQUIPAMENTOS_PORTATEIS | 1.200 | 2.800 | BAIXA |

### IMO_CASO_00003_01 — TOTAL · confiança BAIXA · elegível: SIM

**Justificativa:** Recomendação inicial com os dados do banco: plano Total, confiança baixa. Casa Gêmea: casa (estimado), proprietário que aluga a terceiros [estimado: crédito compatível com aluguel de R$ 8.350 em 11 dos 12 meses e imóvel fora do endereço principal], alugado a terceiros; área 169 m² (estimada pelo IPTU e pela energia: 130–221 m²); padrão normal (a confirmar). Por que o Total: recebe cerca de R$ 8.350/mês de aluguel: renda que pararia após um sinistro; 1 dependente: danos a terceiros e despesas de hospedagem da família; casa: mais portas e janelas expostas a arrombamento. Por que não o Prático: O Prático não cobre aluguel, RC familiar nem despesas emergenciais, que respondem aos sinais citados acima. Em reais: o cliente recebe cerca de R$ 8.350/mês de aluguel, então até R$ 25.050 a R$ 50.100 ficariam sem proteção se o imóvel ficasse inabitável. Assistências do plano (não entram no detalhamento de coberturas): Casa em Apuros, Casa Funcionando, Casa Arrumada, Casa Limpa, Casa sem Insetos e Pragas, Casa Segura; em destaque para este cliente: Casa Limpa, limpeza de calhas e caixa d'água evita infiltração (que a cobertura não paga); Casa Segura, tela de proteção, película em box e check-up residencial para a família. O plano pode mudar conforme a confirmação do vínculo com o imóvel.

**Perguntas de confirmação:**

-   1) Há obra ou reforma em andamento no imóvel? (Não / Reforma pequena, como pintura ou piso / Obra estrutural ou ampliação) [por quê: define a elegibilidade: imóvel em reforma ou construção fica fora da cobertura (CG 7.1 w/x)]
-   2) Este imóvel está alugado para outra pessoa? Identificamos um crédito mensal de cerca de R$ 8.350. (Sim, está alugado / Não, eu moro nele / Não, está vazio) [por quê: muda o plano: quem recebe aluguel precisa da cobertura de perda de aluguel]
-   3) A área construída do imóvel fica entre 130 e 221 m²? (Sim / Menor / Maior / Não sei) [por quê: área define o custo de reconstrução]
-   4) Confirmo que o imóvel fica em área urbana, tem paredes de alvenaria, não está em obra estrutural e não é tombado. (Sim / Não — o atendimento segue com o gerente)

| Cobertura | Mín (R$) | Máx (R$) | Confiança |
|---|---|---|---|
| INCENDIO_RAIO_EXPLOSAO_FUMACA | 431.200 | 761.700 | MEDIA |
| DANOS_POR_AGUA | 43.900 | 77.700 | MEDIA |
| VENDAVAL_GRANIZO | 85.900 | 151.600 | MEDIA |
| IMPACTO_VEICULOS_TERRESTRES | 42.700 | 75.400 | MEDIA |
| QUEDA_AERONAVE | 86.200 | 152.300 | MEDIA |
| DANOS_ELETRICOS | 1.000 | 2.100 | BAIXA |
| ROUBO_FURTO_ARROMBAMENTO | 2.000 | 3.900 | BAIXA |
| QUEBRA_DE_VIDROS | 5.200 | 13.300 | MEDIA |
| RESPONSABILIDADE_CIVIL_FAMILIAR | 25.000 | 60.000 | BAIXA |
| PERDA_PAGAMENTO_ALUGUEL | 25.000 | 50.100 | MEDIA |
| DESPESAS_EMERGENCIAIS | 10.000 | 30.000 | MEDIA |

