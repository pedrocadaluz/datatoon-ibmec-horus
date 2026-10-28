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

| Nome | Papel |
|---|---|
| Ludmila Guedes | Ideia da Casa Gêmea e motor de regras |
| Milton Rodrigues | _a preencher_ |
| Anna Clara Melo | _a preencher_ |
| Isabella Rodrigues | _a preencher_ |
| Pedro Arthur Miranda | _a preencher_ |

---

## Entrega

| Arquivo | Conteúdo |
|---|---|
| [`entrega/template_resultado_times.csv`](entrega/template_resultado_times.csv) | 138 imóveis do Teste Comum: elegibilidade, tipo/uso/vínculo sugeridos, plano, coberturas, confiança, justificativa, perguntas e fontes |
| [`entrega/template_coberturas_times.csv`](entrega/template_coberturas_times.csv) | 1.393 coberturas (1.283 fixas dos planos + 110 adicionais opcionais): faixa mínima e máxima em reais, confiança, dados usados, regra de cálculo, justificativa, o que confirmar e observação |
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
  | `NAO` | Situação irregular ou parede combustível |
  | `PENDENTE_VALIDACAO` | Possível obra relevante (CG 7.1 w/x) |
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
- **Declaração única no fim:** "imóvel urbano, de alvenaria, sem obra estrutural e não tombado". Substitui várias perguntas de elegibilidade.
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

---

## Resultados (base Teste Comum, 138 imóveis)

| Indicador | Resultado |
|---|---|
| Imóveis processados | 138 de 138 (100%) |
| Coberturas com faixa em reais | 1.393 de 1.393 (100%): 1.283 fixas dos planos + 110 adicionais opcionais (Equipamentos Portáteis 86, Bicicleta 24), nenhuma sem estimativa |
| Recomendações com justificativa e comparação | 138 de 138 |
| Elegibilidade | 135 `SIM` · 3 `PENDENTE_VALIDACAO` (possível obra) · 0 `NAO` |
| Plano | Total 50,0% · Prático 39,9% · Essencial 10,1% |
| Confiança geral | Alta 74,6% · Média 16,7% · Baixa 8,7% |
| Perguntas por imóvel (além da declaração) | 0: 34,1% · 1: 55,1% · 2: 8,7% · 3: 2,2% |
| Canal | One Click Buy 63,8% · Gerente 16,7% · Atendimento assistido 10,9% · App com confirmação 8,7% |
| Testes de formato da entrega | 14 de 14 aprovados ([`docs/03_entrega.md`](docs/03_entrega.md)) |
| Tempo de execução | ~3 s para os 2.716 imóveis das duas bases |

Inquilinos e locadores vão ao Total porque as CG (Perda de Aluguel 1.1) cobrem exatamente o que eles pagam ou recebem. O inquilino recebe o reembolso do aluguel de uma moradia temporária. O locador recebe o aluguel que deixa de receber.

### Métricas de qualidade (base de desenvolvimento)

| Métrica | Resultado | Como foi medido |
|---|---|---|
| **Faixa de reconstrução contém o custo real** | **cerca de 89%** (faixa calibrada em ~90%) | Área e padrão reais escondidos (273 imóveis), custo verdadeiro = área real × CUB × fator do padrão real; ver `docs/12_avaliacao_modelo.md` (E3). O teste de `validacao.py` (97%) compara com o centro da própria faixa e é otimista |
| Erro do centro da faixa | 6% a 13% (mediana por cobertura) | Mesmo teste |
| Modelo de área | Erro mediano 13,4% · R² 0,86 (log) · intervalo de 80% contém o real em 79,9% | Validação cruzada de 5 dobras por cliente. **Teste cego** (treino só no desenvolvimento, n = 46 imóveis do teste com área real): erro mediano 16,2% (IC 95%: 12,8% a 21,8%), cobertura 78%; sem overfitting nem vazamento (`docs/13_diagnostico_ajuste.md`) |
| Estabilidade do plano | Limiares de bens ±20% mudam 3,6% / 1,4% dos planos | [`docs/02_regras_seguro.md`](docs/02_regras_seguro.md) |
| Confiança geral | Alta 69% · Média 22% · Baixa 9% | Antes da análise de impacto: alta 37% |

