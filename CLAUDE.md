# Datathon Proteção Inteligente (BBDW + Ibmec) — Seguro Residencial

Contexto para continuar o trabalho em qualquer sessão. Idioma do projeto: **português**.

## Prazos
- Evento: 27 a 29/10/2026.
- **Entrega obrigatória: 29/10 até 10h** (meta interna: 9h). Sem ela o time não apresenta.
- Vídeo ≤ 5 min · pitch 5 min · perguntas da banca 5 min.

## Repositório
- GitHub: https://github.com/pedrocadaluz/datatoon-ibmec-horus (time **Horus**: Ludmila, Milton, Anna, Isabella, Pedro). Branch `main`; a pasta local é o clone.
- `.gitignore` do repositório exclui as bases originais (`Seguro_Residencial_*`) e o guia em PDF. As saídas tratadas (`saidas/`, `entrega/`) são versionadas.
- CSVs da entrega ficam em `entrega/` (raiz), como previsto na estrutura do Pedro.
- Antes de commitar: rodar scripts 01 a 04 do zero; dar `git pull` antes de começar (outros membros também fazem push).

## Materiais recebidos
- `DatathonBBDW-GuiaDosTimes.pdf` — regras, entregáveis, critérios (fonte principal).
- `Seguro_Residencial_Desenvolvimento/` — 2.200 clientes, 2.578 imóveis. Para explorar e calibrar.
- `Seguro_Residencial_Teste_Comum/` — 120 clientes, 138 imóveis (`CASO_xxxxx`). **É a base da entrega.**
- Tabelas: `clientes`, `enderecos_imoveis`, `sinais_imobiliarios`, `bens_compras`, `territorio`, `catalogo_coberturas_fixas_planos`, `dicionario_dados`, `template_resultado_times` (1 linha/imóvel) e `template_coberturas_times` (só cabeçalho; 1 linha por cobertura).
- **Não alterar os arquivos originais** dessas pastas.

## A ideia: "Casa Gêmea" (ideia da Ludmila)
Um motor que monta uma **cópia virtual da casa do cliente** com os dados que o banco já tem, **faz só as perguntas que mudam o resultado** e recomenda o plano com faixas, explicando **por que o plano abaixo não basta e por que o de cima seria desnecessário**. O mesmo motor serve a todos os canais; só muda a interface.

Fluxo: **Elegibilidade → Casa Gêmea (com selos) → Perguntas que mudam o resultado → Plano + faixas → Comparação por lacuna de cobertura → Canais**

Decisões tomadas:
- **Selos em todo campo da casa gêmea**: `OBSERVADO` / `ESTIMADO` / `A_CONFIRMAR`, com confiança. Nunca apresentar estimativa como fato.
- **Perguntas fechadas com opções personalizadas** a partir dos dados (ex.: "Seu imóvel tem entre 70 e 100 m²? Sim / Menor / Maior / Não sei"). "Não sei" é sempre válido: a faixa fica mais larga, mas a cotação não trava.
- **Escolha da pergunta é calculável**: para cada pergunta, simular as respostas possíveis e medir quanto o plano/faixa muda. Pergunta-se em ordem de impacto. **Regra de parada**: nenhuma resposta restante muda o plano nem a faixa além de um limite. Isso também gera a métrica de sensibilidade.
- **Comparação por lacuna de cobertura, nunca por preço** (não há preço na base). Ex.: "O Essencial não cobre roubo e você tem R$ X em eletrônicos"; "O Total inclui perda de aluguel, mas o imóvel é seu e quitado". Tom: "recomendação transparente" — evitar frases que soem como acusação ao gerente/banco.
- **Motor de regras determinístico decide e calcula; IA (se usada) só redige texto.** Não focar em chatbot/LLM; o diferencial é a lógica.
- **Canais**: App (cliente clica), Gerente (pergunta, digita, vê o motivo de cada pergunta), SAC/telefone (atendente lê opções), Agentes autônomos (contrato JSON de entrada/saída do motor).
- **Semáforo de canal**: 🟢 One Click Buy (confiança alta) · 🟡 confirmar 1–3 perguntas · 🔴 gerente (obra, vínculo ambíguo, locador).
- **Elegibilidade em 3 níveis**: `ELEGIVEL` · `ELEGIVEL_CONDICIONADO` (plano provisório + confirmação obrigatória) · `INELEGIVEL` (só com evidência). O guia diz "não tratar como elegível **sem validação**" (rural, obra estrutural, condenado, tombado, parede combustível) — não é recusa automática.
- **Privacidade**: idade e renda **nunca** definem risco, plano ou patrimônio. Dependentes/pet só indicam **necessidade** (RC familiar). App/maturidade digital só para **escolha de canal**. Mostrar no pitch: campos usados / só para canal / proibidos. Citar LGPD e minimização.

