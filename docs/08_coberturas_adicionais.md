# Coberturas adicionais e assistências: catálogo extraído das Condições Gerais

> **Atenção (28/10/2026):** este catálogo foi feito sobre a **v1.3**. A versão vigente é a **V1.6** (desde 11/08/2026). Use `saidas/catalogo_adicionais.csv` (já conferido para a V1.6) e `docs/10_reconciliacao_cg.md` para a numeração correta das cláusulas. Diferenças: 7.1 x/y vira 7.1 w/x; MEI é 5.6; partes comuns do condomínio, 5.3; declaração inexata, 11 (alínea a); a V1.6 acrescenta **Instalações e Pequenos Reparos** (4.1 j) e a exclusão 7.1 y (desocupação acima de 30 dias).


Fonte: Condições Gerais BB Seguros **v1.3** (SUSEP 15414.606453/2020-10, 61 páginas) e **v2.3** (SUSEP 15414.003077/2009-93, 43 páginas), em `dados_externos/condicoes_gerais_bb/`. Dados completos em `saidas/catalogo_adicionais.csv` (16 linhas). Cláusulas citadas como "item" da própria CG; nada foi transcrito além de trechos curtos. Nome comercial das coberturas: **não localizado** nas CG (a página do produto não foi consultada, pois o site bloqueia robôs).

## 1. Resumo para o motor

- Os planos do guia (Essencial, Prático, Total) seguem a estrutura da **v1.3**. A v2.3 oferece muito menos (ver seção 5), então a recomendação deve usar a v1.3.
- Na v1.3, várias coberturas fixas do guia são formalmente "adicionais" (Danos por Água, RC Familiar, Despesas Emergenciais, Queda de Aeronave e Impacto de Veículos, item 4.1). Aqui, "adicional" significa **fora dos planos do guia**.
- Das 16 linhas do catálogo: 9 são oferecíveis de verdade, 3 são da Básica Ampla fora dos planos (baixa prioridade), 3 são redundantes com Danos por Água (item 4.3 proíbe contratar juntas) e 1 é o adicional elétrico da v2.3.
- **As 5 mais úteis para personalizar:** Equipamentos Portáteis, Indenização a Valor de Novo, Desocupação Temporária, Bicicleta, Atividade Profissional (MEI).

## 2. Tabela principal (adicionais oferecíveis)

