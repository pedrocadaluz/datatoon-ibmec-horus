# Horus: Proteção Inteligente (Seguro Residencial)

> **Casa Gêmea**: recomendação de seguro residencial com poucas perguntas, ancorada nos dados que o banco já tem e em um motor de regras auditável.

**Datathon Proteção Inteligente · BBDW + Ibmec (BB Seguros) · 27 a 29/10/2026 · desafio Seguro Residencial (dados sintéticos)**

## O Problema

A contratação tradicional de seguro residencial exige formulários longos e perguntas técnicas, e gera alto abandono. Além disso, 61% dos imóveis da base de desenvolvimento (67% na de teste) não têm área cadastrada, o que inviabiliza cotações automáticas simples.

## A Ideia

A Casa Gêmea é uma cópia virtual do imóvel montada com os dados que o banco já tem. Com ela, o motor verifica a elegibilidade, recomenda o plano (Essencial, Prático ou Total) e sugere uma faixa de valor para cada cobertura. Cada decisão vem com o grau de confiança e a explicação. Antes de fechar, o motor faz **só as perguntas que mudam o resultado**. Explica também **por que o plano abaixo não basta e por que o de cima seria desnecessário**.

O mesmo motor serve a todos os canais: o cliente no app, o gerente na agência, o atendente do SAC e agentes autônomos. Só muda a interface.

---

## Equipe Horus

Desafio escolhido: **Seguro Residencial**.

- Anna Clara Melo
- Isabella Rodrigues
- Ludmila Guedes
- Milton Rodrigues
- Pedro Arthur Miranda

---

## Entrega

| Arquivo | Conteúdo |
|---|---|
| [`entrega/template_resultado_times.csv`](entrega/template_resultado_times.csv) | 138 imóveis do Teste Comum: elegibilidade, tipo/uso/vínculo sugeridos, plano, coberturas, confiança, justificativa, perguntas e fontes |
| [`entrega/template_coberturas_times.csv`](entrega/template_coberturas_times.csv) | 1.393 coberturas (1.283 fixas dos planos + 110 adicionais aplicáveis): faixa mínima e máxima em reais, confiança, dados usados, regra de cálculo, justificativa, o que confirmar e observação |
| [`docs/`](docs/) | Relatórios de cada etapa, convenções dos campos e fontes externas |

---

## Como funciona

```
 Dados do banco                     Fontes públicas
 (cadastro, transações, bens)       (Condições Gerais BB, CUB)
        │                                   │
        ▼                                   │
 ┌──────────────────┐                       │
 │ 1. CASA GÊMEA    │  tipo, vínculo, uso, área, padrão, parede,
 │                  │  obra, bens — cada um com selo e confiança
 └────────┬─────────┘                       │
          ▼                                 ▼
 ┌──────────────────────────────────────────────────┐
 │ 2. REGRAS DO SEGURO                              │
 │    elegibilidade → plano → faixas de LMI         │
 │    → comparação com os planos vizinhos           │
 └────────┬─────────────────────────────────────────┘
          ▼
 ┌──────────────────────────────────────────────────┐
 │ 3. ANÁLISE DE IMPACTO                            │
 │    simula as respostas de cada campo incerto:    │
 │    muda o plano? estreita a faixa?               │
 │    → perguntas em ordem de impacto + confiança   │
 └────────┬─────────────────────────────────────────┘
          ▼
   App (One Click Buy) · Gerente · SAC · Agentes
```

### 1. Casa Gêmea: o que o banco já sabe
Cada informação recebe um **selo** e uma confiança, para nunca apresentar estimativa como fato:
- **selo:** `OBSERVADO`, `ESTIMADO` ou `A_CONFIRMAR`;
- **confiança:** alta, média ou baixa;
- **evidência:** os sinais usados.

