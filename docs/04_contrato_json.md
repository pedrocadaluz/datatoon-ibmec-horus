# Etapa 04 — Contrato JSON do motor
_Gerado por `scripts/04_contrato_json.py` em 28/10/2026. Versão do contrato: 1.0._

Um único contrato atende **app, gerente, SAC e agentes autônomos**. O canal envia o imóvel e as respostas coletadas até agora; o motor atualiza a Casa Gêmea (respostas viram selo `CONFIRMADO`), refaz elegibilidade, plano, faixas e confiança, e devolve as **próximas perguntas** em ordem de impacto. O motor não guarda estado: cada chamada traz todas as respostas já dadas, o que facilita auditoria e reprocessamento.

```
canal ──► { imovel_id, respostas } ──► motor ──► { casa_gemea, recomendacao, coberturas, proximas_perguntas, canal }
  ▲                                                                                  │
  └──────────────────── cliente responde a próxima pergunta ◄───────────────────────┘
```

## Entrada

| Campo | Tipo | Descrição |
|---|---|---|
| `versao_contrato` | texto | `"1.0"` |
| `imovel_id` | texto | Imóvel da base (ex.: `IMO_CASO_00003_01`) |
| `respostas` | objeto | Pergunta → resposta. Vazio na primeira chamada. |

| Pergunta (`id`) | Respostas aceitas |
|---|---|
| `obra` | `NAO` · `REFORMA_PEQUENA` · `OBRA_ESTRUTURAL` (→ inelegível até o fim da obra, CG 7.1) |
| `vinculo` | `INQUILINO` · `PROPRIETARIO_FINANCIADO` · `PROPRIETARIO_QUITADO` · `PROPRIETARIO_LOCADOR` · `IMOVEL_VAZIO` |
| `tipo_imovel` | `APARTAMENTO` · `CASA` · `CASA_EM_CONDOMINIO` |
| `ocupacao` | `OCUPADO` · `DESOCUPADO` (→ sem cobertura de roubo, CG Roubo 2.1 c) |
| `conteudo` | `MENOR` · `NA_FAIXA` · `MAIOR` · `NAO_SEI` · ou valor em reais |
| `area_m2` | `NA_FAIXA` · `MENOR` · `MAIOR` · `NAO_SEI` · ou área em m² |
| `padrao_construtivo` | `ECONOMICO` · `NORMAL` · `SUPERIOR` · `NAO_SEI` |
| `declaracao_unica` | `SIM` · `NAO` (→ elegibilidade pendente, vai ao gerente) |

`NAO_SEI` é sempre aceito: a pergunta sai da lista, a faixa continua larga e a cotação não trava. Resposta inválida devolve `{"erro": ...}` sem alterar nada.

## Saída

| Campo | Descrição |
|---|---|
| `status` | `RECOMENDACAO_INICIAL` (há perguntas) · `RECOMENDACAO_CONFIRMADA` (nada mais a perguntar) · `ENCAMINHAR_GERENTE` · `INELEGIVEL` |
| `elegibilidade` | `status` (ELEGIVEL, ELEGIVEL_CONDICIONADO, INELEGIVEL) e `motivo` |
| `casa_gemea` | Cada campo com `valor`, `selo` (OBSERVADO, ESTIMADO, A_CONFIRMAR, CONFIRMADO), `confianca` e `evidencia`; faixas de área e bens |
| `recomendacao` | Plano, confiança geral, por que este plano, por que não o de baixo e o de cima, campos que ainda podem mudar o plano |
| `coberturas` | Faixa mínima e máxima (LMI), confiança, regra, justificativa, o que confirmar e observação |
| `proximas_perguntas` | Em ordem de impacto: `id`, `pergunta`, `opcoes` (valor + rótulo), `aceita_numero`, `impacto`, `motivo` |
| `canal` | Semáforo e canal sugerido |

Cada canal usa os mesmos campos de outro jeito: o **app** mostra `opcoes` como botões; o **gerente** vê também `motivo` e `impacto` de cada pergunta; o **SAC** lê `pergunta` e `opcoes` em voz alta; um **agente** chama o motor em laço até `status` ≠ `RECOMENDACAO_INICIAL`.

## Jornada de exemplo

Imóvel `IMO_CASO_00003_01`: casa, possível locador (crédito mensal de aluguel) e sinal de reforma. Arquivos completos em `saidas/contrato/`.