---

## Como executar

Requisitos: **Python 3.12.2** (arquivo `.python-version`) e as dependências de `requirements.txt` (pandas e numpy; fastapi e uvicorn para a API do web-app).

```bash
pip install -r requirements.txt

python scripts/01_construir_casa_gemea.py   # Casa Gêmea das duas bases      → saidas/casa_gemea_*.csv, docs/01
python scripts/02_aplicar_regras.py         # regras, faixas e validação      → saidas/recomendacao_*, coberturas_*, docs/02
python scripts/03_gerar_entrega.py          # templates oficiais + 14 testes → entrega/, docs/03
python scripts/04_contrato_json.py          # jornada de exemplo do contrato  → saidas/contrato/, docs/04
python scripts/04_contrato_json.py entrada.json   # responde uma chamada do contrato JSON
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
│   ├── entrega.py                 monta e valida os templates oficiais
│   └── motor.py                   contrato JSON: respostas → recomendação atualizada
├── api/                           FastAPI fina sobre o motor (sem regras próprias)
├── web/                           web-app (React + TypeScript, PWA): web e celular
├── scripts/                       etapas executáveis, em ordem (01 a 04 pipeline; 05 rodar o web-app; 06 auditoria de proxy; 07 análise de colunas)
├── entrega/                       os 2 CSVs da entrega (templates oficiais preenchidos)
├── saidas/                        arquivos gerados (Casa Gêmea, recomendação, validação, auditoria, contrato)
├── docs/                          relatórios por etapa (índice em docs/README.md)
└── dados_externos/                CUB por UF, fatores Sinduscon, Condições Gerais BB (V1.6 vigente, v1.3 e v2.3 para comparação)
```

As bases originais da organização (`Seguro_Residencial_*`) ficam na raiz, ignoradas pelo Git.

---

## Privacidade e uso dos dados

| Uso | Campos |
|---|---|
| **Definem risco, plano e valores** | Endereço e termos, área, padrão, parede, situação cadastral, aluguel pago/recebido, financiamento, condomínio, IPTU, energia, compras, gastos com obra e vidraçaria, bens vinculados |
| **Só indicam necessidade, nunca risco** | Dependentes e pet (necessidade de RC familiar e despesas emergenciais) |
| **Só escolhem o canal** | Usuário de app, frequência de acesso, maturidade digital |
| **Nunca usados** | Idade, renda, origem e confiança da renda |

- Os campos proibidos estão listados em `config.CAMPOS_PROIBIDOS`. O teste de entrega confere que nenhum texto cita idade ou renda do cliente.
- **Minimização (LGPD, art. 6º, III):** o motor só pergunta o que muda o resultado. Cerca de um terço dos imóveis (34,1%) não precisa de nenhuma pergunta além da declaração única.
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

## Limitações

- Tipo, vínculo e uso são **sugestões** a partir de sinais indiretos e não substituem a declaração do cliente.
- O **padrão construtivo** falta em 73% dos casos. O indício pelo IPTU acerta os extremos, mas não classifica, por isso entra com confiança baixa.
- O **modelo de área** vale para os 10 municípios da base; outra cidade exige recalibrar.
- **Não há dado** para identificar imóvel rural, tombado, sobrado ou uso MEI; esses pontos são cobertos pela declaração única.
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
- pesquisar e ler as Condições Gerais da BB Seguros e as tabelas CUB;
- redigir os relatórios e este README.

As decisões de produto foram da equipe: a ideia da Casa Gêmea, a comparação por lacuna, as perguntas fechadas, a elegibilidade em 3 níveis e os guardrails de privacidade.

**O motor não usa IA nem modelos de linguagem em execução.** Todas as decisões (elegibilidade, plano, faixas, perguntas e confiança) são regras determinísticas e auditáveis em `src/casa_gemea/`. Os textos de justificativa são montados por regra a partir dos dados de cada imóvel. A equipe revisou o código e os resultados e é capaz de explicar e defender cada regra.