| Campo | Como é obtido |
|---|---|
| Tipo | Complemento do endereço + termos de casa/apartamento + condomínio pago |
| Vínculo | Aluguel pago → inquilino · parcela de financiamento → financiado · crédito compatível com aluguel → locador · nenhum sinal → proprietário sem financiamento. Sinais em conflito baixam a confiança. |
| Uso | Endereço principal + número de imóveis do cliente |
| Área | Cadastro; se faltar (61% dos casos), modelo com IPTU, energia, tipo e município |
| Padrão construtivo | Cadastro; se faltar, indício pelo IPTU por m² (só desloca a faixa, confiança baixa) |
| Obra | Gasto com material de construção e vidraçaria em 24 meses |
| Bens | Mínimo: bens ponderados ou 50% das compras de 36 meses · máximo: bens cadastrados ou compras |

### 2. Regras do seguro
Base oficial: Condições Gerais do Seguro Residencial BB Seguros V1.6 (vigência desde 11/08/2026; ver [`docs/10_reconciliacao_cg.md`](docs/10_reconciliacao_cg.md)), Processo SUSEP 15414.606453/2020-10 ("CG").

- **Elegibilidade em 3 níveis:**

  | Nível | Quando |
  |---|---|
  | `NAO` | Situação irregular, parede combustível ou obra estrutural confirmada pelo cliente (CG 7.1 w/x) |
  | `PENDENTE_VALIDACAO` | Possível obra relevante (CG 7.1 w/x), tipo de imóvel indefinido ou declaração única não confirmada: plano provisório e gerente |
  | `SIM` | Demais casos, sujeitos à declaração única do cliente |

- **Plano por pontuação.** Nenhum sinal decide sozinho.

  | Pontos para o Prático (roubo e vidros) | Pontos para o Total (aluguel, RC e despesas) |
  |---|---|
  | Bens de valor | Paga aluguel |
  | Eletrônicos | Recebe aluguel |
  | Gasto com vidraçaria | Pet |
  | Ser casa | Dependentes |

- **Faixas de LMI** (Limite Máximo de Indenização, o teto que a seguradora paga). O seguro é a Primeiro Risco Absoluto (CG 15.1), então a faixa é o LMI que cobre a perda plausível do evento:

  | Cobertura | Fórmula |
  |---|---|
  | Incêndio | Prédio (área × CUB da UF × fator de tipo e padrão × interesse segurável) + bens |
  | Água, vendaval, impacto, aeronave, elétricos, roubo, vidros | Percentuais documentados como premissas |
  | Aluguel | 3 a 6 meses (CG: até 6) |
  | Despesas emergenciais | Pela regra de 3% do LMI ao dia (CG) |

  As incertezas são combinadas pela raiz da soma dos quadrados: quanto menos se sabe, mais larga a faixa.
- **Comparação por lacuna de cobertura, nunca por preço** (a base não tem preços). Exemplo: "O Essencial não cobre roubo nem quebra de vidros, que protegem os bens citados".

### 3. Perguntas que mudam o resultado
Para cada campo incerto, o motor **simula as respostas plausíveis e refaz a recomendação**:

| Campo | Simulação |
|---|---|
| Vínculo | E se o crédito não for aluguel? |
| Tipo | E se for casa em vez de apartamento? |
| Ocupação | E se a segunda residência ficar vazia? Imóvel desocupado não tem cobertura de roubo (CG, Roubo 2.1 c). |
| Bens | No mínimo e no máximo da faixa |
| Área e padrão | Confirmados |

- **Regra de parada:** pergunta-se só o que define a elegibilidade, muda o plano ou estreita a faixa de incêndio em pelo menos 25%. Quando a faixa já está estreita (máximo até 30% acima do mínimo), as perguntas só de faixa param.
- **Ordem:** elegibilidade → plano → faixa.
- **Declaração única no fim:** cobre as restrições do guia (9.1) que a base não permite verificar: área urbana, fora de comunidade carente, sem vínculo com atividade rural, paredes de alvenaria, sem construção, reconstrução ou obra estrutural, não tombado, desapropriado nem condenado, e sem outro seguro residencial BB no mesmo endereço. Substitui várias perguntas de elegibilidade. Se o cliente não confirmar, o caso vai ao gerente.
- **Formato:** perguntas fechadas, com opções personalizadas a partir dos dados. Exemplo: "A área fica entre 130 e 221 m²? Sim / Menor / Maior / Não sei". "Não sei" é sempre válido: a faixa fica mais larga, mas a cotação não trava.

