# Cores e tipografia do site BB Seguros (Seguro Residencial)

Inspeção de leitura feita no Chrome em 28/10/2026, na página https://www.bbseguros.com.br/seguros/seguro-residencial. Nenhum formulário foi preenchido e nenhum bloqueio foi contornado (a página carregou sem o bloqueio Incapsula).

Método: `getComputedStyle` em todos os elementos do `body` (cor de fundo, cor do texto e cor da borda), contagem de frequência, leitura das regras `:root` e busca de regras `:hover` nas folhas de estilo acessíveis.

## Tabela de elementos

| Elemento | Cor de fundo | Cor do texto | Hex | Onde aparece |
|---|---|---|---|---|
| Header (`<header>`) | transparente (herda branco) | `#212529` | fundo `#FFFFFF` | Topo da página |
| Barra de atalhos (`.shortcuts-region`) | transparente | `#212529` | fundo `#FFFFFF` | Faixa "Contratar um seguro / Acionar e acompanhar / Solicitar assistência" |
| Menu de Seguros (`nav.block-menu`) | `#465EFF` | `#FFFFFF` | fundo `#465EFF` | Barra de menu azul, com "Pra Você", "Seguro pra Vida" e "Seguro Residencial" |
| Item de menu ativo (`.menu-item--active-trail`) | `#5A6FFF` | `#FFFFFF` | fundo `#5A6FFF` | Item "Seguro Residencial" no menu |
| Item de menu "Fale Com a Gente" e destaque (`.highlight-item`) | `#FCFC30` | `#212529` | fundo `#FCFC30` | Item de destaque do menu |
| Área do cliente (botão mobile) | `#5A6FFF` | `#FFFFFF` | fundo `#5A6FFF` | Botão "ÁREA DO CLIENTE" |
| Hero / título (`h1`) | transparente | `#5A6FFF` | texto `#5A6FFF` | Título sobre fundo branco (não há hero azul com título amarelo) |
| Subtítulo / preço (`p`) | transparente | `#5A6FFF` | texto `#5A6FFF` | Ex.: "R$ 19,90* por mês" |
| Botão primário "Contratar seguro" (link) | transparente | `#465EFF` | texto `#465EFF` | Link "CONTRATAR SEGURO" no menu |
| Botão "Faça sua cotação" | `#FF6F68` | (branco) | fundo `#FF6F68` | Chamada de cotação, seção "Ficou na dúvida? Chame..." |
| Banner de nível três (`.banner-nivel-tres-row`) | `#FCEE4F` | (escuro) | fundo `#FCEE4F` | Faixa "Seguro Residencial O S..." |
| Cards de planos (`.card-plans`) | `#F9F7FF` | `#212529` | fundo `#F9F7FF`, borda `#DDE4FC` | Cards dos planos do seguro |
| Itens de lista (`.paragraph--type--lista-de-topicos`) | `#F9F7FF` | `#212529` | fundo `#F9F7FF` | Lista de tópicos |
| Bordas de itens (`.item`) | transparente | n/a | borda `#DDE4FC` | Itens de seleção e cards |
| Fundo do menu expandido (`div`) | `#E5E8FF` | n/a | fundo `#E5E8FF` | Painel "Menu de Seguros" |
| Ícones de benefício (`.beneficio-premium__product-icon`) | `#FFE352` | n/a | fundo `#FFE352` | Ícones de benefícios |
| Botões de acessibilidade ("Recursos Assistivos", "Acessível em Libras") | `#003087` | (branco) | fundo `#003087` | Botões de acessibilidade |
| Rodapé (`footer`) | `#465EFF` | `#FFFFFF` | fundo `#465EFF`, texto `#FFFFFF` | Rodapé "Menu de Seguros Footer" |
| Breadcrumb ativo (`li.breadcrumb-item.active`) | transparente | `#4C4C4C` | texto `#4C4C4C` | Trilha "Residencial" |
| Link de "pular para o conteúdo" (acessibilidade) | transparente | `#007BFF` | texto `#007BFF` | Link oculto de acessibilidade, visível só no foco |
| Fundo principal (`main` e `body`) | `#FFFFFF` | `#212529` | fundo `#FFFFFF` | Fundo geral da página |

