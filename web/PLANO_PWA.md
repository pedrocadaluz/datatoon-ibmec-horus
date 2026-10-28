# Casa Gêmea PWA

Especificação: `_referencias_frontend/BRIEF_PWA.md`. Implementação autorizada no clone atual, sem commit, push ou publicação. Alterações apenas em web/, api/ e scripts/05_rodar_web.ps1.

- [x] Mobile: navegação inferior com seletor de caso, perguntas confortáveis, contador fixo, recomendação em bottom sheet acessível, gestos e safe areas.
- [x] PWA: manifesto, ícones próprios, instalação, casco offline sem dados de imóveis, atualização explícita sem perder respostas.
- [x] Rede local: script único de inicialização, API/Vite em 0.0.0.0, CORS de origens locais explícitas, QR em /celular, suporte a certificado local opcional.
- [x] Verificação: testes existentes, Pixel 7 e iPhone 14, todos os canais em 360/390/430/768/1280, cache sem API, instalação via Chrome, Lighthouse móvel, screenshots e README.

Decisões de implementação: manter React/TypeScript e o contrato existente. Service worker próprio gerado a partir da lista fechada dos arquivos estáticos do build, sem cache de runtime. API só por rede e com Cache-Control no-store. Cálculos/respostas continuam em memória. O modo de demonstração usa build de produção; HTTPS confiável é necessário para instalação completa no celular pela LAN. HTTP local continua permitindo a jornada no navegador.

Lighthouse atual não possui categoria PWA: medir performance e acessibilidade e verificar instalação separadamente pelo Chrome DevTools Protocol e manifesto/SW reais. Não instalar certificados no sistema sem ação explícita do usuário. Não usar túnel público.
