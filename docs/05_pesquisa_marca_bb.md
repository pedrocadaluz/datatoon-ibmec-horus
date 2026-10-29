# Pesquisa de marca e jornada: Seguro Residencial BB Seguros

Pesquisa feita em 28/10/2026 no navegador, com valores lidos do CSS computado das páginas. Nada foi preenchido nem enviado: a cotação para no primeiro passo, que pede nome, CPF, celular, e-mail e data de nascimento.

Fontes:
- Produto: https://www.bbseguros.com.br/seguros/seguro-residencial
- Plano Prático: https://www.bbseguros.com.br/seguros/para-voce/residencial/residencial-pratico
- Cotação: https://cotacaoseguroresidencial.bbseguros.com.br/home

## 1. Cores

| Hex | Uso | Onde aparece |
|---|---|---|
| `#5A6FFF` | Primária: títulos, cabeçalho, botão "Área do cliente", título dos cards de plano | h1 "Seguro Residencial", h2 das seções, card "Seguro Residencial Prático" (36px) |
| `#4D64FF` | Botão "Saiba mais" dos cards | Barra inferior de cada card de plano |
| `#465EFF` | Links de ação ("Contratar seguro") | Menu e atalhos |
| `#FFFFFF` | Fundo da página e texto sobre a cor primária | `body`, texto dos botões azuis |
| `#F9F7FF` | Fundo secundário dos cards de plano | Cards Essencial, Prático e Total |
| `#DDE4FC` | Borda dos cards | Borda de 0,8px dos cards de plano |
| `#212529` | Texto corpo | `body`. Corrige a referência anterior (`#2E2E2E`) |
| `#4C4C4C` | Descrição curta dos planos | "17 assistências + 8 coberturas" |
| `#FCFC30` | Amarelo do hero e do slogan | Fundo da hero (medido 8 vezes); o amarelo também aparece como `#FCEE4F`, `#FFFA72` e `#FFE352` em outras faixas |
| `#FF6F68` (aprox.) | Botão de chamada da hero | "FAÇA SUA COTAÇÃO" (na tela aparece em salmão; na cotação, `#FA796D`) |
| `#7B8BFF` | Botão desabilitado (provável) | "AVANÇAR" na primeira tela da cotação, com campos vazios |
| `#003087` | Azul escuro | Medido em 2 elementos; não identifiquei onde, então não usar como regra |

Observação: a cor da cotação (`cotacaoseguroresidencial`) é a mesma azul primária, mas o fundo é branco com a foto à esquerda, sem a faixa amarela.

## 2. Tipografia e formas

- **Famílias**: títulos e botões em `BancoDoBrasilTitulos` (700); corpo e títulos de seção em `BancoDoBrasilTextos`; textos dos cards de plano em `Inter` (14,99px). Fallback: `-apple-system, Segoe UI, Roboto, Arial`.
- **Tamanhos**: h1 32px/700; h2 de seção 36px/700 (e 28px em blocos menores); h3 24px/700; título de card de plano 36px/700; corpo 16px/400; texto de card 15px; rótulo de card 10px/500 (caixa alta).
- **Botões**: "Contratar seguro" 15px/700 (texto azul, sem caixa); botões de ação com cantos de 4px; "Área do cliente" com cantos de 8px.
- **Cantos**: 4px nos cards e botões; sem sombras.
- **Bordas**: 0,8px sólida `#DDE4FC` nos cards.
- **Largura do conteúdo**: bloco de texto central de aproximadamente 648px; campos de formulário de 366px.
- **Campos da cotação**: altura de 38px (a caixa interna) e rótulo flutuante em 16px.

## 3. Componentes

