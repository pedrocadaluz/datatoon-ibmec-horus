# Horus · Casa Gêmea

Web-app PWA do Datathon Proteção Inteligente. Quatro canais consomem o mesmo motor Python, sem reimplementar suas regras. Não há contratação real.

## Rodar o web-app no computador e no celular

Pré-requisitos: Python 3.12 ou 3.13, Node 24 e npm 11. Na raiz do repositório, execute:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/05_rodar_web.ps1
```

O script prepara os ambientes, compila a PWA e inicia API e frontend em `0.0.0.0`. Ele imprime os endereços da rede local e a página do QR code. No computador, abra **http://localhost:5173**. Para o telefone, abra **http://localhost:5173/celular** no computador e escaneie o QR. O endereço desta execução é **http://172.16.1.109:5173**; ele depende da rede e o terminal é a referência atual. Computador e telefone precisam estar na mesma rede Wi-Fi.

A API permanece na porta 8000, com documentação em `/docs`. O telefone acessa apenas o frontend: o proxy encaminha `/api` na própria origem. CORS permite somente localhost e os IPs privados detectados neste computador, nas portas da demonstração, sem wildcard ou credenciais. As respostas HTTP da API têm `Cache-Control: no-store`. O QR é gerado localmente, sem serviço externo.

Deixe esse terminal aberto. Ctrl+C encerra as árvores dos dois processos iniciados por essa execução, incluindo o processo filho do Python no Windows. O script não mata servidores preexistentes nem altera o firewall. Se uma porta estiver ocupada, feche a execução anterior ou use `-PortaWeb 5174 -PortaApi 8001`. Se o Windows pedir acesso à rede, permita o Node apenas na rede privada usada na demonstração.

O motor precisa das pastas originais `Seguro_Residencial_Desenvolvimento` e `Seguro_Residencial_Teste_Comum`. O inicializador procura na raiz e nas estruturas convencionais de extração em Downloads. Para outro caminho, acrescente `-Dados 'C:\pasta-que-contem-as-duas-bases'`. A variável `CASA_GEMEA_DADOS` também é aceita. Os originais são somente lidos. Nenhuma base foi incorporada ao casco offline.

### Instalar no celular e a limitação de HTTPS

Em HTTP pelo IP da LAN, a jornada funciona no navegador. O service worker e a promoção de instalação exigem **contexto seguro**: HTTPS confiável, ou localhost no próprio dispositivo. Logo, o HTTP do computador não vira uma PWA offline completa no telefone. Não há túnel público nem envio de dados para serviço externo. [Requisitos de instalação](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable).

A alternativa local é um certificado de desenvolvimento confiável com [mkcert](https://github.com/FiloSottile/mkcert). Instale a ferramenta conforme o projeto e, no computador da demonstração:

```powershell
New-Item -ItemType Directory -Force web/.certs
mkcert -install
mkcert -cert-file web/.certs/cert.pem -key-file web/.certs/key.pem 172.16.1.109 localhost 127.0.0.1
powershell -ExecutionPolicy Bypass -File scripts/05_rodar_web.ps1 -Certificado web/.certs/cert.pem -Chave web/.certs/key.pem
```

Troque o IP pelo mostrado no terminal. Para o telefone confiar no certificado, instale também nele **somente o certificado público `rootCA.pem`**, localizado por `mkcert -CAROOT`. No iPhone: instalar o perfil e habilitar confiança em Ajustes > Geral > Sobre > Confiança em certificados. No Android/Chrome: instalar como certificado de CA nas configurações de segurança do aparelho. Não transfira `rootCA-key.pem` nem a chave do servidor. O script aceita os arquivos fornecidos e não instala certificados no sistema. A pasta `web/.certs/` e arquivos de chave estão ignorados pelo Git.

Depois, abra o endereço **https://IP:5173**. No Android/Chrome, toque em **Instalar app** quando o navegador oferecer, ou no menu de instalação. No iPhone/Safari: **Compartilhar, Adicionar à Tela de Início**. A interface instalada usa modo standalone e respeita as áreas seguras da tela. Os botões de instalação são condicionais à plataforma e à oferta do navegador. O teste de instalação foi feito em Chrome normal com perfil temporário; Pixel 7 e iPhone 14 foram emulados, sem afirmar teste em aparelho físico.

### Desenvolvimento separado

Os dois comandos anteriores continuam disponíveis para desenvolvimento, em terminais separados:

```powershell
powershell -ExecutionPolicy Bypass -File api/rodar.ps1
npm --prefix web start
```

Esse modo usa o servidor de desenvolvimento do Vite. O service worker é registrado **somente no build de produção**, servido pelo script conjunto ou por `npm --prefix web run preview`. Fontes e ícones são locais; internet é necessária apenas para instalar dependências na primeira preparação.

## Stack em três linhas

- Vite, React e TypeScript: desenvolvimento rápido, contrato tipado e build estático pequeno.
- CSS próprio com transições e SVG autoral: identidade Horus, sem biblioteca visual ou serviço de imagens; Inter distribuída localmente pelo pacote com licença OFL.
- FastAPI e Uvicorn: adaptador fino que carrega `Motor()` uma vez e entrega a saída de `recomendar()` diretamente.

Referências técnicas consultadas: [Vite](https://vite.dev/guide/), [corpos de requisição FastAPI](https://fastapi.tiangolo.com/tutorial/body/) e [ciclo de vida FastAPI](https://fastapi.tiangolo.com/advanced/events/).

## Uso e roteiro de apresentação

O caso inicial é `IMO_CASO_00003_01`, de Curitiba. Todas as respostas ficam somente na memória do navegador, separadas por imóvel e compartilhadas pelos quatro canais. Recarregar a página limpa a sessão. “Recomeçar” limpa o imóvel atual. “Editar” remove a resposta escolhida e as posteriores, para o motor refazer a ordem.

1. Mostre a Casa Gêmea: toque em um dado para abrir sua evidência. “Ver os outros dados da casa” revela uso, acabamento, paredes e obras. Todo valor inferido acompanha selo e confiança.
2. Responda “Não” à obra e “Não, eu moro nele” ao vínculo. O plano passa de Total para Prático. Informe 160 m² e confirme a declaração. O caso termina com faixa de incêndio de R$ 505.300 a R$ 633.500.
3. Mostre “Ver detalhes da recomendação” e “Todas as coberturas”. O destaque amarelo mostra a lacuna de aluguel quando o Total protege um inquilino ou locador. A regra da RC familiar aparece junto à sua faixa.
4. Alterne Gerente, SAC e Agente: as mesmas respostas e os mesmos números continuam disponíveis. No Agente, edite a entrada, execute e copie entrada ou saída.

O contador usa **diretamente `jornada.perguntas_evitadas` e `campos_formulario_tradicional`**. A justificativa curta usa `recomendacao.justificativa_curta`. A confiança é categórica: os três segmentos representam baixa, média e alta, sem probabilidades inventadas. A faixa é limite sugerido de indenização; não é valor do seguro a pagar. Faixas cuja razão máximo/mínimo ultrapassa 4 exibem “Faixa larga: confirme para estreitar” ao abrir a cobertura.

No celular, as abas e a troca de imóvel ficam na navegação inferior. O plano, a faixa de incêndio e o semáforo ficam no resumo fixo; toque ou deslize para cima para abrir as coberturas. O painel é um dialog nativo com foco contido e retorno ao botão; Fechar, Escape ou deslizar pelo puxador o recolhe. A Casa Gêmea continua disponível na seção expansível sob a pergunta. O contador fica fixo no topo e usa somente os valores do motor.

Pressione **P** fora de campos e botões para entrar no modo apresentação. **Setas esquerda/direita** percorrem Casa Gêmea, perguntas e recomendação. **1 a 9** registram a opção numerada da pergunta atual; **Esc** sai. Os botões visíveis também permitem navegar. No telefone, os lembretes de atalhos ficam ocultos. A− e A+ ajustam o texto de 90% a 130%. Redução de movimento do sistema é respeitada.

## Estrutura

| Caminho | Responsabilidade |
|---|---|
| `web/src/App.tsx` | Sessões por imóvel, canais, apresentação e tratamento de rede |
| `web/src/House.tsx` | Ilustração conceitual própria, campos, selos e evidências |
| `web/src/Question.tsx` | Pergunta única, opções, valor exato e histórico editável |
| `web/src/Recommendation.tsx` | Plano, justificativas, canal, faixas e comparação |
| `web/src/Channels.tsx` | Ficha do gerente e contrato JSON do agente |
| `web/src/types.ts`, `api.ts`, `format.ts` | Tipos, transporte HTTP e apresentação em pt-BR |
| `web/tests/` | Jornadas reais e verificação WCAG AA com Playwright e axe |
| `web/evidencias/` | Screenshots das jornadas e estados importantes |
| `api/main.py` | Validação HTTP e encaminhamento ao motor Python |
| `api/test_api.py` | Testes de entrada, privacidade e paridade dos 138 casos |
| `api/rodar.ps1` | Ambiente Python isolado e inicialização local |

## Casco offline e privacidade

O manifesto é `web/public/manifest.webmanifest`. O service worker é gerado por `web/pwa-build.ts` a partir de uma lista fechada dos arquivos estáticos do build: HTML, JS, CSS, fontes e ícones. Não há cache de runtime. Requisições `/api`, POSTs e outras origens não são interceptadas; nenhuma resposta de recomendação, lista de imóveis ou IP local é armazenada. O app abre offline com uma mensagem de reconexão; após recarregar offline, nenhum caso reaparece. As respostas continuam somente na memória do React, sem localStorage, IndexedDB ou sincronização em segundo plano.

Versões novas aguardam confirmação em “Atualizar agora”, pois a atualização recarrega a sessão. “Depois” mantém as respostas em memória. O cache antigo do casco é removido na ativação da nova versão. O cliente não faz decisões de seguro offline.

## API e limites

- `GET /api/health`: disponibilidade do motor.
- `GET /api/rede`: IPs privados deste computador para gerar o QR local, sem dados de imóveis.
- `GET /api/imoveis`: os 138 identificadores, cliente sintético e município/UF. Seleção explícita de campos, sem serializar o perfil do cliente.
- `GET /api/imoveis/{id}/sinais`: conflitos registrados na inferência inicial. As evidências atuais vêm do próprio contrato.
- `POST /api/recomendar`: recebe a versão 1.0, imóvel e todas as respostas; devolve o contrato real, incluindo os novos campos de justificativa e jornada.

IDs inexistentes retornam 404; versão ou resposta inválida, 422; base ausente, 503 com instrução de correção. Números devem ser finitos e não ultrapassar a precisão inteira segura do navegador (`2**53 - 1`). A API exige pelo menos 1 m² ou R$ 100 em bens, coerente com a precisão inteira/de centenas usada pelo motor. O frontend só grava a resposta quando a API aceita a atualização. Trocar rapidamente de imóvel cancela a consulta anterior, inclusive execuções do painel JSON. Valores ainda não enviados são limpos ao trocar de imóvel.

Compatibilidade documentada: o motor já trata `NAO_SEI` preservando a inferência, mas algumas listas de opções não continham esse código. A API completa as listas em memória, expondo esse ramo existente em todas as perguntas. Nenhum arquivo de `src/` foi alterado para isso. Plano, faixas, confiança e ordem permanecem decididos pelo motor.

## Verificação

Além dos testes abaixo, `npm --prefix web run audit:mobile` gera os relatórios Lighthouse locais em `web/evidencias/lighthouse-mobile.report.*`. Lighthouse atual não possui mais a categoria PWA desde a versão 12; os critérios de instalação são verificados separadamente pelo Chrome DevTools Protocol e registrados em `pwa-instalabilidade.json`. [Mudança oficial](https://developers.google.com/speed/docs/insights/release_notes). Os testes de navegador abrem automaticamente um preview de produção na porta 4173 para verificar o service worker.

Com API e frontend em execução:

```powershell
api/.venv/Scripts/python.exe -m pip install -r api/requirements-test.txt
api/.venv/Scripts/python.exe -m unittest api.test_api -v
npm --prefix web run build
npm --prefix web test
powershell -ExecutionPolicy Bypass -File scripts/05_rodar_web.ps1 -PortaWeb 5181 -PortaApi 8011 -Verificar
```

Se as bases estiverem fora da raiz, configure `CASA_GEMEA_DADOS` no terminal dos testes Python. Os testes usam Chrome instalado, sem baixar outro navegador. Os relatórios temporários ficam ignorados pelo Git. Os testes de acessibilidade usam redução de movimento para medir o contraste estável, fora das animações de entrada.

## Decisões de design

Azul `#5A6FFF`, amarelo `#FCFC30` pontual, papel `#F9F7FF`, bordas `#DDE4FC`, cantos de 4 a 6px e Inter. O azul de texto e ações é mais escuro para contraste AA. Marca e casa em SVG são autorais; não representam a planta real do imóvel. Não há logotipo ou imagens do BB. Dados sintéticos e condição de protótipo aparecem na página. Textos humanos do motor têm travessões normalizados só na apresentação; no painel JSON, o caractere é escapado, preservando o valor do contrato ao copiar e interpretar.