## O que já descobrimos nos dados (base de desenvolvimento)
- CSVs com BOM → `encoding="utf-8-sig"`. `bem_id` se repete entre as bases: nunca cruzar bases por ele.
- 378 clientes têm 2 imóveis (29% dos imóveis). 21% dos imóveis não são o endereço principal.
- **Elegibilidade**: 100% `REGULAR`; parede só `ALVENARIA` ou `NAO_DISPONIVEL` (78%); não existe campo de rural/tombado. Sinal indireto de obra: `gastos_material_construcao_24m` (18% > 0; 66 casos > R$ 30 mil).
- **Vínculo** (grupos não se sobrepõem): paga aluguel → inquilino (531) · parcela de financiamento → proprietário financiado (781) · recebe crédito compatível com aluguel → locador (241) · nenhum → proprietário quitado (1.025).
- **Tipo**: complemento + `possui_termo_*` + condomínio pago. Casa + condomínio = casa em condomínio (262). Termo apartamento sem condomínio pago (397) = ambíguo.
- **Área** falta em 61%. Correlação com IPTU **0,82** e energia **0,81**; condomínio 0,02, renda 0,01; padrão construtivo não muda a área. Estimar com IPTU + energia (+ município), validar nos 39% com área real e usar o erro para a largura da faixa.
- Padrão construtivo falta em 73%.
- `valor_bem_ponderado_referencia = valor_cadastrado × probabilidade_bem_no_imovel_referencia` (vale em 100%). A probabilidade cai com outra UF/município e sobe com financiamento pelo banco.

## Planos (catálogo — usar estes nomes exatos)
- ESSENCIAL: INCENDIO_RAIO_EXPLOSAO_FUMACA, DANOS_POR_AGUA, VENDAVAL_GRANIZO, IMPACTO_VEICULOS_TERRESTRES, QUEDA_AERONAVE, DANOS_ELETRICOS
- PRATICO: Essencial + ROUBO_FURTO_ARROMBAMENTO, QUEBRA_DE_VIDROS
- TOTAL: Prático + RESPONSABILIDADE_CIVIL_FAMILIAR, PERDA_PAGAMENTO_ALUGUEL, DESPESAS_EMERGENCIAIS
- Assistências **não** entram no template de coberturas.

## Regras de formato da entrega
- Os dois templates preenchidos para **todos** os 138 casos do Teste Comum.
- Faixas em reais, **só números** (sem "R$", sem separador de milhar). Mínimo ≤ máximo.
- Confiança baixa **não** dispensa faixa; ausência de estimativa só excepcional e justificada.
- Entregáveis: 2 CSVs, README.md (equipe, arquitetura, execução, premissas, limitações, métricas, **uso de IA declarado**), código, requirements.txt + versão do Python (3.12.2), documentação de dados externos (fonte, data, licença, método, limitações), vídeo.
- Critérios da banca: Adequação 20% · Inovação 20% · Jornada 15% · Uso dos dados 15% · Explicabilidade 10% · Viabilidade 10% · Privacidade 10%.

