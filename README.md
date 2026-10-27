# Horus: Proteção Inteligente (Seguro Residencial)

> **Casa Gêmea**: recomendação de seguro residencial com poucas perguntas, ancorada nos dados que o banco já tem e em um motor de regras auditável.

Projeto desenvolvido para o **Datathon Proteção Inteligente** (BBDW + Ibmec, BB Seguros), de 27 a 29/10/2026, com foco no desafio de Seguro Residencial (dados sintéticos). Entrega final: 29/10/2026 às 10h.

---

## O Problema

A contratação tradicional de seguro residencial exige formulários longos, perguntas técnicas e gera alto abandono. Além disso, 61% dos imóveis da base de desenvolvimento (67% na de teste) não têm área cadastrada, inviabilizando cotações automáticas simples.

## A Ideia: Casa Gêmea

A **Casa Gêmea** é a cópia virtual do imóvel montada com dados que o ecossistema bancário já possui (IPTU, energia, água, aluguel, financiamento, condomínio e compras de bens e materiais). Um motor de REGRAS (determinístico e auditável):
1. Monta o perfil do imóvel com o que já se sabe, marcando o que é dado, estimativa ou a confirmar;
2. Decide qual pergunta fazer e completa a casa a cada resposta;
3. Recomenda o plano ideal e faixas adequadas de cobertura.

Modelos de IA generativa, quando utilizados, atuam exclusivamente na redação de textos e contato amigável, nunca decidindo aceitação ou coberturas.

Fluxo central: **sinais -> sugestão inicial -> confiança -> confirmação -> recomendação**.

---

## Como Funciona

0. **Elegibilidade Prévia**: avaliada antes de qualquer interação em 3 níveis (ELEGÍVEL, ELEGÍVEL CONDICIONADO, INELEGÍVEL).
1. **Montagem da Casa Gêmea**: cada dado recebe um selo (`OBSERVADO`, `ESTIMADO` ou `A_CONFIRMAR`), grau de confiança (`ALTA`, `MEDIA`, `BAIXA`) e respectiva evidência. A área ausente é estimada via modelo log-linear.
2. **Perguntas Fechadas e Cirúrgicas**: perguntas objetivas com opções personalizadas e "Não sei" sempre disponível. O motor só pergunta o que altera o plano ou a faixa, ordenado por impacto, e encerra o questionamento assim que nenhuma resposta mudaria o resultado.
3. **Recomendação com Faixas de Cobertura**: recomenda Essencial, Prático ou Total com faixas mín/máx em R$ por cobertura, representando o Limite Máximo de Indenização (LMI) sugerido (não se refere a prêmio).
4. **Comparação por Lacuna de Cobertura**: os planos são comparados tecnicamente pelas coberturas protegidas e lacunas existentes, nunca por preço (a base não possui preços de prêmio).

### Catálogo de Planos
* **Essencial**: incêndio/raio/explosão/fumaça, danos por água, vendaval/granizo, impacto de veículos, queda de aeronave e danos elétricos.
* **Prático**: Essencial + roubo/furto mediante arrombamento + quebra de vidros.
* **Total**: Prático + responsabilidade civil familiar + perda/pagamento de aluguel + despesas emergenciais.
*(Assistências não integram as coberturas do template).*

---

## Um Motor, Vários Canais

A inteligência de subscrição é unificada e opera em múltiplos canais com base em um semáforo de decisão:
* **Verde (App / One Click Buy)**: alta confiança e sem atritos críticos; cliente contrata com 1 clique.
* **Amarelo (App com Confirmação)**: solicita de 1 a 3 confirmações rápidas antes da contratação.
* **Vermelho (Mesa / Gerente)**: divergências ou condições especiais; gerente recebe a ficha completa e o motivo de cada pergunta.
* **SAC e Agentes Autônomos**: apoio ao atendente para leitura das opções e integração via contrato JSON padronizado.

---

## Guardrails e Privacidade