- **Cabeçalho**: barra azul `#5A6FFF` com ícone de menu à esquerda, logo "BB Seguros" (amarelo sobre azul) e botão "Área do cliente" à direita. Abaixo, migalhas: Página inicial > Seguros > Residencial.
- **Hero**: fundo amarelo, título azul "Seguro Residencial", parágrafo curto, botão "Faça sua cotação" e foto de família à direita. Dois ícones de acessibilidade fixos na borda direita.
- **Barra de atalhos**: três links em linha: "Contratar um seguro", "Acionar e acompanhar", "Solicitar assistência".
- **Cards de plano**: três cards lado a lado (Essencial, Prático, Total). Cada um tem o nome, a linha "N assistências + N coberturas", o texto "mensais a partir de", o preço em reais (Essencial R$ 19,90; Prático R$ 27,74; Total R$ 62,23), uma nota "Valor poderá variar de acordo com o perfil e região" e dois botões: "Simule online" e "Saiba mais".
- **Lista de coberturas**: itens com título e texto curto, sem ícones visíveis. No plano Prático: danos elétricos, vendaval, quebra de vidros, roubo e/ou furto, pequenos reparos, incêndio e raio, danos por água, impacto de veículos ou queda de aeronave. Cada item tem o botão "Visualizar".
- **Benefícios premium** (só no Total): três cards com h3 e "Saiba mais" (fechadura eletrônica, assistente virtual, decoração online).
- **Passos**: a página de cotação não tem stepper visível na primeira tela.
- **Formulário de cotação**: layout em duas colunas. À esquerda, foto com o slogan "Pra qualquer agora" e a frase "Seguro Residencial da BB Seguros". À direita: título em azul, opção de Pessoa física ou jurídica (rádio), campos e o botão "Avançar".
- **Rodapé**: links institucionais, abas "Para você / Para empresas / Para o agro", texto da SUSEP (processo 15414.606453/2020-10, seguradora Aliança do Brasil), telefones de SAC e ouvidoria, e o canal de conduta ética.
- **Outros**: FAQ com 10 perguntas, botão de WhatsApp e uma aba de chat flutuante. A cotação mostra o selo do reCAPTCHA.

## 4. Jornada de cotação

1. A partir de "Faça sua cotação" (hero) ou "Simule online" (cards), abre `cotacaoseguroresidencial.bbseguros.com.br/home` em nova aba.
2. **Tela 1 (parei aqui)**: "Vamos iniciar a cotação do seu seguro residencial. Primeiro nos conte um pouco sobre você." Campos: tipo de pessoa (física ou jurídica), nome completo, CPF, celular, e-mail, data de nascimento. Botão "Avançar".
3. **Ponto de parada**: esta tela já exige dados pessoais. Não preenchi nada.
4. Não observado: quantas telas vêm depois, a ordem das perguntas, a barra de progresso, como preço e coberturas são exibidos, e quais campos são obrigatórios além dos visíveis.

Não foi possível ver: a tela de resultado e o fechamento da contratação.

## 5. Tom de voz

Frases literais, com a página de origem:
1. "Seus imprevistos não tem hora certa para acontecer." (produto, seção Assistências 24 horas)
2. "E deixa os perrengues do lar que a gente resolve." (produto, seção "Toda proteção para o lugar mais especial")
3. "Todo o processo pode ser feito de forma online." (produto, seção "Contrate online")
4. "Rápido, prático e a poucos cliques." (produto, seção "Contrate online")
5. "Ficou na dúvida? Chama a gente agora!" (produto, rodapé da FAQ)

Descrição: o tom é próximo e coloquial, com expressões do dia a dia ("perrengues", "mãozinha no lar", "chama a gente"), voltado a quem quer praticidade e tranquilidade em casa. Usa tratamento informal ("você"), frases curtas e promessas de rapidez e facilidade. Os textos jurídicos ficam no rodapé, em linguagem formal e longa.

## 6. Coberturas e assistências destacadas

- **Destaques do site**: "Coberturas exclusivas": cobre danos por alagamento (enchentes, chuvas, rompimento de tubulação), apresentado como "primeiro seguro residencial" com essa cobertura. Parcelamento em até 18 meses e pagamento no cartão ou em conta.
- **Coberturas (plano Prático)**: danos elétricos; vendaval; quebra de vidros; roubo e/ou furto de bens; pequenos reparos; incêndio e raio; danos por água; impacto de veículos ou queda de aeronave.
- **Assistências ("Casa em apuros")**: chaveiro; eletricista; encanador; desentupimento; cobertura provisória de telhados; limpeza após sinistro.
- **Benefício premium (Total)**: escolha de um entre fechadura eletrônica, assistente virtual e decoração online.

## 7. Screenshots


Não capturei screenshots dos cards de plano nem do rodapé; a descrição vem do texto da página e do CSS.

## 8. O que não consegui ver e por quê

- **Telas após a primeira da cotação**: exigem CPF, e-mail e telefone para avançar. Parei conforme a regra.
- **Página "Coberturas e assistências" separada**: não existe como página própria. As coberturas aparecem na página do produto e em cada plano (`residencial-pratico`, `residencial-total`). Visitei só o Prático; não visitei o Essencial nem o Total.
- **Cores exatas de botões de chamada (Simule online, Faça sua cotação)**: li a cor de fundo pelo CSS, mas nos botões de hero e cards o valor computado não bateu com a cor visível em tela. Trate os hex dos botões como aproximados.
- **Logotipo e imagens**: não copiados; só descritos.