A **confiança geral** mede a chance de o plano mudar depois das perguntas:

| Confiança | Significado |
|---|---|
| Alta | Nenhuma resposta plausível muda o plano |
| Média | Um campo pode mudar o plano |
| Baixa | Dois ou mais campos podem mudar, ou a elegibilidade está pendente |

Campo incerto que não muda nada não baixa a confiança.

### 4. Contrato JSON: as perguntas funcionando
O motor recebe `{ imovel_id, respostas }` e devolve a recomendação atualizada:
- Casa Gêmea com as respostas marcadas com o selo `CONFIRMADO`;
- elegibilidade, plano, faixas e confiança recalculados;
- próximas perguntas com opções (código + rótulo);
- semáforo e status.

O motor não guarda estado: cada chamada traz todas as respostas, o que facilita a auditoria. Detalhes e exemplos em [`docs/04_contrato_json.md`](docs/04_contrato_json.md).

Jornada de exemplo (`IMO_CASO_00003_01`, possível locador com sinal de reforma):

| Passo | Resposta | Plano | Confiança | Faixa de incêndio (R$) | Semáforo |
|---|---|---|---|---|---|
| 0 | — | Total | Baixa | 431 mil – 762 mil | 🔴 gerente |
| 1 | sem obra | Total | Média | 431 mil – 762 mil | 🟡 |
| 2 | "não, eu moro nele" | **Prático** | Alta | 447 mil – 793 mil | 🟢 |
| 3 | área 160 m² + declaração | Prático | Alta | **505 mil – 634 mil** | 🟢 confirmada |

A mesma saída serve a todos os canais:
- o **app** mostra as opções como botões;
- o **gerente** vê também o motivo e o impacto de cada pergunta;
- o **SAC** lê pergunta e opções;
- um **agente autônomo** chama o motor em laço até o status deixar de ser `RECOMENDACAO_INICIAL`.

### Canais (semáforo)

| Semáforo | Quando | Canal |
|---|---|---|
| 🟢 Verde | Confiança alta | One Click Buy (usuário de app) ou atendimento assistido |
| 🟡 Amarelo | Um campo pode mudar o plano | App com 1 a 3 confirmações ou atendimento assistido |
| 🔴 Vermelho | Elegibilidade pendente, vínculo ou obra a confirmar | Gerente |

O semáforo é uma **sugestão de canal** para a BB Seguros. A organização definiu que canal, linguagem, CTA e momento da oferta ficam com a BB; o motor só indica onde a recomendação pode seguir sem fricção.

### 5. Personalização: o mesmo plano, explicado para cada cliente
Módulo `personalizacao.py`. Não muda o plano nem as faixas; muda o que se destaca e como se fala.

| Peça | O que faz | Sinais usados |
|---|---|---|
| Perfil (arquétipo) | 9 perfis, como "Inquilino com família", "Casa conectada", "Casa de temporada" | Vínculo, uso, obra, eletrônicos, bens, dependentes e pet |
| Necessidade por cobertura | Índice de 0 a 100 que ordena a conversa (não é probabilidade de sinistro) | Frequência de sinistros da carteira BB + sinais do imóvel (eletrônicos, consumo de água e energia, bens) |
| Coberturas adicionais | Até 3 por imóvel, das Condições Gerais (item 4.1): equipamentos portáteis, indenização a valor de novo, desocupação temporária, bicicleta, atividade MEI | Compras de 36 meses, bens cadastrados, uso do imóvel |
| Assistências em destaque | Quais assistências do plano mais servem a este cliente (não entram no template, conforme o guia) | Eletrônicos, dependentes, pet, tipo do imóvel |
| Tom da jornada | Express, guiada ou com especialista | Só maturidade digital (canal) |