* **Minimização e LGPD**: uso exclusivo de dados do imóvel, contas de consumo e histórico de compras. Dependentes e pets entram estritamente se houver necessidade de cobertura específica. Uso do app serve apenas para priorização do canal de contato.
* **Variáveis Proibidas**: idade, renda e confiança de renda são proibidas em qualquer regra de elegibilidade ou subscrição.
* **Controle Humano**: garantido pelo transbordo ao gerente (semáforo vermelho) e autonomia do cliente em todas as confirmações.

---

## Estado Atual e Próximos Passos

* **Etapa 1 (Casa Gêmea)**: concluída. Modelo de área log-linear (`log(IPTU)`, `log(energia)`, tipo de imóvel e município) treinado na base de desenvolvimento com validação cruzada:
  * Erro percentual mediano: 13,4% (erro médio absoluto: 22,7 m²; R² = 0,86);
  * Faixa de 80% cobre a área real em 79,9% dos casos.
* **Etapa 2 (Regras do seguro)**: concluída. Elegibilidade, plano por pontuação, faixas de LMI por cobertura (custo de reconstrução via CUB), justificativa, confiança, semáforo e canal. Na base de teste: 135 elegíveis e 3 condicionados; Total 50%, Prático 40%, Essencial 10%. Ver `docs/02_regras_seguro.md`.
* **Próximos Passos**: motor de perguntas mínimas (Etapa 3), contrato JSON, conversão para os templates oficiais e demo.

---

## Dados e Entregáveis

* **Bases de Dados**: Desenvolvimento (2.200 clientes, 2.578 imóveis) e Teste Comum (120 clientes, 138 imóveis, base da entrega).
* **Entregáveis do Desafio**:
  1. `template_resultado_times.csv` (138 imóveis avaliados);
  2. `template_coberturas_times.csv` (138 imóveis com faixas de LMI);
  3. Código com requirements e versão do Python;
  4. Vídeo demonstrativo de até 5 minutos;
  5. Este documento `README.md`.

---

## Estrutura do Repositório

```text
datathon_horus/
├── README.md
├── requirements.txt               # [em breve] dependências
├── docs/
│   ├── 01_casa_gemea.md           # Etapa 1: relatório da Casa Gêmea
│   ├── 02_regras_seguro.md        # Etapa 2: elegibilidade, plano, faixas, canal
│   └── fontes_externas.md         # Fontes públicas usadas (CUB, CG, Monitor Mercantil)
├── scripts/
│   ├── 01_construir_casa_gemea.py # Etapa 1
│   ├── 02_aplicar_regras.py       # Etapa 2
│   └── 03_motor_perguntas.py      # [em breve] Etapa 3: perguntas mínimas
├── src/
│   └── casa_gemea/                # [em breve] pacote Python (carregar, área, inferências, regras, pipeline)
├── dados_externos/                # [em breve] CUB por UF, fatores de padrão, Condições Gerais
├── saidas/                        # CSVs gerados pelos scripts
└── entrega/                       # [em breve] template_resultado_times.csv e template_coberturas_times.csv
```

Os scripts rodam na raiz do projeto, em ordem numérica. As bases originais da organização ficam fora do repositório.

## Como Executar

> TODO: Documentar comandos de instalação de dependências e execução dos scripts após a publicação do pacote `src/`.

## Métricas

> TODO: Consolidar métricas finais do modelo de recomendação, perguntas evitadas e cobertura dos casos de teste.

---

## Limitações

* Tipo, vínculo e uso são sugestões extraídas de sinais indiretos e não substituem declaração oficial do cliente.
* "Proprietário quitado" é inferido pela ausência de sinais de financiamento ou aluguel.
* A base não contém informações de área rural, imóveis tombados, criminalidade local ou índices climáticos.
* O modelo de estimação de área é calibrado especificamente para os 10 municípios presentes na base.

---

## Equipe Horus

* Ludmila [a preencher]
* Milton [a preencher]
* Anna [a preencher]
* Isabella [a preencher]
* Pedro [a preencher]

---

## Uso de IA

Ferramentas de inteligência artificial foram empregadas no suporte ao desenvolvimento de código e estruturação de documentação. O desenho da solução, arquitetura de regras determinísticas e validação técnica foram concebidos e auditados pela Equipe Horus, que assume integral responsabilidade pelo projeto.