Observação sobre hover: não foram encontradas regras `:hover` com as cores de destaque nas folhas de estilo acessíveis. Os estados de hover dos botões não foram confirmados por esta leitura.

## Variáveis CSS (`:root`)

O `:root` que aparece nas folhas de estilo é o do Bootstrap 4 padrão (`--blue: #007bff`, `--primary: #007bff`, `--gray-dark: #343a40` etc.). O site não redefine essas variáveis para as cores de marca. As cores da marca (`#465EFF`, `#5A6FFF`, `#FCFC30`) estão escritas diretamente nas regras das folhas de estilo, não como variáveis.

## Cores de destaque por frequência de uso (top 10)

Contagem de elementos com cor de fundo, não contando transparente. Fonte: varredura de `body *`.

| # | Hex | Elementos (fundo) | Papel observado |
|---|---|---|---|
| 1 | `#5A6FFF` | 40 | Menu (item ativo), botão "Área do cliente", texto de título e preço |
| 2 | `#465EFF` | 13 | Barra de menu, rodapé, link de contratação |
| 3 | `#F9F7FF` | 13 | Cards e listas de tópicos |
| 4 | `#FCFC30` | 8 | Item de destaque do menu |
| 5 | `#4D64FF` | 8 | Variação próxima de `#465EFF` (não identificada com precisão) |
| 6 | `#FFFFFF` | 6 | Fundo geral |
| 7 | `#FCEE4F` | 3 | Banner de nível três |
| 8 | `#FFE352` | 3 | Ícones de benefício |
| 9 | `#3751FF` | 2 | Variação de azul (não identificada com precisão) |
| 10 | `#003087` | 2 | Botões de acessibilidade |

Cores de texto mais frequentes: `#FFFFFF` (92), `#5A6FFF` (90), `#212529` (73), `#4C4C4C` (44), `#007BFF` (9), `#465EFF` (8).

Cores de borda: `#DDE4FC` (11) é a borda dominante dos cards e itens.

## Presença de `#465EFF` e `#5A6FFF`

- **`#465EFF` aparece sim.** Fundo da barra de menu (`nav.block-menu`), fundo do rodapé (`footer`), texto do link "CONTRATAR SEGURO" e alguns itens do menu ("Pra Você", "Seguro pra Vida").
- **`#5A6FFF` aparece sim.** Fundo do item de menu ativo "Seguro Residencial", fundo do botão "Área do cliente" (mobile), e texto do `h1` e do preço.

## Tipografia

- Fonte de títulos: **BancoDoBrasilTitulos**, sans-serif. `h1` com 32px e peso 700.
- Fonte de texto: **BancoDoBrasilTextos**, com fallbacks Inter, Lato e `-apple-system`.
- Fonte base do `body` no computado: `Inter, sans-serif`, 14px, peso 400 (é o fallback computado).
- A fonte de títulos é a fonte institucional do BB (de licença do próprio banco), não deve ser usada no nosso protótipo sem permissão. Para o demo, usar uma fonte livre.

## Conclusões para o protótipo (demo do Datathon)

- A página real é majoritariamente branca, com azul `#465EFF` / `#5A6FFF` como cor de marca e amarelo `#FCFC30` como destaque do menu. O `h1` é azul sobre branco, e não amarelo sobre azul como estava descrito em `CLAUDE.md` na seção de visual do demo. Vale corrigir a descrição do demo: o "hero azul com título amarelo" não foi confirmado nesta página.
- Os valores em `dict COR` do demo (`#465EFF` / `#FCFC30`) estão coerentes com as cores observadas. `#5A6FFF` também aparece com peso alto e pode ser usado como azul secundário.
- Nenhuma cor aqui é oficial. São valores observados em produção e servem só de referência visual.