## Padrões de desenvolvimento (pedido da equipe)
- **Arquivos sempre organizados e bonitos, prontos para enviar à banca**: nomes claros em português, código comentado com moderação, docstrings curtas, scripts numerados por etapa.
- Tudo em código e reprodutível; o mesmo pipeline roda na base de desenvolvimento e na de teste.
- Estrutura:
  - `src/casa_gemea/` — pacote do motor (carregamento, inferências, regras, perguntas)
  - `scripts/` — etapas executáveis numeradas (`01_...py`, `02_...py`)
  - `saidas/` — arquivos gerados (casa gêmea, templates preenchidos)
  - `docs/` — relatórios e documentação (dados, regras, fontes externas)
  - `dados_externos/` — fontes públicas baixadas (ex.: CUB por UF), com a origem documentada
- Python 3.12; dependências em `requirements.txt`. Registrar no README onde a IA foi usada.

## Plano
1. **27/10 (hoje)**: entender os dados e fazer inferências (casa gêmea: tipo, vínculo, uso, área, conteúdo, alertas, selos) + entender as regras do seguro (elegibilidade, escolha de plano, fórmula das faixas, CUB por UF).
2. **28/10 manhã**: gerar os 2 CSVs obrigatórios (prioridade máxima) e validar formato.
3. **28/10 tarde**: perguntas + comparador, demo (Streamlit), métricas, README.
4. **28/10 noite**: slides, vídeo, ensaio. **29/10 ≤ 9h**: entrega.
- Se atrasar, cortar nesta ordem: interface → comparador visual → enriquecimento extra. Nunca cortar CSVs nem README.

## Status
- [x] Exploração inicial dos dados e leitura do guia
- [x] Casa gêmea (etapa 01) — `python scripts/01_construir_casa_gemea.py` → `saidas/casa_gemea_*.csv` + `docs/01_casa_gemea.md`
  - Pacote: `src/casa_gemea/` (`config`, `carregar`, `area`, `calibracao`, `inferencias`, `regras`, `pipeline`). Modelo de área: erro mediano 13%, R² 0,86, faixa de 80% (−23%/+31%).
  - Sinais combinados: locador só com confiança média se o imóvel não for o endereço principal (186/241 em conflito); quitado com confiança alta se área veio de laudo de financiamento; obra = material ≥30 mil, ou ≥10 mil + vidraçaria, inquilino desce um nível; padrão pelo IPTU/m² vs. cidade só como indício (confiança BAIXA; acerta extremos, não classifica); conflitos detectados (área divergente, locador no endereço principal, apto sem condomínio).
  - Conteúdo: mín = maior entre bens ponderados e 50% das compras 36m; máx = maior entre bens cadastrados e compras.
- [x] Regras do seguro (etapa 02) — `python scripts/02_aplicar_regras.py` → `saidas/recomendacao_*.csv`, `saidas/coberturas_*.csv` + `docs/02_regras_seguro.md` e `docs/fontes_externas.md`
  - Fonte oficial: Condições Gerais BB Seguros **V1.6, vigente desde 11/08/2026** (SUSEP 15414.606453/2020-10; a v1.3 foi a primeira fonte e foi reconciliada em `docs/10_reconciliacao_cg.md`), cópia em `dados_externos/condicoes_gerais_bb/`. Pontos-chave: Primeiro Risco Absoluto (15.1); conteúdo primeiro e Segundo Risco só na estrutura em condomínio e financiamento habitacional (15.2.1); imóveis em reforma/construção excluídos (7.1 w/x); desocupação acima de 30 dias exclui qualquer evento, salvo veraneio declarado (7.1 y, novo na V1.6); declaração inexata perde direito (11, alínea a); aluguel até 6 meses, mensal ≤ LMI/6; despesas emergenciais 10% 48h + 3%/dia; roubo e aluguel não cobrem imóvel desocupado; celulares/joias/bens de terceiros não cobertos (6.1).
  - CUB R8-N por UF (ago–set/2026, `dados_externos/cub_r8n_por_uf.csv`; GO usa DF). Fatores tipo/padrão Sinduscon-MG abr/2025 (casa R-1 = 1,21× R8-N).
  - Plano por pontuação (Prático: bens, eletrônicos, vidraçaria, casa; Total: inquilino 2, locador 2, pet 1, dependentes 1). Teste: Total 50%, Prático 40%, Essencial 10%. Estabilidade: limiares ±20% mudam ≤3,6% dos planos.
  - Faixas: incertezas combinadas por raiz da soma dos quadrados em log (máx/mín ~2×). Percentuais de perda por evento são premissas (constantes no topo da seção de faixas em `regras.py`).
  - Semáforo/canal: vermelho = condicionado, vínculo ou obra a confirmar → gerente; verde = confiança alta (+ app → One Click Buy).
  - Dado de contexto: danos elétricos = 53,3% dos sinistros da carteira residencial BB (Monitor Mercantil, 21/07/2026).