**Adicionais no template de coberturas.** Entram só os que têm faixa em reais: `EQUIPAMENTOS_PORTATEIS` (25% a 60% dos eletrônicos, confiança média) e `BICICLETA` (30% a 60% dos itens de lazer, confiança **baixa**, porque "item de lazer" não é necessariamente bicicleta). Valor de novo, desocupação e MEI não têm limite próprio e ficam só na explicação do motor. No contrato JSON, os adicionais vêm no campo `coberturas_adicionais`.

**Três perfis contrastantes** ([`docs/11_personas.md`](docs/11_personas.md), gerado por `scripts/10_personas.py`):

| Persona (fictícia) | Imóvel | Plano | Por quê |
|---|---|---|---|
| Marina, inquilina de apartamento com 3 dependentes e pet | `IMO_CASO_00008_01` | Total | Paga aluguel e tem família: aluguel e RC familiar |
| Rafael, casa financiada com muitos eletrônicos | `IMO_CASO_00016_01` | Prático | Bens e casa: roubo e vidros; sem aluguel para proteger |
| Helena, apartamento de temporada que fica vazio | `IMO_CASO_00059_01` | Essencial (começa no Prático) | Imóvel desocupado não tem cobertura de roubo (CG, Roubo 2.1 c): o motor **desce** o plano |

---

## Resultados (base Teste Comum, 138 imóveis)

| Indicador | Resultado |
|---|---|
| Imóveis processados | 138 de 138 (100%) |
| Coberturas com faixa em reais | 1.393 de 1.393 (100%), nenhuma sem estimativa: 1.283 fixas + 110 adicionais (86 equipamentos portáteis, 24 bicicleta) |
| Recomendações com justificativa e comparação | 138 de 138 |
| Elegibilidade | 135 `SIM` · 3 `PENDENTE_VALIDACAO` (possível obra) · 0 `NAO` |
| Plano | Total 50,0% · Prático 39,9% · Essencial 10,1% |
| Confiança geral | Alta 74,6% · Média 16,7% · Baixa 8,7% |
| Perguntas por imóvel (além da declaração) | 0: 31,9% · 1: 57,2% · 2: 8,7% · 3: 2,2% (média 0,81) |
| Perguntas evitadas | 7,2 de 8 campos de um formulário tradicional, em média |
| Canal | One Click Buy 63,8% · Gerente 16,7% · Atendimento assistido 10,9% · App com confirmação 8,7% |
| Testes de formato da entrega | 15 de 15 aprovados ([`docs/03_entrega.md`](docs/03_entrega.md)) |
| Testes da API | 10 de 10, incluindo paridade dos 138 casos com os CSVs |
| Tempo de execução | ~3 s para os 2.716 imóveis das duas bases |

**Por que metade vai ao Total.** Dos 69 casos Total, 52 (75%) são inquilinos (31) ou locadores (21). As CG (Perda de Aluguel 1.1) cobrem exatamente o que eles pagam ou recebem: o inquilino recebe o reembolso do aluguel de uma moradia temporária, e o locador, o aluguel que deixa de receber. Os outros 17 têm pet **e** dependentes, que pedem RC familiar, além de algum sinal do Prático. O plano mais completo não é o padrão: 69 imóveis ficam no Prático ou no Essencial.

### Métricas de qualidade (base de desenvolvimento)