## Entrega

- **Pronto:** PWA com manifesto, ícones 192/512/maskable e iOS, casco offline sem dados, instalação condicional, QR local, navegação inferior com seletor de imóvel, painel de recomendação acessível, safe areas, feedback tátil opcional e Cliente ponta a ponta, Casa Gêmea com evidências, perguntas e valores exatos, plano/faixas/canal ao vivo, explicações curtas e detalhadas, contador real, destaque de aluguel, RC, quatro canais, apresentação, texto ajustável, responsividade e testes.
- **Fora do escopo:** contratação, preços de prêmio, autenticação, persistência, publicação e alteração das regras Python. A API aceita a rede local, com CORS restrito e proxy de mesma origem para o telefone. Não foi publicada na internet.
- **Validação final:** 10 testes Python e 18 testes de navegador passaram; build TypeScript/Vite passou. Lighthouse móvel: desempenho 98, acessibilidade 100 e boas práticas 100. Chrome sem erros de instalabilidade. Inicialização e encerramento do script verificados em portas alternativas, sem processos ou listeners restantes. Paridade dos 138 imóveis e de todas as faixas com os dois CSVs regenerados. Verificação automática WCAG A/AA nas quatro visões e no celular sem violações detectadas. Screenshots em `web/evidencias/`. Revisão independente concluída e achados corrigidos com regressões.
- **Limites da validação:** Pixel 7 e iPhone 14 emulados em Chromium; aparelho físico, Safari real e confiança do certificado no telefone não foram testados. O modo escuro opcional ficou de fora. Detalhes em [PWA_VALIDACAO.md](PWA_VALIDACAO.md).
- **Bugs conhecidos:** nenhum problema funcional confirmado pendente. A ferramenta de testes Python emite um aviso de depreciação de httpx em Starlette, sem impacto na aplicação. A verificação automatizada de acessibilidade não substitui uma auditoria manual completa com tecnologia assistiva.

Não foram feitos commit ou push. A pasta de referência permanece fora da entrega de código. Frontend, testes e adaptador foram produzidos com assistência de IA; a decisão de seguro continua no motor determinístico do projeto.

## Visões App e Comparativo (retiradas da tela)

As visões **App** (simulador do app com 3 personas) e **Comparativo** saíram da navegação em 28/10 para deixar a demonstração focada nos quatro canais. Os componentes (`AppSim.tsx`, `Comparativo.tsx`, `MotorPensou.tsx`, `personas.ts`) continuam no repositório, sem uso. As personas seguem documentadas em `docs/11_personas.md`, geradas por `scripts/10_personas.py`.
