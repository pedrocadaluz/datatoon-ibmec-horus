# Implementação Casa Gêmea

Brief vinculante: `_referencias_frontend/BRIEF.md`. Execução autorizada no clone atual, sem commit ou push. Só criar `web/`, `api/` e acrescentar duas dependências ao requirements.

- [x] API fina: inicializar Motor uma vez, listar 138 imóveis por campos permitidos, recomendar sem alterar o contrato, validar entrada e erros.
- [x] Cliente: visual próprio de casa, selos/confiança, pergunta única com Não sei e número, histórico reversível, recomendação, faixas e comparação ao vivo.
- [x] Canais: ficha de gerente, roteiro SAC, JSON copiável, respostas compartilhadas por imóvel, apresentação e acessibilidade.
- [x] Verificação: testes API contra CSVs de entrega, jornadas no navegador em 3 semáforos, responsividade, build, screenshots e README.

Arquitetura: Vite + React + TypeScript, CSS com transições e SVG próprio. FastAPI mantém o contrato Python como autoridade. Não atribuir percentuais fictícios à confiança.

Riscos a verificar: bases originais ausentes neste clone; troca rápida de imóvel; Não sei em declaração; erro/rede sem perda de respostas; inelegível sem plano ou contratação; texto do motor com travessões (normalizar só apresentação).

## Registro

Leitura do brief, contrato, motor e referências concluída. Git pull: atualizado. Arquivos preexistentes de docs e referências preservados.

API: 8 testes passaram, cobrindo 138 planos/elegibilidades/confianças e todas as faixas do CSV regenerado. Web: 8 testes passaram, cobrindo 3 semáforos, jornada real, quatro canais, AA em desktop/celular, faixa larga, contador e textos do contrato, teclado, zoom, erro de rede, valor exato isolado por imóvel e disputa de execução JSON. Build TypeScript/Vite passou.

Decisões: execução no clone solicitado, sem worktree/commit; plano e registro ficam em web/ para respeitar o escopo permitido. Caminhos das bases configuráveis somente nesta execução. Completar NAO_SEI em memória permite usar o ramo já existente do motor, preservando inferência. Validação numérica mínima respeita a precisão de arredondamento do motor (1 m² e R$ 100), com máximo técnico de precisão segura no navegador. Confiança visual em três categorias, sem percentuais inventados. Contador consumido diretamente do novo bloco jornada. Fonte e ícones locais.

Revisão independente concluída. Corrigidos: valor não enviado persistindo entre imóveis com a mesma pergunta; falta de selo/confiança nas perguntas de estimativa (inclusive SAC e fila do gerente); números extremos retornando 500; mensagem de transporte em inglês. Os dois últimos foram tratados como falhas do contrato HTTP e do requisito de idioma, apesar da baixa probabilidade no pitch. Reproduções observadas falhando antes das correções e suíte inteira verde após a rodada. Nenhum achado funcional pendente. Correção atuarial, publicação/autenticação e auditoria manual completa de acessibilidade continuam fora do escopo contratado para este protótipo.