| Métrica | Resultado | Como foi medido |
|---|---|---|
| **Faixa de reconstrução contém o custo real** | **cerca de 89%** (faixa calibrada em ~90%) | Área e padrão reais escondidos (273 imóveis), custo verdadeiro = área real × CUB × fator do padrão real; ver `docs/12_avaliacao_modelo.md` (E3). O teste de `validacao.py` (97%) compara com o centro da própria faixa e é otimista |
| Erro do centro da faixa | 6% a 13% (mediana por cobertura) | Mesmo teste |
| Modelo de área | Erro mediano 13,4% · R² 0,86 (log) · intervalo de 80% contém o real em 79,9% | Validação cruzada de 5 dobras por cliente. **Teste cego** (treino só no desenvolvimento, n = 46 imóveis do teste com área real): erro mediano 16,2% (IC 95%: 12,8% a 21,8%), cobertura 78%; sem overfitting nem vazamento (`docs/13_diagnostico_ajuste.md`) |
| Estabilidade do plano | Limiares de bens ±20% mudam 3,6% / 1,4% dos planos | [`docs/02_regras_seguro.md`](docs/02_regras_seguro.md) |
| Consistência entre casos semelhantes | 91,2% dos grupos (desenvolvimento) e 93,8% (teste) recebem o mesmo plano; os grupos restantes são todos explicados por eletrônicos, vidraçaria ou desocupação | Imóveis agrupados por tipo, vínculo, nível de bens, pet e dependentes; [`docs/14_consistencia.md`](docs/14_consistencia.md) |
| Confiança geral | Alta 69% · Média 22% · Baixa 9% | Antes da análise de impacto: alta 37% |
| Valor das perguntas escolhidas | Com 1 pergunta, o plano fica igual ao plano com tudo confirmado em **98,2%** dos casos (93,8% com uma pergunta aleatória; 92,0% sem perguntar) | 600 imóveis com área e padrão escondidos; [`docs/12_avaliacao_modelo.md`](docs/12_avaliacao_modelo.md) (E4) |
| Sensibilidade do plano às premissas | Limiares de bens, vidros, eletrônicos e vínculo: robusto. Pesos de pet e dependentes (±1): mudam de 12% a 40% dos planos | `docs/12_avaliacao_modelo.md` (E5); ver Premissas |
| Idade e renda não vazam para o plano | Embaralhar ou zerar idade e renda: 0 divergências nos 2.578 imóveis e nas coberturas; a idade não é prevista pelo motor (AUC 0,48 a 0,50) | Teste contrafactual e de proxy; [`docs/06_auditoria_proxy.md`](docs/06_auditoria_proxy.md) |

### Métricas sugeridas pelo guia (seção 8)

| Métrica do guia | Resultado |
|---|---|
| Percentual de casos processados | 100% (138 de 138) |
| Recomendações com justificativa | 100% |
| Cumprimento das regras de elegibilidade | 100%: elegibilidade avaliada antes do plano em todos os casos; inelegível nunca recebe plano nem adicional (teste automático) |
| Completude dos templates e das coberturas fixas | 100%: todas as fixas do plano em cada imóvel (teste automático) |
| Quantidade média de perguntas de confirmação | 0,81 por imóvel, mais a declaração única |
| Percentual de casos com confiança baixa | 8,7% |
| Estabilidade das recomendações | Limiares ±20% mudam até 3,6% dos planos |
| Consistência entre casos semelhantes | 93,8% dos grupos no teste (91,2% no desenvolvimento) |
| Sensibilidade das faixas | Responder a área estreita a faixa de incêndio de 1,77× para 1,25× (jornada `IMO_CASO_00003_01`) |
| Tempo de execução e taxa de falhas | ~4,5 s para os 4 scripts e os 2.716 imóveis; 0 falhas |
| Reprodutibilidade | Rodar de novo gera arquivos idênticos (conferido com `git diff`) |
| Consistência plano × coberturas | 100%: `coberturas_recomendadas` = linhas do template de coberturas (teste automático) |

---

## Como executar

Requisitos: **Python 3.12.2** (arquivo `.python-version`) e as dependências de `requirements.txt` (pandas, numpy, FastAPI e Uvicorn; streamlit só para a demo legada). O web-app pede também **Node 24 e npm 11**.

### 1. Bases de dados
Descompacte as bases recebidas da organização na raiz do projeto, com estes nomes de pasta:

```
Seguro_Residencial_Desenvolvimento/   (2.200 clientes, 2.578 imóveis)
Seguro_Residencial_Teste_Comum/       (120 clientes, 138 imóveis)
```

As pastas são ignoradas pelo Git e os arquivos originais só são lidos. Para a API, outro local pode ser indicado na variável `CASA_GEMEA_DADOS` (a pasta que contém as duas bases).

