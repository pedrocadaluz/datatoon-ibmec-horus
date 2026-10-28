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
    "confianca_geral": "BAIXA",
    "por_que_este_plano": [
      "recebe cerca de R$ 8.350/mês de aluguel: renda que pararia após um sinistro",
      "1 dependente: danos a terceiros e despesas de hospedagem da família",
      "casa: mais portas e janelas expostas a arrombamento"
    ],
    "por_que_nao_plano_abaixo": "O Prático não cobre aluguel, RC familiar nem despesas emergenciais, que respondem aos sinais citados acima.",
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
      "motivo": "define a elegibilidade: imóvel em reforma ou construção fica fora da cobertura (CG 7.1 x/y)"
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
      "pergunta": "Confirmo que o imóvel fica em área urbana, tem paredes de alvenaria, não está em obra estrutural e não é tombado.",
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
      "motivo": "substitui as perguntas de elegibilidade que os dados não respondem (CG 11.1.2: declaração inexata faz perder o direito)"
    }
  ],
  "canal": {
    "semaforo": "VERMELHO",
    "sugerido": "GERENTE"
  },
  "respostas_aplicadas": []
}
```
