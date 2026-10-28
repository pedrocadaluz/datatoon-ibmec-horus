# Validação da PWA Casa Gêmea

Executada em 28/10/2026, localmente, sem publicação, commit ou push.

## Resultado

| Verificação | Evidência |
|---|---|
| Build TypeScript e Vite | Passou, build de produção com service worker gerado |
| API Python | 10 testes passaram, incluindo paridade de recomendações e todas as faixas dos 138 imóveis com os dois CSVs de entrega atuais |
| Navegador | 18 testes passaram |
| Lighthouse móvel | Desempenho 98, acessibilidade 100, boas práticas 100 |
| Instalabilidade | Chrome com perfil normal temporário, manifesto sem erros, service worker controlando a página, Page.getInstallabilityErrors sem erros |
| Offline e privacidade | Casco abre offline, API não responde do cache, nenhum imóvel reaparece após recarga, localStorage vazio |
| Rede local | Página /celular e /api/health acessíveis no IP privado desta execução |
| Inicializador | Início e saída com -Verificar em 5181/8011, portas livres e sem processos Python/Node remanescentes |
| Revisão independente | Corrigido encerramento da árvore do Python no Windows; nenhum achado importante pendente |

Os relatórios Lighthouse estão em [HTML](evidencias/lighthouse-mobile.report.html) e [JSON](evidencias/lighthouse-mobile.report.json). A checagem de instalação está em [pwa-instalabilidade.json](evidencias/pwa-instalabilidade.json). Lighthouse 13 não oferece mais categoria PWA; os critérios de instalação foram verificados diretamente no navegador.

## Jornadas e acessibilidade

Playwright usou os perfis devices['Pixel 7'] e devices['iPhone 14'], ambos em Chromium instalado. O caso IMO_CASO_00003_01 foi percorrido até Prático e incêndio de R$ 505.300 a R$ 633.500. O teste verifica que Não sei aparece acima do resumo fixo na primeira pergunta, que o selo permanece visível e que o painel de recomendação abre e fecha.

Cliente, Gerente, SAC e Agente foram exercitados em 360, 390, 430, 768 e 1280 px, sem rolagem horizontal. Nos celulares, o teste também percorre os três passos da apresentação, verifica a Casa Gêmea expansível, o painel de recomendação e os controles de toque visíveis com pelo menos 44 px. Texto ampliado, redução de movimento, teclado, foco dos dialogs e verificações axe A/AA fazem parte da suíte.

Screenshots principais:

- [Pixel 7, pergunta](evidencias/pwa-pixel-7-inicio.png) e [painel](evidencias/pwa-pixel-7-painel.png).
- [iPhone 14, pergunta](evidencias/pwa-iphone-14-inicio.png) e [painel](evidencias/pwa-iphone-14-painel.png).
- [Cliente](evidencias/pwa-celular-cliente.png), [Gerente](evidencias/pwa-celular-gerente.png), [SAC](evidencias/pwa-celular-sac.png), [Agente](evidencias/pwa-celular-agente.png).
- [Offline](evidencias/pwa-offline.png) e [QR local](evidencias/pwa-acesso-celular-qr.png).

## Limites e fora do escopo

Não houve teste em telefone físico, Safari real ou instalação e confiança de certificado no aparelho. A LAN HTTP permite a jornada online; instalação PWA completa e service worker no telefone dependem de HTTPS local confiável, conforme o README. A validação de instalabilidade foi feita em localhost, que é contexto seguro.

O modo escuro opcional ficou de fora. Não há autenticação, contratação, persistência de respostas ou publicação na internet. Nenhum dado de cliente é salvo no cache do service worker. Novos builds aguardam a ação Atualizar agora; essa ação informa que reiniciará as respostas. O ciclo entre duas versões foi revisado no código, sem simular uma atualização de produção.

Nenhum bug funcional confirmado permanece pendente. A suíte Python emite somente um aviso de depreciação de httpx em Starlette. Auditoria automatizada e emulação não equivalem à validação completa com tecnologias assistivas e aparelhos físicos.