- [x] Melhorias pós-etapa 02 (28/10)
  - **Análise de impacto** (`perguntas.py`): simula respostas de vínculo (locador→quitado), tipo, ocupação (2ª residência desocupada = sem roubo, CG Roubo 2.1 c), bens (mín/máx), área e padrão. Pergunta só o que muda plano, elegibilidade ou estreita a faixa de incêndio ≥ 25%; + declaração única no fim.
  - **Confiança geral = estabilidade do plano**: alta = nenhuma resposta muda o plano; média = 1 campo; baixa = 2+ campos, obra a confirmar ou não elegível. Dev: alta 69%, média 22%, baixa 9% (antes 37/52/11).
  - **Validação** (`validacao.py`, CV 5 dobras): escondendo área e padrão de 1.016 imóveis, a faixa contém o centro da faixa recalculada em 97,1% (número otimista: **citar ~89% a 90%**, medido contra o custo de reconstrução verdadeiro em `docs/12_avaliacao_modelo.md` E3; ajuste de 28/10 que alargou vidros e removeu faixas de mín = máx).
  - Recomendação montada em `recomendacao.py` (evita import circular regras↔perguntas). `saidas/validacao_faixas.csv`.
  - Textos corrigidos: dono também tem cobertura de aluguel (moradia temporária, CG Perda de Aluguel 1.1.1 b) → "útil, mas não prioritária"; inquilino também (1.1.2 b) — confirma Total. RC cita pet/dependentes reais; singular/plural; água lista área a confirmar; vidros com confiança só pela área.
  - Testado e descartado: padrão por condomínio/m² (pior que chutar NORMAL); locador por aluguel/m² e regularidade (não separa grupos); RC p/ 2 imóveis (RC é ligada ao imóvel, CG RC 1.1).
  - Em aberto (decisão do time): RC familiar cobre vazamento para o vizinho (CG RC 1.1 e) — apartamento poderia pontuar para o Total.
- [x] CSVs da entrega (etapa 03) — `python scripts/03_gerar_entrega.py` → `entrega/template_resultado_times.csv` (138) + `template_coberturas_times.csv` (1.393 = 1.283 fixas + 110 adicionais) + `docs/03_entrega.md`
  - Lógica em `src/casa_gemea/entrega.py` (montar + 14 testes de formato; o script falha se algum teste falhar). Rodar 02 antes não é necessário: o 03 executa o pipeline inteiro.
  - Campos do template são "LIVRE_E_DOCUMENTADA" no dicionário. Convenções: `elegivel` = SIM / PENDENTE_VALIDACAO / NAO; listas separadas por " | "; última pergunta = declaração única.
  - Justificativa: recomendação inicial → Casa Gêmea com selos → por que este → por que não abaixo/acima → o que pode mudar o plano.
  - Decisão (28/10): apartamento NÃO pontua para o Total por RC/vazamento; fica como evolução futura.