| Passo | Respostas enviadas | Plano | Confiança | Faixa de incêndio | Semáforo | Status | Próximas perguntas |
|---|---|---|---|---|---|---|---|
| 0 | (nenhuma) | TOTAL | BAIXA | R$ 431.200 – 761.700 | VERMELHO | ENCAMINHAR_GERENTE | obra, vinculo, area_m2, declaracao_unica |
| 1 | obra=NAO | TOTAL | MEDIA | R$ 431.200 – 761.700 | AMARELO | RECOMENDACAO_INICIAL | vinculo, area_m2, declaracao_unica |
| 2 | obra=NAO, vinculo=PROPRIETARIO_QUITADO | PRATICO | ALTA | R$ 446.800 – 792.900 | VERDE | RECOMENDACAO_INICIAL | area_m2, declaracao_unica |
| 3 | obra=NAO, vinculo=PROPRIETARIO_QUITADO, area_m2=160, declaracao_unica=SIM | PRATICO | ALTA | R$ 505.300 – 633.500 | VERDE | RECOMENDACAO_CONFIRMADA | nenhuma |

## Exemplo de chamada (passo 0)

Entrada:

```json
{
  "versao_contrato": "1.0",
  "imovel_id": "IMO_CASO_00003_01",
  "respostas": {}
}
```

Saída (coberturas resumidas):