### 2. Motor e entrega

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python scripts/01_construir_casa_gemea.py   # Casa Gêmea das duas bases      → saidas/casa_gemea_*.csv, docs/01
python scripts/02_aplicar_regras.py         # regras, faixas e validação      → saidas/recomendacao_*, coberturas_*, docs/02
python scripts/03_gerar_entrega.py          # templates oficiais + 15 testes → entrega/, docs/03
python scripts/04_contrato_json.py          # jornada de exemplo do contrato  → saidas/contrato/, docs/04
python scripts/04_contrato_json.py entrada.json   # responde uma chamada do contrato JSON
python scripts/10_personas.py               # três personas contrastantes     → saidas/personas/, docs/11
python scripts/11_consistencia.py           # consistência entre casos        → saidas/consistencia_grupos.csv, docs/14
```

Scripts de análise (não são necessários para a entrega): `06_auditoria_proxy.py`, `07_analise_colunas.py`, `08_avaliar_modelo.py`, `09_diagnostico_ajuste.py`.

### 3. Web-app (interface oficial)
Windows, num comando (API + web, com QR code para o celular):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/05_rodar_web.ps1
```

Mac ou Linux, em dois terminais na raiz do projeto, com o ambiente do passo 2 ativo:

```bash
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000   # terminal 1: API
npm --prefix web start                                         # terminal 2: web em http://localhost:5173
```

Detalhes (celular, HTTPS, testes de navegador) em [`web/README.md`](web/README.md).

### 4. Testes

```bash
pip install -r api/requirements-test.txt
python -m unittest api.test_api      # API: 10 testes, inclui paridade dos 138 casos com os CSVs
npm --prefix web run build           # build TypeScript/Vite
npm --prefix web test                # jornadas e acessibilidade no navegador (Chrome instalado)
```

- O script 03 roda o pipeline inteiro sozinho e **falha com erro** se algum teste de formato não passar.
- Tudo é determinístico: rodar de novo gera os mesmos arquivos.
- O que é calibrado (modelo de área, IPTU e aluguel por m²) usa **só a base de desenvolvimento** e é reaplicado sem ajustes na base de teste.

---

## Estrutura do projeto

```
├── README.md · CLAUDE.md          visão geral e contexto de trabalho
├── requirements.txt · .python-version
├── src/casa_gemea/                motor (pacote Python, uma responsabilidade por módulo)
│   ├── config.py                  caminhos, selos, limiares, campos sensíveis
│   ├── carregar.py                leitura e junção das tabelas
│   ├── area.py · calibracao.py    modelo de área e parâmetros por cidade
│   ├── inferencias.py             Casa Gêmea: cada campo com selo, confiança e evidência
│   ├── regras.py                  elegibilidade, plano, faixas, comparação, canal
│   ├── perguntas.py               análise de impacto, perguntas e confiança geral
│   ├── recomendacao.py · pipeline.py   junta regras e perguntas por imóvel
│   ├── validacao.py               teste das faixas escondendo dados reais
│   ├── personalizacao.py          perfil, necessidade por cobertura, adicionais, assistências, tom
│   ├── entrega.py                 monta e valida os templates oficiais
│   └── motor.py                   contrato JSON: respostas → recomendação atualizada
├── api/                           FastAPI fina sobre o motor (sem regras próprias)
├── web/                           web-app (React + TypeScript, PWA): web e celular
├── scripts/                       etapas executáveis, em ordem (01 a 04 pipeline; 05 rodar o web-app; 06 a 09 auditoria e avaliação; 10 personas; 11 consistência)
├── entrega/                       os 2 CSVs da entrega (templates oficiais preenchidos)
├── saidas/                        arquivos gerados (Casa Gêmea, recomendação, validação, auditoria, contrato)
├── docs/                          relatórios por etapa (índice em docs/README.md)
├── dados_externos/                CUB por UF, fatores Sinduscon, Condições Gerais BB (V1.6 vigente, v1.3 e v2.3 para comparação)
└── demo/ · .streamlit/            demo Streamlit anterior (legado; a interface oficial é `web/`)
```

As bases originais da organização (`Seguro_Residencial_*`) ficam na raiz, ignoradas pelo Git. Os materiais recebidos (guia, apresentações e bases compactadas) ficam na pasta `doc/`, também ignorada.

---

## Privacidade e uso dos dados