| Cobertura (id) | O que cobre | Cláusula | Condições e exclusões | Dimensionável e base | Para quem faz sentido |
|---|---|---|---|---|---|
| **EQUIPAMENTOS_PORTATEIS** (v1.3) | Dano acidental e roubo ou furto com arrombamento de portáteis, dentro do imóvel; paga com depreciação | 4.1 g; Esp. Portáteis 1 a 3 | Itens listados com tipo, marca, modelo e valor (1.2); POS até 10% (3.1); queda em líquido e desgaste fora (2.1); celular é bem não coberto (6.1 k) | **Sim.** Soma dos portáteis; proxy: parcela de `compras_eletronicos_36m` | Compras de eletrônicos altas. Complementa Danos Elétricos, que não cobre queda nem dano mecânico |
| **INDENIZACAO_VALOR_DE_NOVO** (v1.3; v2.3 20.3) | Tira a depreciação do prédio e do conteúdo | 25.1; 24.2 | Prêmio adicional e aceitação (25.1); sem ela, vestuário deprecia 30% ou 50% sem nota (24.2) | **Não** (muda a base de pagamento, não o LMI) | Muito eletrônico, eletrodoméstico e móvel recentes (`compras_*_36m`) |
| **DESOCUPACAO_TEMPORARIA** (v1.3) | Mantém coberturas em desocupação de 30 a 60 dias | 4.1 f; Esp. Desocupação 1 e 2 | Proposta 15 dias antes (1.4); acima de 60 dias fora (2.1 a); obra interrompe (2.1 b). Se restabelece o roubo: **não localizado** | **Não** (extensão de condição, usa os LMI existentes) | Segunda residência, locador entre inquilinos, viagem longa, consumo de energia e água muito baixo |
| **BICICLETA** (v1.3) | Roubo (mesmo na rua) e furto com arrombamento da bicicleta | 4.1 b; Esp. Bicicleta 1 a 4 | Identificada na apólice (1.3); bicicletário e garagem comum fora (2.1 a, b); POS até 10% | **Sim.** Valor declarado, no máximo o valor real (1.6) | Quem guarda a bicicleta dentro da unidade. Gatilho: `ITEM_LAZER` (não confirmado, perguntar) |
| **ATIVIDADE_PROFISSIONAL_MEI** (v1.3 e v2.3) | Bens da atividade profissional dentro da casa | v1.3 5.7, 6.1 b; v2.3 3.1.1, 6.1 k | MEI declarado, risco aceito, prêmio adicional | **Sim.** Valor dos equipamentos (pergunta) | Quem trabalha em casa com CNPJ MEI. Nunca usar renda ou idade como gatilho |
| **OBRAS_DE_ARTE** (v1.3) | Roubo, arrombamento e quebra por queda de obras listadas | 4.1 j; 6.1 c, d; Esp. Obras 1 a 4 | Obra listada e documentada (3.1); sem ela quadro, joia e coleção não são cobertos | **Sim.** Valor por obra | Só por declaração do cliente |
| **PAISAGISMO** (v1.3) | Plantas e jardim contra incêndio, vendaval, granizo, roubo | 4.1 k; 6.1 g; Esp. Paisagismo 1 a 4 | Laudo possível (3.1); seca, pragas e chuva excessiva fora (2.1) | **Sim.** Valor do projeto | Casa com jardim investido. Baixa prioridade |
| **INFIDELIDADE_EMPREGADOS** (v1.3) | Roubo, apropriação ou estelionato por empregado doméstico registrado | 4.1 i; Esp. Infidelidade 1 e 2 | Empregado registrado e autoria comprovada (1.1); o roubo fixo exclui crimes de funcionário (Roubo 3.1 a) | **Sim.** Valor do conteúdo exposto | Pergunta: tem empregado doméstico registrado? |
| **FRANQUIA_SEGURO_AUTOMOVEL** (v1.3) | Reembolsa a franquia do casco do carro | 4.1 h; Esp. Franquia 1 e 2 | Comprovar pagamento (1.1) | **Sim.** Valor da franquia (pergunta) | Cliente com seguro auto. Baixa aderência |
| **DESMORONAMENTO**, **TERREMOTO_MAREMOTO_TREMOR_DE_TERRA**, **TUMULTOS_GREVES_LOCAUTES** (v1.3) | Itens da Básica Ampla fora dos planos | 3.3 c, g, h | Desmoronamento exclui revestimento, fundação e muro (2.1); POS até 10% | **Sim**, sobre o prédio, com perda baixa | Sem sinal no banco. Oferecer só por declaração |
| **ALAGAMENTO**, **DANOS_POR_CHUVA**, **ROMPIMENTO_TUBULACOES** (v1.3) | Já contidos em Danos por Água | 4.1; **4.3** | Não podem ser contratados com Danos por Água | Mesma base de Danos por Água | **Não oferecer** a quem tem plano do guia. Rompimento tem POS de até 15% (3.1) |
| **DANOS_ELETRICOS_E_RAIO_FORA_DO_TERRENO** (v2.3) | Danos elétricos e raio fora do terreno | v2.3 adicional 1 a 5; v1.3 7.1 w | Na v2.3 só vale se identificado na apólice (2.2.2); lâmpadas e fusíveis fora | **Sim.** Valor de eletroeletrônicos | Já é fixa dos planos (53,3% dos sinistros da carteira, dado de contexto do projeto) |

## 3. Coberturas fixas com condição especial (devem ir na justificativa)

