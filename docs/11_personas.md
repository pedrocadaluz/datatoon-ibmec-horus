# Etapa 11: três personas e o comportamento do motor

_Gerado por `scripts/10_personas.py`. Dados fictícios (base de teste comum); os nomes das personas são inventados para a demonstração. Cada jornada está em `saidas/personas/`._

O mesmo motor, com os mesmos dados do banco, produz recomendações, adicionais, canal e tom diferentes para cada perfil. Nenhuma regra usa idade ou renda; a personalização vem do imóvel, do vínculo, das compras, de dependentes e pet e do uso do app.

## Comparativo

| | **Marina** | **Rafael** | **Helena** |
|---|---|---|---|
| Imóvel | `IMO_CASO_00008_01` | `IMO_CASO_00016_01` | `IMO_CASO_00059_01` |
| Quem é | Inquilina de apartamento em Fortaleza, com 3 dependentes e pet, e usa muito o app do banco. | Dono de casa financiada no Rio de Janeiro, com muitos eletrônicos, que acabou de gastar muito em material de construção. | Tem um apartamento de temporada em Fortaleza, que passa meses vazio, e quase não usa o app. |
| Arquétipo | Inquilino com família | Casa conectada | Casa de temporada |
| Jornada e tom | EXPRESS: direto e rápido: poucas palavras, um toque por decisão | EXPRESS: direto e rápido: poucas palavras, um toque por decisão | HUMANA: acolhedor e simples, com apoio de um especialista a um toque de distância |
| Modo | nova apólice | nova apólice | nova apólice |
| Plano (início) | Total | Pratico | Pratico |
| Plano (fim) | Total | Pratico | Essencial |
| Canal (início) | verde, one_click_buy | vermelho, gerente | amarelo, atendimento_assistido |
| Canal (fim) | verde, one_click_buy | verde, one_click_buy | verde, atendimento_assistido |
| Faixa de incêndio (fim) | R$ 19.400 a R$ 52.900 | R$ 350.700 a R$ 845.300 | R$ 53.200 a R$ 111.000 |
| Adicionais sugeridos | EQUIPAMENTOS_PORTATEIS, INDENIZACAO_VALOR_DE_NOVO | INDENIZACAO_VALOR_DE_NOVO, EQUIPAMENTOS_PORTATEIS, BICICLETA | DESOCUPACAO_TEMPORARIA, EQUIPAMENTOS_PORTATEIS, INDENIZACAO_VALOR_DE_NOVO |
| Perguntas feitas | 1 mais a declaração única | 1 mais a declaração única e resposta a adicional | 1 mais a declaração única e resposta a adicional |
| Perguntas evitadas (de 8) | 7 | 7 | 7 |
| Assistências em destaque | Casa Funcionando, Casa sem Insetos e Pragas | Casa Funcionando, Casa Limpa | base do plano |
| Benefício premium sugerido | Assistente virtual | não se aplica (plano sem benefício premium) | não se aplica (plano sem benefício premium) |
| Notificação do app | **Um seguro feito para a sua casa**: Você comprou cerca de R$ 6.225 em eletrônicos. | **Um seguro feito para a sua casa**: Você renovou cerca de R$ 65.100 em eletrônicos, eletrodomésticos e móveis nos últimos 36 meses. | **Um seguro feito para a sua casa**: O imóvel fica sem moradores por períodos. |
| Alertas | nenhum | nenhum | desocupacao |

## Marina: Inquilino com família

Inquilina de apartamento em Fortaleza, com 3 dependentes e pet, e usa muito o app do banco.

| Passo | Resposta | Plano | Elegibilidade | Canal | Faixa de incêndio | Adicionais |
|---|---|---|---|---|---|---|
| 0 | (nenhuma) | Total | elegivel | verde | R$ 19.400 a R$ 52.900 | EQUIPAMENTOS_PORTATEIS, INDENIZACAO_VALOR_DE_NOVO |
| 1 | conteudo = NA_FAIXA | Total | elegivel | verde | R$ 19.400 a R$ 52.900 | EQUIPAMENTOS_PORTATEIS, INDENIZACAO_VALOR_DE_NOVO |
| 2 | declaracao_unica = SIM | Total | elegivel | verde | R$ 19.400 a R$ 52.900 | EQUIPAMENTOS_PORTATEIS, INDENIZACAO_VALOR_DE_NOVO |

**Por que este plano** (rastro do motor):

- 1 ponto(s): bens estimados em R$ 9.300 a R$ 18.600
- 2 ponto(s): paga aluguel de R$ 1.500: se o imóvel ficar inabitável, continua devendo o aluguel
- 1 ponto(s): tem pet: danos a terceiros causados pelo animal
- 1 ponto(s): 3 dependentes: danos a terceiros e despesas de hospedagem da família

**Adicionais e por quê:**

- **Equipamentos portáteis** (necessidade 52): Você comprou cerca de R$ 6.225 em eletrônicos. Danos elétricos não cobrem queda nem dano mecânico de notebook, tablet ou câmera; esta cobertura sim, dentro de casa. Faixa sugerida: R$ 1.600 a R$ 3.700. (CG V1.6, item 4.1 g)
- **Indenização a valor de novo** (necessidade 47): Você renovou cerca de R$ 18.550 em eletrônicos, eletrodomésticos e móveis nos últimos 36 meses. Sem esta opção, a indenização desconta a depreciação (tabela da CG). (CG V1.6, itens 24.2 e 25.1)

## Rafael: Casa conectada

Dono de casa financiada no Rio de Janeiro, com muitos eletrônicos, que acabou de gastar muito em material de construção.

