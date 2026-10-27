# Etapa 01 — Casa Gêmea
_Gerado por `scripts/01_construir_casa_gemea.py` em 27/10/2026._

A Casa Gêmea é a cópia virtual de cada imóvel, montada só com os sinais disponíveis. Cada informação recebe um **selo** (`OBSERVADO`, `ESTIMADO` ou `A_CONFIRMAR`), uma **confiança** (`ALTA`, `MEDIA`, `BAIXA`) e a **evidência** usada.

| Base | Imóveis | Clientes |
|---|---|---|
| desenvolvimento | 2578 | 2200 |
| teste | 138 | 120 |

## Como cada campo foi inferido

| Campo | Sinais usados | Regra |
|---|---|---|
| Tipo de imóvel | complemento, termos apartamento/casa/condomínio, condomínio pago | Apartamento ou casa pelo complemento; casa + condomínio = casa em condomínio. Apartamento sem condomínio pago tem confiança média. |
| Vínculo | aluguel pago, parcela de financiamento, crédito compatível com aluguel | Inquilino > financiado > locador > quitado (ausência de sinais). Sinais simultâneos = a confirmar. |
| Uso | endereço principal, nº de imóveis do cliente, vínculo | Principal = moradia habitual; 2º imóvel não principal = temporada/segunda residência; locador = alugado a terceiros. |
| Área | área cadastrada; senão IPTU, energia, tipo, município | Modelo log-linear (detalhes abaixo) com faixa de 80%. |
| Padrão construtivo | cadastro | Ausente → `NORMAL` como referência, a confirmar. |
| Parede externa | cadastro | Ausente → a confirmar (requisito de elegibilidade). |
| Sinal de obra | gasto com material de construção em 24 meses | 0 / < 10 mil (leve) / < 30 mil (moderada) / ≥ 30 mil (possível obra relevante). |
| Conteúdo | bens vinculados e compras de 36 meses | Mín = bens ponderados pela probabilidade; máx = maior entre bens cadastrados e compras. |

**Não usados em nenhuma inferência:** idade, renda, origem e confiança da renda.

## Modelo de área

`log(área) = b0 + b1·log(IPTU) + b2·log(energia) + b3·[casa] + efeito do município`

Treinado nos imóveis com área real da base de desenvolvimento e avaliado com validação cruzada de 5 dobras.

| Métrica | Valor |
|---|---|
| Imóveis com área real (treino) | 1016 |
| Erro médio absoluto | 22,7 m² |
| Erro percentual mediano | 13,4% |
| R² (escala log) | 0,86 |
| Faixa de 80% contém a área real | 79,9% dos casos |
| Largura da faixa em relação à estimativa | -23% / +31% |

Variáveis testadas e descartadas: condomínio (correlação 0,02 com a área), renda (0,01) e padrão construtivo (área mediana igual entre padrões).

<details><summary>Coeficientes</summary>

| variável | coeficiente |
|---|---|
| intercepto | -1,7 |
| log(IPTU anual) | 0,6 |
| log(energia mensal) | 0,4 |
| é casa | 0,1 |
| município: Brasilia | -0,1 |
| município: Curitiba | -0,1 |
| município: Fortaleza | 0,1 |
| município: Goiania | 0,1 |
| município: Porto Alegre | -0,1 |
| município: Recife | 0,1 |
| município: Rio de Janeiro | -0,2 |
| município: Salvador | 0,1 |
| município: Sao Paulo | -0,2 |

</details>

## Resultado por campo

### Tipo de imóvel

| valor | desenvolvimento (n) | desenvolvimento (%) | teste (n) | teste (%) |
|---|---|---|---|---|
| CASA | 1198 | 46,5 | 60 | 43,5 |
| APARTAMENTO | 1118 | 43,4 | 63 | 45,7 |
| CASA_EM_CONDOMINIO | 262 | 10,2 | 15 | 10,9 |

### Vínculo com o imóvel