| Fixa do plano | Condição que importa (cláusula v1.3) |
|---|---|
| ROUBO_FURTO_ARROMBAMENTO | Não cobre imóvel desocupado, vazio ou mobiliado (Esp. Roubo 2.1 c); drones fora; bicicleta só dentro de casa ou box fechado (2.1 a, b); crime de funcionário fora (3.1 a); POS até 10% |
| PERDA_PAGAMENTO_ALUGUEL | Prazo máximo de 6 meses; aluguel mensal até 1/6 do LMI (1.2, 1.3); não cobre imóvel desocupado (3.1 a); vale para locador (1.1.1 a), proprietário morador que precisa de moradia temporária (1.1.1 b) e inquilino (1.1.2); pode pedir contrato e comprovante (2.1) |
| DESPESAS_EMERGENCIAIS | Imóvel inadequado por no mínimo 24 horas ou interditado (1.1); 10% do LMI nas primeiras 48 horas e 3% por 24 horas seguintes, até 30 dias (1.3); aluguel não entra (1.2) |
| RESPONSABILIDADE_CIVIL_FAMILIAR | Cobre pet, vazamento do imóvel para o vizinho, esporte, bicicleta e trabalhos de manutenção (1.1 a a g); não cobre bens de terceiros em poder do segurado, parentes que moram juntos, veículos, dano moral (2.1); exige sentença ou acordo autorizado (1.1) |
| DANOS_ELETRICOS | POS até 10% (4.1); lâmpadas, baterias, transformadores fora (2.1 a); dano mecânico e instalação precária fora (3.1) |
| DANOS_POR_AGUA | Exclui torneira aberta, umidade, manutenção feita pelo segurado e troca de material em cômodos sem dano (2.1); mesmo evento em 72 horas (1.1 d); POS até 10% |
| VENDAVAL_GRANIZO | Cercas, muros e portões e bens soltos ao ar livre fora (2.1); calha entupida fora (3.1 a); POS até 10% |
| QUEBRA_DE_VIDROS | Quebra por vendaval, temperatura ou colocação fora (3.1); arranhão fora; franquia na apólice (4.1) |
| QUEDA_AERONAVE / IMPACTO_VEICULOS | Veículo ou aeronave do próprio segurado, sócios, familiares e empregados fora (2.1 a); POS até 10% |
| INCENDIO_RAIO_EXPLOSAO_FUMACA | Queimada rural fora; dano de raio ao conteúdo fora (2.1); inclui reposição de documentos pessoais (1.2) |

Pontos gerais: contratação a Primeiro Risco Absoluto (CG 15.1); Segundo Risco para condomínio e financiamento habitacional (15.2); prédio e conteúdo em limite único dá prioridade ao prédio (5.6); depreciação do conteúdo sem a cláusula de valor de novo (24.2).

## 4. Assistências (não entram como linhas do template)

Nomes e conteúdo conforme o guia (seção 9.2, `p11.png`). As CG não detalham as assistências: o guia manda consultar os manuais oficiais para limites e uso.

| Assistência (plano) | Serviços | Situação do cliente que a relaciona |
|---|---|---|
| Casa em Apuros (todos) | Chaveiro, eletricista, encanador, desentupimento, telhado provisório, limpeza pós-sinistro | Vazamento, queda de energia, telhado danificado, alagamento |
| Casa Funcionando (Prático e Total) | Conserto de eletrodomésticos, fogão, cooktop, ar-condicionado, TV | Muito eletrodoméstico e eletrônico (`compras_*_36m`); não indeniza o bem, só o serviço |
| Casa Arrumada (Prático e Total) | Instalação, fixação, montagem, descarte | Mudança recente, compras de móveis |
| Casa Limpa (Prático e Total) | Calhas, ralos, sifões, caixa d'água, placa solar, caçamba | Casa com calha e telhado (previne Danos por Chuva e a exclusão por falta de manutenção); locador entre inquilinos |
| Casa sem Insetos e Pragas (Total) | Desinsetização | Pet, dependentes, imóvel de locação |
| Casa Segura (Total) | Aquecedor a gás, película de box, fechadura eletrônica, tela de proteção, olho mágico | Dependentes pequenos e pet (tela, película); imóvel vazio ou segunda residência; ver Desocupação Temporária |
| Benefício premium (Total) | Não detalhado no guia | Não localizado |