| Passo | Resposta | Plano | Elegibilidade | Canal | Faixa de incêndio | Adicionais |
|---|---|---|---|---|---|---|
| 0 | (nenhuma) | Pratico | elegivel_condicionado | vermelho | R$ 350.700 a R$ 845.300 | INDENIZACAO_VALOR_DE_NOVO, EQUIPAMENTOS_PORTATEIS, BICICLETA |
| 1 | obra = REFORMA_PEQUENA | Pratico | elegivel | verde | R$ 350.700 a R$ 845.300 | INDENIZACAO_VALOR_DE_NOVO, EQUIPAMENTOS_PORTATEIS, BICICLETA |
| 2 | declaracao_unica = SIM | Pratico | elegivel | verde | R$ 350.700 a R$ 845.300 | INDENIZACAO_VALOR_DE_NOVO, EQUIPAMENTOS_PORTATEIS, BICICLETA |
| 3 | equipamentos = SIM | Pratico | elegivel | verde | R$ 350.700 a R$ 845.300 | INDENIZACAO_VALOR_DE_NOVO, EQUIPAMENTOS_PORTATEIS, BICICLETA |

**Por que este plano** (rastro do motor):

- 2 ponto(s): bens estimados em R$ 32.600 a R$ 65.100
- 1 ponto(s): eletrônicos e eletrodomésticos de até R$ 33.000
- 1 ponto(s): casa: mais portas e janelas expostas a arrombamento

**Adicionais e por quê:**

- **Indenização a valor de novo** (necessidade 70): Você renovou cerca de R$ 65.100 em eletrônicos, eletrodomésticos e móveis nos últimos 36 meses. Sem esta opção, a indenização desconta a depreciação (tabela da CG). (CG V1.6, itens 24.2 e 25.1)
- **Equipamentos portáteis** (necessidade 63): Você comprou cerca de R$ 11.800 em eletrônicos. Danos elétricos não cobrem queda nem dano mecânico de notebook, tablet ou câmera; esta cobertura sim, dentro de casa. Faixa sugerida: R$ 3.000 a R$ 7.100. (CG V1.6, item 4.1 g)
- **Bicicleta** (necessidade 55): Você tem cerca de R$ 20.650 em itens de lazer. Se parte for bicicleta, esta cobertura protege contra roubo e furto com arrombamento, inclusive fora de casa em alguns casos. Faixa sugerida: R$ 6.200 a R$ 12.400. (CG V1.6, item 4.1 b)

## Helena: Casa de temporada

Tem um apartamento de temporada em Fortaleza, que passa meses vazio, e quase não usa o app.

| Passo | Resposta | Plano | Elegibilidade | Canal | Faixa de incêndio | Adicionais |
|---|---|---|---|---|---|---|
| 0 | (nenhuma) | Pratico | elegivel | amarelo | R$ 53.200 a R$ 111.000 | DESOCUPACAO_TEMPORARIA, EQUIPAMENTOS_PORTATEIS, INDENIZACAO_VALOR_DE_NOVO |
| 1 | ocupacao = DESOCUPADO | Essencial | elegivel | verde | R$ 53.200 a R$ 111.000 | DESOCUPACAO_TEMPORARIA, EQUIPAMENTOS_PORTATEIS, INDENIZACAO_VALOR_DE_NOVO |
| 2 | declaracao_unica = SIM | Essencial | elegivel | verde | R$ 53.200 a R$ 111.000 | DESOCUPACAO_TEMPORARIA, EQUIPAMENTOS_PORTATEIS, INDENIZACAO_VALOR_DE_NOVO |
| 3 | desocupacao = SIM | Essencial | elegivel | verde | R$ 53.200 a R$ 111.000 | DESOCUPACAO_TEMPORARIA, EQUIPAMENTOS_PORTATEIS, INDENIZACAO_VALOR_DE_NOVO |

**Por que este plano** (rastro do motor):

- 1 ponto(s): tem pet: danos a terceiros causados pelo animal

**Adicionais e por quê:**

- **Desocupação temporária** (necessidade 75): O imóvel fica sem moradores por períodos. Sem esta extensão, roubo e aluguel não são cobertos com o imóvel vazio, e acima de 30 dias seguidos nenhum evento é coberto (a menos que seja veraneio declarado). (CG V1.6, item 4.1 f e exclusão 7.1 y)
- **Equipamentos portáteis** (necessidade 63): Você comprou cerca de R$ 11.550 em eletrônicos. Danos elétricos não cobrem queda nem dano mecânico de notebook, tablet ou câmera; esta cobertura sim, dentro de casa. Faixa sugerida: R$ 2.900 a R$ 6.900. (CG V1.6, item 4.1 g)
- **Indenização a valor de novo** (necessidade 59): Você renovou cerca de R$ 37.050 em eletrônicos, eletrodomésticos e móveis nos últimos 36 meses. Sem esta opção, a indenização desconta a depreciação (tabela da CG). (CG V1.6, itens 24.2 e 25.1)

**Alertas:**

- Imóvel vazio por mais de 30 dias seguidos perde as coberturas, salvo veraneio declarado (CG V1.6, 7.1 y).

## Como ler

- **Jornada EXPRESS, GUIADA ou HUMANA:** vem da maturidade digital do cliente e muda ritmo, texto e canal, nunca o plano nem o valor.
- **Adicionais:** só aparecem com sinal nos dados e viram pergunta quando falta confirmação. O índice de necessidade é premissa da equipe, não probabilidade de sinistro.
- **Recibos:** cada personalização mostra os dados usados (campo `personalizacao.recibos`), e o cliente pode desligá-la.