| valor | desenvolvimento (n) | desenvolvimento (%) | teste (n) | teste (%) |
|---|---|---|---|---|
| PROPRIETARIO_QUITADO | 1025 | 39,8 | 47 | 34,1 |
| PROPRIETARIO_FINANCIADO | 781 | 30,3 | 39 | 28,3 |
| INQUILINO | 531 | 20,6 | 31 | 22,5 |
| PROPRIETARIO_LOCADOR | 241 | 9,3 | 21 | 15,2 |

### Uso do imóvel

| valor | desenvolvimento (n) | desenvolvimento (%) | teste (n) | teste (%) |
|---|---|---|---|---|
| MORADIA_HABITUAL | 2193 | 85,1 | 113 | 81,9 |
| ALUGADO_A_TERCEIROS | 241 | 9,3 | 21 | 15,2 |
| TEMPORADA_OU_SEGUNDA_RESIDENCIA | 144 | 5,6 | 4 | 2,9 |

### Origem da área

| valor | desenvolvimento (n) | desenvolvimento (%) | teste (n) | teste (%) |
|---|---|---|---|---|
| ESTIMADO | 1562 | 60,6 | 92 | 66,7 |
| OBSERVADO | 1016 | 39,4 | 46 | 33,3 |

### Padrão construtivo

| valor | desenvolvimento (n) | desenvolvimento (%) | teste (n) | teste (%) |
|---|---|---|---|---|
| A_CONFIRMAR | 1878 | 72,8 | 98 | 71,0 |
| OBSERVADO | 700 | 27,2 | 40 | 29,0 |

### Material da parede externa

| valor | desenvolvimento (n) | desenvolvimento (%) | teste (n) | teste (%) |
|---|---|---|---|---|
| NAO_INFORMADO | 2019 | 78,3 | 109 | 79,0 |
| ALVENARIA | 559 | 21,7 | 29 | 21,0 |

### Sinal de obra

| valor | desenvolvimento (n) | desenvolvimento (%) | teste (n) | teste (%) |
|---|---|---|---|---|
| SEM_SINAL | 2117 | 82,1 | 109 | 79,0 |
| REFORMA_LEVE | 244 | 9,5 | 15 | 10,9 |
| REFORMA_MODERADA | 151 | 5,9 | 11 | 8,0 |
| POSSIVEL_OBRA_RELEVANTE | 66 | 2,6 | 3 | 2,2 |

### Confiança no valor do conteúdo

| valor | desenvolvimento (n) | desenvolvimento (%) | teste (n) | teste (%) |
|---|---|---|---|---|
| MEDIA | 2139 | 83,0 | 109 | 79,0 |
| BAIXA | 439 | 17,0 | 29 | 21,0 |

## Campos a confirmar por imóvel

| valor | desenvolvimento (n) | desenvolvimento (%) | teste (n) | teste (%) |
|---|---|---|---|---|
| 0 | 103 | 4,0 | 5 | 3,6 |
| 1 | 657 | 25,5 | 34 | 24,6 |
| 2 | 1214 | 47,1 | 63 | 45,7 |
| 3 | 456 | 17,7 | 26 | 18,8 |
| 4 | 94 | 3,6 | 3 | 2,2 |
| 5 | 49 | 1,9 | 6 | 4,3 |
| 6 | 5 | 0,2 | 1 | 0,7 |

## Valores de referência (base de desenvolvimento)

| Medida | Mediana | P90 |
|---|---|---|
| Área (m²) | 126 | 265 |
| Conteúdo mínimo (R$) | 7.600 | 33.200 |
| Conteúdo máximo (R$) | 34.000 | 75.230 |
| Eletrônicos + eletrodomésticos, máx (R$) | 20.400 | 45.000 |

## Limitações

- Tipo, vínculo e uso são **sugestões** a partir de sinais indiretos; não substituem a declaração do cliente.
- "Proprietário quitado" é inferido pela **ausência** de sinais e pode incluir imóvel cedido ou de familiar.
- Não é possível distinguir sobrado de casa térrea, nem identificar imóvel rural, tombado ou uso MEI com os dados recebidos.
- A estimativa de área só vale para os 10 municípios da base; outra cidade exige recalibrar o modelo.
- O conteúdo pode estar subestimado (bens não comprados via banco) ou superestimado (compras que não ficaram no imóvel).