- [x] README.md (28/10): ideia, fluxo, resultados, métricas, execução, estrutura, privacidade, fontes, premissas, limitações, descartados, uso de IA. **Falta preencher a tabela da equipe (nomes e papéis).** Atualizar números se as regras mudarem.
- [x] Contrato JSON (28/10) — `src/casa_gemea/motor.py` (`Motor().recomendar({imovel_id, respostas})`), `python scripts/04_contrato_json.py [entrada.json]` → `saidas/contrato/` + `docs/04_contrato_json.md`
  - Sem estado: cada chamada traz todas as respostas. Respostas viram selo `CONFIRMADO` (config). Opções estruturadas em `perguntas.OPCOES`; `NAO_SEI` sempre aceito; área/bens aceitam número.
  - Novas regras: obra estrutural confirmada → INELEGIVEL; declaração negada → condicionado (gerente). Inelegível não recebe perguntas.
  - Regra de parada absoluta: faixa de incêndio ≤ 1,30× (FAIXA_ACEITAVEL) → não pergunta mais só por faixa (antes a regra relativa não parava).
  - Testado: motor sem respostas = CSV entregue (0 divergências em 138); respostas inválidas → erro.
  - Jornada exemplo IMO_CASO_00003_01: Total/baixa/vermelho → (sem obra) → (mora nele) Prático/alta → (160 m² + declaração) confirmada, faixa 505–634 mil.
- [x] ~~Demo Streamlit~~ (28/10; **removida** do repositório no mesmo dia, a pedido da Ludmila: a interface oficial é o web-app `web/` + `api/`) — era `streamlit run demo/app.py` (streamlit 1.40.1 no requirements; tema em `.streamlit/config.toml`)
  - Visual inspirado na página do Seguro Residencial da BB Seguros (barra de atalhos, menu, breadcrumb, hero azul com título amarelo, cards). Cores aproximadas (#465EFF / #FCFC30, não confirmadas em fonte oficial; dict COR no topo). Sem logo oficial; aviso "PROTÓTIPO" e rodapé. Site oficial bloqueia robôs (Incapsula): não contornar.
  - 4 visões do mesmo motor e das mesmas respostas: Cliente (1 pergunta por vez, botões, valor exato p/ área/bens, cards dos planos, faixas, botão contratar só no verde), Gerente (selos, evidência, impacto), SAC (roteiro "Leia:"), Agente (JSON editável).
  - Casos de demonstração: 00003 (locador+reforma → Prático), 00001, 00013, 00016.
  - Testado com streamlit AppTest: 0 exceções nas 4 visões e 40 clientes.
- [ ] Slides, vídeo
- [x] Ajustes de faixas e jornada (28/10, Pedro + Claude): inquilino com benfeitorias de 3% a 10% (antes 0% a 10%, gerava faixas de até 20×); vidros R$ 40 a 60/m² (antes mín = máx em 42 linhas); RC familiar escalonada por pet e dependentes (antes idêntica nas 69 linhas); aluguel do proprietário morador com incertezas combinadas em log; faixa nunca colapsa em mín = máx; "por que não o plano de baixo" do Total mostra em reais o aluguel que o Prático deixaria sem proteção. Contrato JSON ganhou `recomendacao.justificativa_curta` e `jornada` (perguntas evitadas); `recomendacao_*.csv` ganhou `qtd_perguntas_evitadas`. Razão máx/mín máxima caiu de 20× para ~11× (mediana ~2,4×).

## Deploy (decisão de 28/10)
- **Hospedagem: Render, serviço único** (a FastAPI serve a API em `/api` e o PWA compilado `web/dist` em `/`; mesma origem, HTTPS, o app instala no celular). Conta **pessoal** do Pedro, nunca a conta da GPE Prime.
- Pré-requisitos antes de publicar: (1) FastAPI servindo `web/dist`; (2) **modo sem as bases originais** (o motor sobe só com dados gerados em `saidas/` e tabelas de referência em `dados_externos/`; as bases da organização nunca vão para hospedagem pública); (3) `render.yaml` (build: `pip install -r requirements.txt` e `npm --prefix web ci && npm --prefix web run build`; start: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`); (4) teste local do pacote final.
- Plano grátis do Render dorme sem uso: abrir a URL alguns minutos antes da apresentação. Reserva para o dia: túnel local. Publicar só com autorização do Pedro.
