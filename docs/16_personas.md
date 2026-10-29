# Etapa 16: três personas desenhadas pelas características

As personas de [`docs/11_personas.md`](11_personas.md) (Marina, Rafael e Helena) foram escolhidas entre casos reais do Teste Comum, já com o resultado do motor. Estas três foram feitas ao contrário: primeiro o perfil, **só pelos critérios que o motor usa**, o mais distantes possível entre si; o resultado vem depois, ao rodar o motor. Nenhuma é definida por idade ou renda (a mesma regra do motor). Nomes e perfis são fictícios.

## Os perfis

| Critério do motor | **Luiza** | **Luigi** | **Júlia** |
|---|---|---|---|
| Tipo de imóvel | Apartamento pequeno | Casa grande | Casa em condomínio |
| Relação com o imóvel | Inquilina | Dono, já quitado | Dona, aluga para outra pessoa |
| Uso do imóvel | Mora nele | Mora nele | Alugado a terceiros (ela não mora) |
| Padrão e paredes | Simples, alvenaria | Alto padrão, alvenaria | Não informado |
| Obra ou reforma | Nenhuma | Reforma em andamento | Não sabe |
| Bens no imóvel | Poucos, quase nada próprio | Muitos, com eletrônicos caros | Mobília é do inquilino |
| Pet e dependentes | Nenhum | Dependentes e um cachorro | Nenhum no imóvel |
| Sinais extras | Nenhum | Gasto recente com vidraçaria | Nenhum |
| Quanto o banco sabe | Muito | Muito | Pouco (dados faltando) |
| Canal preferido | Só o app | Gerente da agência | Telefone (SAC) |

- **Luiza** mora de aluguel e resolve tudo pelo celular. Quer algo rápido, sem ler contrato.
- **Luigi** tem a casa cheia: família, pet e reforma no meio do caminho. Quer conversar com alguém de confiança antes de decidir.
- **Júlia** tem o imóvel como investimento. Não mora lá, não sabe detalhes da construção e liga para tirar dúvida.

## O que cada uma exercita no produto

| Persona | Features |
|---|---|
| Luiza | Jornada rápida no app, poucas perguntas, interesse segurável de inquilino (só o conteúdo) |
| Luigi | Adicionais por sinais (eletrônicos, vidros, RC familiar por pet e dependentes), alerta de obra, canal Gerente |
| Júlia | Muitas estimativas e respostas "Não sei", bens de terceiros, imóvel que não é moradia, canal SAC |

## Como testar no app

As três não existem na base. Cada uma foi ligada ao imóvel do Teste Comum **mais parecido pelas características**, escolhido sem rodar o motor nem olhar o plano. No seletor do app, elas aparecem no grupo **Personas**, junto com Marina, Rafael e Helena.

| Persona | Imóvel | O que bate | O que não bate |
|---|---|---|---|
| Luiza | `IMO_CASO_00036_02` (Goiânia/GO) | Apartamento de 50 m², inquilina, mora nele, poucos bens, sem pet, sem obra, usa muito o app | Tem 2 dependentes |
| Luigi | `IMO_CASO_00098_01` (São Paulo/SP) | Casa de 217 m², dono quitado, alto padrão, muitos eletrônicos, pet, 3 dependentes | Sem sinal de reforma nem de vidraçaria; usa o app |
| Júlia | `IMO_CASO_00015_02` (Porto Alegre/RS) | Casa em condomínio, dona que aluga para terceiros, sem pet | Dados de construção completos; usa o app |

Para chegar ao perfil exato, use a aba **Agente** e mude as respostas no JSON (por exemplo `"obra": "REFORMA_PEQUENA"` para o Luigi ou `"padrao_construtivo": "NAO_SEI"` para a Júlia).