## 5. O que não dá para cobrir (avisar o cliente)

1. **Imóvel desocupado**: roubo e perda de aluguel não cobrem (Roubo 2.1 c; Aluguel 3.1 a). Só a Desocupação Temporária estende, de 30 a 60 dias, e ela exige aviso 15 dias antes.
2. **Imóvel em obra, reforma ou construção**: exclusão geral (CG 7.1 x, y). Pequenos reparos de manutenção sem mexer na estrutura são permitidos.
3. **Declaração inexata ou omissão** que influa na aceitação ou no preço: perda do direito à indenização (CG 11.1.2); sem má-fé, a seguradora pode cancelar ou cobrar a diferença (11.2). É o motivo de perguntar ocupação, obra e uso.
4. **Bens fora da cobertura geral** (CG 6.1): celulares, joias e relógios, obras de arte e coleções (sem cobertura própria), dinheiro, veículos, animais, plantas, bens de terceiros em poder do segurado, bens da atividade profissional sem MEI, bens ao ar livre, bens sem comprovação de origem.
5. **Uso comercial**: fora, salvo MEI declarado com prêmio adicional (5.7).
6. **Rural**: instalações para produção rural e queimada rural fora (6.1 q; Incêndio 2.1 a).
7. **Infiltração, umidade, desgaste e má conservação**: excluídos (CG 7.1 m, p, q).
8. **Calha entupida**, cercas, muros e portões em vendaval (Vendaval 2.1 e 3.1 a).
9. **Cobertura de seguro principal**: condomínio e financiamento habitacional esgotam primeiro o seguro específico (15.2).

## 6. Diferenças v1.3 x v2.3 que afetam a recomendação

| Ponto | v1.3 | v2.3 |
|---|---|---|
| Estrutura | Básica Simples ou Ampla, mais 14 adicionais | Só básica (incêndio, explosão, raio) e 2 adicionais (danos elétricos e raio fora do terreno; RC Familiar) |
| Roubo, vidros, vendaval, aluguel, água, despesas emergenciais | Coberturas contratáveis | **Excluídos** (5.1 t, y, o, z, i a m, w) |
| Desocupação | Roubo e aluguel excluem desocupado; adicional de 30 a 60 dias | Desocupação acima de 30 dias exclui tudo, salvo veraneio (5.1 bb) |
| RC Familiar | Cobre esporte, vazamento para o vizinho, bicicleta, parentes dependentes (1.1) | **Exclui** esporte (2.1 n) e vazamento (2.1 h); terceiros excluem ascendentes e descendentes; só filhos menores |
| Danos elétricos | Básica Ampla (1.1), com POS até 10% | Adicional pago, franquia por evento |
| Depreciação | Tabela do item 24.2; valor de novo é adicional (25.1) | Linha reta; valor de novo após reparo em até 180 dias (20.2, 20.3) |
| Limite | LMI por cobertura, Primeiro Risco Absoluto (15.1, 17) | Limite máximo da garantia da básica e limites por adicional (16.1) |

**Consequência:** os planos do guia só existem na v1.3. Recomendar RC com base em vazamento para o vizinho ou esporte vale só na v1.3 (decisão em aberto do time sobre apartamento e Total, ver CLAUDE.md); na v2.3 isso seria negativa.

## 7. Observações para o time

- O guia lista "pequenos reparos" entre as coberturas do Essencial, mas as CG v1.3 só tratam disso como exceção à exclusão de obras (7.1 x). O catálogo fixo da base não tem essa linha; não foi alterado.
- Nenhuma cobertura adicional tem preço na base, então a recomendação deve ser por lacuna de cobertura (regra do projeto), e os adicionais com faixa precisam de premissa de base (coluna `base_de_calculo`).
- O catálogo em CSV não altera templates nem motor; integração fica a cargo do time.