```json
{
  "versao_contrato": "1.0",
  "imovel_id": "IMO_CASO_00003_01",
  "cliente_id": "CASO_00003",
  "status": "ENCAMINHAR_GERENTE",
  "elegibilidade": {
    "status": "ELEGIVEL",
    "motivo": ""
  },
  "casa_gemea": {
    "tipo_imovel": {
      "valor": "CASA",
      "selo": "ESTIMADO",
      "confianca": "ALTA",
      "evidencia": "complemento 'QUADRA 8 CASA 15', sem condomínio"
    },
    "vinculo": {
      "valor": "PROPRIETARIO_LOCADOR",
      "selo": "ESTIMADO",
      "confianca": "MEDIA",
      "evidencia": "crédito compatível com aluguel de R$ 8.350 em 11 dos 12 meses e imóvel fora do endereço principal"
    },
    "uso_imovel": {
      "valor": "ALUGADO_A_TERCEIROS",
      "selo": "ESTIMADO",
      "confianca": "MEDIA",
      "evidencia": "imóvel gera crédito compatível com aluguel"
    },
    "area_m2": {
      "valor": 169,
      "selo": "ESTIMADO",
      "confianca": "MEDIA",
      "evidencia": "modelo IPTU + energia + tipo + município (faixa de 80%)"
    },
    "padrao_construtivo": {
      "valor": "NORMAL",
      "selo": "A_CONFIRMAR",
      "confianca": "BAIXA",
      "evidencia": "não cadastrado e área estimada; NORMAL adotado como referência"
    },
    "material_parede": {
      "valor": "NAO_INFORMADO",
      "selo": "A_CONFIRMAR",
      "confianca": "BAIXA",
      "evidencia": "material da parede externa não cadastrado"
    },
    "alerta_obra": {
      "valor": "REFORMA_MODERADA",
      "selo": "A_CONFIRMAR",
      "confianca": "BAIXA",
      "evidencia": "R$ 15.150 em material de construção em 24 meses"
    },
    "conteudo": {
      "valor": 29200,
      "selo": "A_CONFIRMAR",
      "confianca": "BAIXA",
      "evidencia": "imóvel alugado a terceiros: bens podem ser do inquilino"
    },
    "area_faixa_m2": [
      130,
      221
    ],
    "conteudo_faixa": [
      19500.0,
      39000
    ]
  },
  "recomendacao": {
    "plano": "TOTAL",
    "justificativa_curta": "Total: recebe cerca de R$ 8.350/mês de aluguel: renda que pararia após um sinistro; 1 dependente: danos a terceiros e despesas de hospedagem da família.",
    "confianca_geral": "BAIXA",
    "por_que_este_plano": [
      "recebe cerca de R$ 8.350/mês de aluguel: renda que pararia após um sinistro",
      "1 dependente: danos a terceiros e despesas de hospedagem da família",
      "casa: mais portas e janelas expostas a arrombamento"
    ],
    "por_que_nao_plano_abaixo": "O Prático não cobre aluguel, RC familiar nem despesas emergenciais, que respondem aos sinais citados acima. Em reais: o cliente recebe cerca de R$ 8.350/mês de aluguel, então até R$ 25.050 a R$ 50.100 ficariam sem proteção se o imóvel ficasse inabitável.",
    "por_que_nao_plano_acima": "É o plano mais completo.",
    "campos_que_podem_mudar_o_plano": [
      "vinculo"
    ]
  },
  "coberturas": [
    {
      "cobertura": "INCENDIO_RAIO_EXPLOSAO_FUMACA",
      "faixa_valor_min": 431200,
      "faixa_valor_max": 761700,
      "confianca": "MEDIA",
      "regra": "prédio (área × CUB × fator de padrão × interesse no prédio) + conteúdo",
      "justificativa": "Perda total possível: prédio R$ 427.329–R$ 753.926 (169 m² (130–221) × CUB PR R$ 2.739/m² × fator 1,11–1,36; casa própria: estrutura inteira; bens no imóvel são do inquilino (bens de terceiros não cobertos, CG 6.1 r), até 20%) + conteúdo R$ 3.900–R$ 7.800.",
      "a_confirmar": "área construída; padrão de acabamento; valor aproximado dos bens no imóvel",
      "observacao": ""
    },
    {
      "cobertura": "DANOS_POR_AGUA",
      "faixa_valor_min": 43900,
      "faixa_valor_max": 77700,
      "confianca": "MEDIA",
      "regra": "10% do prédio + 30% do conteúdo",
      "justificativa": "Vazamento, chuva pelo telhado ou rompimento de tubulação atingem acabamentos e parte dos bens, raramente tudo. É a 2ª causa de sinistro na carteira residencial da BB Seguros (14,6%).",
      "a_confirmar": "área construída; padrão de acabamento; valor aproximado dos bens no imóvel",
      "observacao": ""
    },
    {
      "...": "uma entrada por cobertura do plano"
    }
  ],
  "proximas_perguntas": [
    {
      "id": "obra",
      "pergunta": "Há obra ou reforma em andamento no imóvel?",
      "opcoes": [
        {
          "valor": "NAO",
          "rotulo": "Não"
        },
        {
          "valor": "REFORMA_PEQUENA",
          "rotulo": "Reforma pequena, como pintura ou piso"
        },
        {
          "valor": "OBRA_ESTRUTURAL",
          "rotulo": "Obra estrutural ou ampliação"
        }
      ],
      "aceita_numero": false,
      "impacto": "elegibilidade",
      "motivo": "define a elegibilidade: imóvel em reforma ou construção fica fora da cobertura (CG 7.1 w/x)"
    },
    {
      "id": "vinculo",
      "pergunta": "Este imóvel está alugado para outra pessoa? Identificamos um crédito mensal de cerca de R$ 8.350.",
      "opcoes": [
        {
          "valor": "PROPRIETARIO_LOCADOR",
          "rotulo": "Sim, está alugado"
        },
        {
          "valor": "PROPRIETARIO_QUITADO",
          "rotulo": "Não, eu moro nele"
        },
        {
          "valor": "IMOVEL_VAZIO",
          "rotulo": "Não, está vazio"
        }
      ],
      "aceita_numero": false,
      "impacto": "pode mudar o plano para Prático",
      "motivo": "muda o plano: quem recebe aluguel precisa da cobertura de perda de aluguel"
    },
    {
      "id": "area_m2",
      "pergunta": "A área construída do imóvel fica entre 130 e 221 m²?",
      "opcoes": [
        {
          "valor": "NA_FAIXA",
          "rotulo": "Sim"
        },
        {
          "valor": "MENOR",
          "rotulo": "Menor"
        },
        {
          "valor": "MAIOR",
          "rotulo": "Maior"
        },
        {
          "valor": "NAO_SEI",
          "rotulo": "Não sei"
        }
      ],
      "aceita_numero": true,
      "impacto": "estreita a faixa de incêndio em 64%",
      "motivo": "área define o custo de reconstrução"
    },
    {
      "id": "declaracao_unica",
      "pergunta": "Confirmo que o imóvel fica em área urbana, fora de comunidade carente e sem ligação com atividade rural, tem paredes de alvenaria e não está em construção, reconstrução nem obra estrutural. Ele também não é tombado, desapropriado nem condenado, e o endereço ainda não tem seguro residencial da BB Seguros.",
      "opcoes": [
        {
          "valor": "SIM",
          "rotulo": "Sim"
        },
        {
          "valor": "NAO",
          "rotulo": "Não — o atendimento segue com o gerente"
        }
      ],
      "aceita_numero": false,
      "impacto": "elegibilidade",
      "motivo": "substitui as perguntas de elegibilidade que os dados não respondem (CG 11, alínea a: declaração inexata faz perder o direito)"
    }
  ],
  "jornada": {
    "campos_formulario_tradicional": 8,
    "perguntas_necessarias": 3,
    "perguntas_evitadas": 5,
    "percentual_evitado": 62
  },
  "canal": {
    "semaforo": "VERMELHO",
    "sugerido": "GERENTE"
  },
  "comparacao_planos": [
    {
      "plano": "ESSENCIAL",
      "nome": "Essencial",
      "situacao": "ABAIXO",
      "coberturas": [
        "INCENDIO_RAIO_EXPLOSAO_FUMACA",
        "DANOS_POR_AGUA",
        "VENDAVAL_GRANIZO",
        "IMPACTO_VEICULOS_TERRESTRES",
        "QUEDA_AERONAVE",
        "DANOS_ELETRICOS"
      ],
      "assistencias": [
        "Casa em Apuros"
      ],
      "resumo": "Deixaria sem proteção roubo e furto com arrombamento, quebra de vidros, responsabilidade civil familiar, perda ou pagamento de aluguel e despesas emergenciais.",
      "motivos": [
        "O Essencial não cobre roubo nem quebra de vidros, que protegem os bens e os acessos citados acima.",
        "O Prático não cobre aluguel, RC familiar nem despesas emergenciais, que respondem aos sinais citados acima. Em reais: o cliente recebe cerca de R$ 8.350/mês de aluguel, então até R$ 25.050 a R$ 50.100 ficariam sem proteção se o imóvel ficasse inabitável."
      ],
      "diferenca": [
        {
          "cobertura": "ROUBO_FURTO_ARROMBAMENTO",
          "nome": "roubo e furto com arrombamento",
          "faixa_valor_min": 2000,
          "faixa_valor_max": 3900,
          "necessidade": "BAIXA",
          "sinais": [
            "casa: mais acessos expostos a arrombamento"
          ],
          "papel": "FICARIA_SEM"
        },
        {
          "cobertura": "QUEBRA_DE_VIDROS",
          "nome": "quebra de vidros",
          "faixa_valor_min": 5200,
          "faixa_valor_max": 13300,
          "necessidade": "BAIXA",
          "sinais": [
            "casa: mais janelas e portas de vidro"
          ],
          "papel": "FICARIA_SEM"
        },
        {
          "cobertura": "RESPONSABILIDADE_CIVIL_FAMILIAR",
          "nome": "responsabilidade civil familiar",
          "faixa_valor_min": 25000,
          "faixa_valor_max": 60000,
          "necessidade": "BAIXA",
          "sinais": [
            "1 dependente em casa"
          ],
          "papel": "FICARIA_SEM"
        },
        {
          "cobertura": "PERDA_PAGAMENTO_ALUGUEL",
          "nome": "perda ou pagamento de aluguel",
          "faixa_valor_min": 25000,
          "faixa_valor_max": 50100,
          "necessidade": "ALTA",
          "sinais": [
            "recebe aluguel: a renda para após um sinistro"
          ],
          "papel": "FICARIA_SEM"
        },
        {
          "cobertura": "DESPESAS_EMERGENCIAIS",
          "nome": "despesas emergenciais",
          "faixa_valor_min": 10000,
          "faixa_valor_max": 30000,
          "necessidade": "BAIXA",
          "sinais": [
            "mais pessoas para abrigar em caso de interdição"
          ],
          "papel": "FICARIA_SEM"
        }
      ]
    },
    {
      "plano": "PRATICO",
      "nome": "Prático",
      "situacao": "ABAIXO",
      "coberturas": [
        "INCENDIO_RAIO_EXPLOSAO_FUMACA",
        "DANOS_POR_AGUA",
        "VENDAVAL_GRANIZO",
        "IMPACTO_VEICULOS_TERRESTRES",
        "QUEDA_AERONAVE",
        "DANOS_ELETRICOS",
        "ROUBO_FURTO_ARROMBAMENTO",
        "QUEBRA_DE_VIDROS"
      ],
      "assistencias": [
        "Casa em Apuros",
        "Casa Funcionando",
        "Casa Arrumada",
        "Casa Limpa"
      ],
      "resumo": "Deixaria sem proteção responsabilidade civil familiar, perda ou pagamento de aluguel e despesas emergenciais.",
      "motivos": [
        "O Prático não cobre aluguel, RC familiar nem despesas emergenciais, que respondem aos sinais citados acima. Em reais: o cliente recebe cerca de R$ 8.350/mês de aluguel, então até R$ 25.050 a R$ 50.100 ficariam sem proteção se o imóvel ficasse inabitável."
      ],
      "diferenca": [
        {
          "cobertura": "RESPONSABILIDADE_CIVIL_FAMILIAR",
          "nome": "responsabilidade civil familiar",
          "faixa_valor_min": 25000,
          "faixa_valor_max": 60000,
          "necessidade": "BAIXA",
          "sinais": [
            "1 dependente em casa"
          ],
          "papel": "FICARIA_SEM"
        },
        {
          "cobertura": "PERDA_PAGAMENTO_ALUGUEL",
          "nome": "perda ou pagamento de aluguel",
          "faixa_valor_min": 25000,
          "faixa_valor_max": 50100,
          "necessidade": "ALTA",
          "sinais": [
            "recebe aluguel: a renda para após um sinistro"
          ],
          "papel": "FICARIA_SEM"
        },
        {
          "cobertura": "DESPESAS_EMERGENCIAIS",
          "nome": "despesas emergenciais",
          "faixa_valor_min": 10000,
          "faixa_valor_max": 30000,
          "necessidade": "BAIXA",
          "sinais": [
            "mais pessoas para abrigar em caso de interdição"
          ],
          "papel": "FICARIA_SEM"
        }
      ]
    },
    {
      "plano": "TOTAL",
      "nome": "Total",
      "situacao": "RECOMENDADO",
      "coberturas": [
        "INCENDIO_RAIO_EXPLOSAO_FUMACA",
        "DANOS_POR_AGUA",
        "VENDAVAL_GRANIZO",
        "IMPACTO_VEICULOS_TERRESTRES",
        "QUEDA_AERONAVE",
        "DANOS_ELETRICOS",
        "ROUBO_FURTO_ARROMBAMENTO",
        "QUEBRA_DE_VIDROS",
        "RESPONSABILIDADE_CIVIL_FAMILIAR",
        "PERDA_PAGAMENTO_ALUGUEL",
        "DESPESAS_EMERGENCIAIS"
      ],
      "assistencias": [
        "Casa em Apuros",
        "Casa Funcionando",
        "Casa Arrumada",
        "Casa Limpa",
        "Casa sem Insetos e Pragas",
        "Casa Segura",
        "Benefício premium"
      ],
      "resumo": "Cobre as necessidades identificadas na sua casa, sem incluir coberturas que os dados não pedem.",
      "motivos": [
        "recebe cerca de R$ 8.350/mês de aluguel: renda que pararia após um sinistro",
        "1 dependente: danos a terceiros e despesas de hospedagem da família",
        "casa: mais portas e janelas expostas a arrombamento"
      ],
      "diferenca": []
    }
  ],
  "personalizacao": {
    "perfil": {
      "arquetipo": "LOCADOR",
      "rotulo": "Locador",
      "descricao": "Vive da renda do aluguel: precisa proteger o imóvel e a renda que ele gera.",
      "sinais": [
        "vínculo: recebe aluguel do imóvel"
      ],
      "jornada": "GUIADA",
      "jornada_motivo": "maturidade digital 66 (35 a 69)",
      "tom": "passo a passo, com exemplos do dia a dia e o motivo de cada pergunta",
      "modo": "NOVA_APOLICE",
      "relacionamento_seguridade": 0
    },
    "necessidades": [
      {
        "cobertura": "PERDA_PAGAMENTO_ALUGUEL",
        "indice": 70,
        "nivel": "ALTA",
        "no_plano_recomendado": true,
        "fatores": [
          {
            "pontos": 65,
            "fator": "recebe aluguel: a renda para após um sinistro"
          }
        ]
      },
      {
        "cobertura": "DANOS_ELETRICOS",
        "indice": 53,
        "nivel": "MEDIA",
        "no_plano_recomendado": true,
        "fatores": [
          {
            "pontos": 8,
            "fator": "consumo de energia alto para o tamanho do imóvel"
          }
        ]
      },
      {
        "cobertura": "DANOS_POR_AGUA",
        "indice": 50,
        "nivel": "MEDIA",
        "no_plano_recomendado": true,
        "fatores": [
          {
            "pontos": 20,
            "fator": "consumo de água de R$ 200/mês (mais pontos hidráulicos em uso)"
          }
        ]
      },
      {
        "cobertura": "VENDAVAL_GRANIZO",
        "indice": 47,
        "nivel": "MEDIA",
        "no_plano_recomendado": true,
        "fatores": [
          {
            "pontos": 25,
            "fator": "casa: telhado e esquadrias expostos"
          }
        ]
      },
      {
        "cobertura": "INCENDIO_RAIO_EXPLOSAO_FUMACA",
        "indice": 30,
        "nivel": "BAIXA",
        "no_plano_recomendado": true,
        "fatores": [
          {
            "pontos": 10,
            "fator": "obra recente aumenta o risco"
          }
        ]
      },
      {
        "cobertura": "IMPACTO_VEICULOS_TERRESTRES",
        "indice": 28,
        "nivel": "BAIXA",
        "no_plano_recomendado": true,
        "fatores": [
          {
            "pontos": 20,
            "fator": "casa: muro, portão e fachada voltados para a rua"
          }
        ]
      },
      {
        "cobertura": "ROUBO_FURTO_ARROMBAMENTO",
        "indice": 27,
        "nivel": "BAIXA",
        "no_plano_recomendado": true,
        "fatores": [
          {
            "pontos": 15,
            "fator": "casa: mais acessos expostos a arrombamento"
          }
        ]
      },
      {
        "cobertura": "RESPONSABILIDADE_CIVIL_FAMILIAR",
        "indice": 25,
        "nivel": "BAIXA",
        "no_plano_recomendado": true,
        "fatores": [
          {
            "pontos": 15,
            "fator": "1 dependente em casa"
          }
        ]
      },
      {
        "cobertura": "QUEBRA_DE_VIDROS",
        "indice": 20,
        "nivel": "BAIXA",
        "no_plano_recomendado": true,
        "fatores": [
          {
            "pontos": 10,
            "fator": "casa: mais janelas e portas de vidro"
          }
        ]
      },
      {
        "cobertura": "DESPESAS_EMERGENCIAIS",
        "indice": 16,
        "nivel": "BAIXA",
        "no_plano_recomendado": true,
        "fatores": [
          {
            "pontos": 8,
            "fator": "mais pessoas para abrigar em caso de interdição"
          }
        ]
      },
      {
        "cobertura": "QUEDA_AERONAVE",
        "indice": 3,
        "nivel": "BAIXA",
        "no_plano_recomendado": true,
        "fatores": []
      }
    ],
    "adicionais_sugeridos": [],
    "assistencias": {
      "base": "Casa em Apuros",
      "destaque": [
        {
          "nome": "Casa Limpa",
          "por_que": "limpeza de calhas e caixa d'água evita infiltração (que a cobertura não paga)"
        },
        {
          "nome": "Casa Segura",
          "por_que": "tela de proteção, película em box e check-up residencial para a família"
        }
      ],
      "so_em_plano_maior": [],
      "beneficio_premium_sugerido": {
        "nome": "Decoração online",
        "por_que": "móveis ou reforma recentes"
      }
    },
    "alertas": [
      {
        "tipo": "BENS_DE_TERCEIROS",
        "texto": "Bens do inquilino não são cobertos (CG V1.6, 6.1 r): o conteúdo considerado é reduzido."
      }
    ],
    "mensagem_do_app": {
      "titulo": "Um seguro feito para a sua casa",
      "texto": "Montamos uma sugestão (Total) com o que o banco já sabe do seu imóvel.",
      "tom": "passo a passo, com exemplos do dia a dia e o motivo de cada pergunta"
    },
    "recibos": [
      {
        "dado": "compras de eletrônicos e eletrodomésticos (36 meses)",
        "usado_para": "equipamentos portáteis, danos elétricos e assistência Casa Funcionando"
      },
      {
        "dado": "bens cadastrados do tipo item de lazer",
        "usado_para": "cobertura de bicicleta"
      },
      {
        "dado": "consumo de água e energia",
        "usado_para": "danos por água e danos elétricos"
      },
      {
        "dado": "vínculo com o imóvel (aluguel, financiamento, crédito)",
        "usado_para": "plano, aluguel e quanto do prédio é seu"
      },
      {
        "dado": "dependentes e pet informados",
        "usado_para": "responsabilidade civil, despesas emergenciais e assistências"
      },
      {
        "dado": "uso do imóvel e ocupação",
        "usado_para": "roubo, desocupação temporária e fechadura eletrônica"
      },
      {
        "dado": "maturidade digital e uso do app",
        "usado_para": "canal, tom e ritmo da conversa (nunca plano nem preço)"
      },
      {
        "dado": "seguro residencial já contratado",
        "usado_para": "modo de revisão em vez de nova apólice"
      }
    ],
    "premissas": [
      "Índice de necessidade: base proporcional à frequência de sinistros da carteira (Monitor Mercantil, 21/07/2026) mais sinais do imóvel; é premissa da equipe, não probabilidade de sinistro.",
      "Faixas dos adicionais são percentuais de bens observados (premissa), sem dado de sinistro por imóvel.",
      "Esta versão não usa idade nem renda do cliente em nenhuma regra de personalização."
    ]
  },
  "explicacao": {
    "passos": [
      {
        "id": "elegibilidade",
        "titulo": "Este imóvel pode ser segurado?",
        "resultado": "ELEGIVEL",
        "motivo": "",
        "checagens": [
          {
            "regra": "Situação cadastral regular",
            "ok": true,
            "base": "Guia 9.1"
          },
          {
            "regra": "Paredes sem predomínio de material combustível",
            "ok": true,
            "base": "Guia 9.1",
            "estado": "A_CONFIRMAR"
          },
          {
            "regra": "Sem obra estrutural em andamento",
            "ok": true,
            "pendente": false,
            "base": "CG V1.6, 7.1 w/x",
            "estado": "A_CONFIRMAR"
          },
          {
            "regra": "Tipo de imóvel identificado",
            "ok": true,
            "base": "Guia 9.1"
          }
        ]
      },
      {
        "id": "casa_gemea",
        "titulo": "O que o banco já sabe da sua casa",
        "texto": "Cada dado vem com selo (observado, estimado, a confirmar), confiança e evidência."
      },
      {
        "id": "plano",
        "titulo": "Qual plano faz sentido?",
        "resultado": "Total",
        "pontos_pratico": 1,
        "pontos_total": 3,
        "sinais_pratico": [
          {
            "pontos": 1,
            "sinal": "casa: mais portas e janelas expostas a arrombamento"
          }
        ],
        "sinais_total": [
          {
            "pontos": 2,
            "sinal": "recebe cerca de R$ 8.350/mês de aluguel: renda que pararia após um sinistro"
          },
          {
            "pontos": 1,
            "sinal": "1 dependente: danos a terceiros e despesas de hospedagem da família"
          }
        ],
        "regra": "Total se pontos do Total >= 3, ou >= 2 com ao menos 1 ponto do Prático; senão Prático se pontos do Prático >= 2; senão Essencial. Nenhum sinal decide sozinho.",
        "por_que_nao_o_de_baixo": "O Prático não cobre aluguel, RC familiar nem despesas emergenciais, que respondem aos sinais citados acima. Em reais: o cliente recebe cerca de R$ 8.350/mês de aluguel, então até R$ 25.050 a R$ 50.100 ficariam sem proteção se o imóvel ficasse inabitável.",
        "por_que_nao_o_de_cima": "É o plano mais completo."
      },
      {
        "id": "faixas",
        "titulo": "Quanto de cobertura",
        "texto": "Cada faixa é o limite máximo de indenização sugerido (não é preço). A largura mostra a incerteza dos dados."
      },
      {
        "id": "perguntas",
        "titulo": "O que ainda pode mudar o resultado",
        "campos_que_mudam_o_plano": [
          "vinculo"
        ],
        "texto": "Só perguntamos o que mudaria o plano, a elegibilidade ou estreitaria a faixa. Se nada mudaria, paramos."
      },
      {
        "id": "canal",
        "titulo": "Como seguir",
        "semaforo": "VERMELHO",
        "canal": "GERENTE"
      }
    ],
    "limites_do_motor": [
      "Percentuais de perda por evento e pesos do plano são premissas da equipe (sem dado de sinistro por imóvel).",
      "Faixa de reconstrução calibrada em cerca de 90% (teste cego da área: erro mediano de 13% no desenvolvimento e 16% no teste).",
      "O motor decide e calcula com regras; IA generativa, quando usada, só redige texto."
    ]
  },
  "respostas_aplicadas": []
}
```