| Uso | Campos |
|---|---|
| **Definem risco, plano e valores** | Endereço e termos, área, padrão, parede, situação cadastral, aluguel pago/recebido, financiamento, condomínio, IPTU, energia, compras, gastos com obra e vidraçaria, bens vinculados |
| **Só indicam necessidade, nunca risco** | Dependentes e pet (necessidade de RC familiar e despesas emergenciais); consumo de água e energia (só ordenam a conversa na personalização) |
| **Só escolhem o canal e o tom** | Usuário de app, frequência de acesso, maturidade digital; seguro residencial já existente e produtos de seguridade (modo "revisão de seguro") |
| **Nunca usados** | Idade, renda, origem e confiança da renda |

- Os campos proibidos estão listados em `config.CAMPOS_PROIBIDOS`. O teste de entrega confere que nenhum texto cita idade ou renda do cliente.
- **Minimização (LGPD, art. 6º, III):** o motor só pergunta o que muda o resultado. Cerca de um terço dos imóveis (31,9%) não precisa de nenhuma pergunta além da declaração única.
- A recomendação é sempre **inicial e transparente**: a justificativa mostra o que é dado do banco e o que é estimativa, e o cliente pode corrigir qualquer campo.

---

## Fontes externas

Detalhes (fonte, data, licença, método e limitações) em [`docs/fontes_externas.md`](docs/fontes_externas.md).

| Fonte | Uso |
|---|---|
| Condições Gerais do Seguro Residencial BB Seguros V1.6 (SUSEP 15414.606453/2020-10) | Coberturas, exclusões, limites, Primeiro Risco Absoluto |
| CUB R8-N por UF (Sinduscons, ago–set/2026) | Custo de reconstrução por m² |
| Tabela CUB Sinduscon-MG (abr/2025) | Fatores de tipo (casa × apartamento) e padrão |
| Monitor Mercantil (21/07/2026) | Distribuição de sinistros da carteira BB, só como contexto |

---

## Premissas

- **Pesos do plano (pet, dependentes e a regra "um ponto de Total junto com um de Prático vira Total")** são premissas de negócio, sem rótulo para calibrar. O plano é sensível a eles: variar cada peso em ±1 muda de 12% a 40% dos imóveis (`docs/12_avaliacao_modelo.md`, E5). Já é robusto a conteúdo, vidros, eletrônicos e vínculo.

- **Percentuais de perda por evento** são premissas da equipe, porque não há dado de sinistro por imóvel. Ficam no topo da seção de faixas em `regras.py`:

  | Evento | Premissa |
  |---|---|
  | Água | 10% do prédio + 30% dos bens |
  | Vendaval | 20% do prédio (casa) ou 3% (apartamento) + 10% dos bens |
  | Elétricos | 50% dos eletrônicos |
  | Roubo | 50% dos bens |
  | Vidros | R$ 50/m² |

- **Interesse segurável** (quanto do prédio é do cliente):

  | Situação | Prédio |
  |---|---|
  | Apartamento | 10% a 30% (estrutura no seguro do condomínio, CG 5.3 e 15.2.1) |
  | Casa financiada | 50% a 100% |
  | Inquilino | Só benfeitorias |

  Bens de terceiros não são cobertos (CG 6.1), por isso o locador segura só 20% do conteúdo.
- **Locador:** só tem confiança média quando o imóvel não é o endereço principal do cliente. Senão, os sinais estão em conflito e o vínculo vira pergunta.
- **Proprietário sem financiamento:** inferido pela ausência de sinais. Pode incluir imóvel cedido ou de familiar.
- **Faixas dos adicionais:** equipamentos portáteis de 25% a 60% dos eletrônicos; bicicleta de 30% a 60% dos itens de lazer. Os itens precisam ser listados na contratação.

## Decisões sobre divergências entre o guia e a base

| Ponto | O que diverge | Decisão |
|---|---|---|
| Instalações e Pequenos Reparos | O guia (9.2) lista como cobertura fixa dos 3 planos; o catálogo da base (`catalogo_coberturas_fixas_planos`) não tem essa linha | Seguimos o catálogo (6 / 8 / 11 coberturas), que define os nomes aceitos no template. Nas CG V1.6 ela aparece no item 4.1 j |
| Queda de aeronave e impacto de veículos | O guia trata como uma cobertura; o catálogo separa em duas | Duas linhas, como no catálogo |
| Assistências | Acompanham o plano | Não entram no template de coberturas (guia, 5.2); o motor só indica quais se destacam para o cliente |
| Coberturas adicionais | O dicionário pede "uma linha por cobertura fixa e adicional aplicável" | Entram só os adicionais com faixa em reais (seção 5) |
| Restrições de aceitação sem sinal na base | Rural, comunidade carente, tombado, desapropriado, condenado e endereço já segurado na BB não têm campo | Cobertos pela declaração única; se o cliente não confirmar, o caso vai ao gerente |
| Canal e momento da oferta | A apresentação da BB diz que canal, linguagem e CTA ficam com a BB | O semáforo é sugestão, não decisão |

## Limitações

- Tipo, vínculo e uso são **sugestões** a partir de sinais indiretos e não substituem a declaração do cliente.
- O **padrão construtivo** falta em 73% dos casos. O indício pelo IPTU acerta os extremos, mas não classifica, por isso entra com confiança baixa.
- O **modelo de área** vale para os 10 municípios da base; outra cidade exige recalibrar.
- **Não há dado** para identificar imóvel rural, tombado, em comunidade carente, já segurado na BB, sobrado ou uso MEI. As restrições de aceitação são cobertas pela declaração única; MEI é oferecido como adicional, a confirmar.
- O **CUB** vem de agregador secundário que cita os Sinduscons e não inclui fundações nem áreas externas. Os fatores de padrão são de Minas Gerais e foram aplicados a todas as UFs.
- **Não há preço** na base: a comparação é por lacuna de cobertura. Os limites em reais de cada plano real não estão nas CG.
- **Confiança geral sem gabarito:** ela não pode ser validada, porque a base não traz o plano "certo". A validação cobre as faixas (área e padrão).

## Testado e descartado

| Ideia | Resultado | Decisão |
|---|---|---|
| Padrão pelo condomínio por m² | Acerto de 48% a 54%, contra 58% de chutar "normal" | Descartado |
| Locador mais preciso (aluguel × aluguel por m² da cidade; regularidade) | Não separa locadores com e sem conflito | Descartado; o vínculo vira pergunta |
| Confiança por contagem de campos a confirmar | Penalizava campos que não mudam nada | Substituída pela análise de impacto |
| Condomínio, renda e padrão no modelo de área | Correlação ~0 com a área | Fora do modelo (a renda também é proibida) |

## Evoluções possíveis

- **RC familiar para apartamentos:** a RC também cobre vazamento para o vizinho (CG, RC Familiar 1.1 e). Pode virar ponto para o Total; ficou fora para não mudar regras validadas na véspera.
- **Dados de risco por região** (alagamento, vendaval, furto). A base tem coordenadas perturbadas e CEP fictício, então ficou fora.
- **Calibrar os percentuais de perda** com dados reais de sinistro da seguradora.

---

## Uso de IA

O desenvolvimento usou o **Claude (Anthropic)**, via Claude Code, como assistente para:
- explorar os dados e sugerir hipóteses;
- escrever e revisar o código Python;
- construir o web-app (React e TypeScript), a API FastAPI e os testes de navegador;
- pesquisar e ler as Condições Gerais da BB Seguros e as tabelas CUB;
- redigir os relatórios e este README.

As decisões de produto foram da equipe: a ideia da Casa Gêmea, a comparação por lacuna, as perguntas fechadas, a elegibilidade em 3 níveis e os guardrails de privacidade.

**O motor não usa IA nem modelos de linguagem em execução.** Todas as decisões (elegibilidade, plano, faixas, perguntas e confiança) são regras determinísticas e auditáveis em `src/casa_gemea/`. Os textos de justificativa são montados por regra a partir dos dados de cada imóvel. A equipe revisou o código e os resultados e é capaz de explicar e defender cada regra.
