# Reconciliação das Condições Gerais: v1.3 para V1.6

Data: 28/10/2026. O repositório cita as CG BB Seguros **v1.3** (out/2024). O site publica hoje a **V1.6**, vigente desde 11/08/2026, mesmo Processo SUSEP 15414.606453/2020-10. Cópia local da V1.6: `dados_externos/condicoes_gerais_bb/cg_residencial_v1_6_2026-08.pdf` (arquivo copiado sem alteração). Detalhe cláusula a cláusula: `saidas/mapa_clausulas_v13_v16.csv`. Catálogo conferido: `saidas/catalogo_adicionais_v16.csv`.

## Conclusão
As regras que sustentam os números do time **não mudaram de conteúdo**. Confirmados iguais na V1.6: aluguel (até 6 meses, mensal ≤ 1/6 do LMI), despesas emergenciais (10% nas 48 h e 3% por dia, até 30 dias), Primeiro Risco Absoluto (15.1), bens de terceiros (6.1 r), roubo sem imóvel desocupado (Roubo 2.1 c), RC Familiar (1.1 b, c, e), depreciação (24.2) e valor de novo (25.1). Todas as condições especiais batem com a v1.3 (similaridade de texto de 91% a 99%, só redação). Das 41 citações levantadas, **28 estão iguais, 10 só mudaram de numeração e 3 mudaram de texto**. Nenhuma faixa, plano ou CSV da entrega precisa mudar de valor.

## Diferenças de conteúdo que importam
1. **Exclusão nova, CG 7.1 y.** Fica excluído o evento com o imóvel desocupado ou desabitado por mais de 30 dias consecutivos, salvo imóvel de veraneio declarado na proposta. Na v1.3 só o roubo e o aluguel caíam (Roubo 2.1 c, Aluguel 3.1 a). Nossos textos dizem "segunda residência vazia = sem roubo"; na V1.6 isso é o mínimo, porque após 30 dias nenhuma cobertura vale. A Desocupação Temporária (30 a 60 dias) continua existindo. Decisão do time: reescrever os textos de ocupação e, se quiserem, perguntar "o imóvel é de veraneio declarado?". O plano recomendado não muda.
2. **CG 15.2 reescrita.** Em condomínio ou com seguro do Sistema Financeiro Habitacional, o residencial passa a ser "inicialmente destinado ao conteúdo", com Segundo Risco só para a estrutura como complemento (15.2.1). A v1.3 dizia "excepcionalmente". A conta de faixa continua válida (apartamento 10% a 30%, financiada 50% a 100%); só a justificativa deve citar o 15.2.1.
3. **Cobertura nova, CG 4.1 j: Instalações e Pequenos Reparos** (ver abaixo).
4. Sem efeito nas regras: salvamento passou a 10% do LMI limitado a R$ 5.000 (17.4); 6.1 a ficou mais ampla; a exclusão de epidemias (7.1 z) saiu; o 11 (Perda de Direitos) foi reorganizado em alíneas, sem mudar a regra da declaração inexata.

## Adicionais novos
- **Instalações e Pequenos Reparos** (4.1 j; Condições Especiais, itens 1 a 5). Serviços pela rede credenciada conforme o plano Essencial, Prático ou Total (1.3), e indenização ou reembolso quando não há prestador (1.1, 1.2). Entrou no catálogo v1.6 com as mesmas colunas. Atenção: o CLAUDE.md diz que assistências não entram no template, e o guia lista "pequenos reparos" no Essencial. Não alterei nada; vale o time decidir se o texto de justificativa deve citar esta cobertura.
- As demais adicionais da V1.6 (Alagamento, Bicicleta, Danos por Água, Danos por Chuva, Despesas Emergenciais, Desocupação, Equipamentos, Franquia Auto, Infidelidade, Obras de Arte, Paisagismo, Queda de Aeronave, RC Familiar, Rompimento) existem, com as mesmas regras. Despesas Emergenciais, Queda de Aeronave, RC e Danos por Água já são fixas dos planos e ficam fora do catálogo, como antes. A linha `DANOS_ELETRICOS_E_RAIO_FORA_DO_TERRENO` existe só na v2.3; na V1.6 danos elétricos é da Básica Ampla.
- Letras do 4.1 que mudaram: Obras de Arte j→k, Paisagismo k→l, Rompimento de Tubulações n→o.

## Numeração: trocas a fazer
| Citação atual | Na V1.6 |
|---|---|
| CG 7.1 x/y (reforma, obra) | **7.1 w/x** |
| CG 7.1 w (raio fora do terreno) | 7.1 v |
| CG 7.1 m, p, q | 7.1 m, o, p |
| CG 5.4 (partes comuns do condomínio) | **5.3** |
| CG 5.6 (limite único, prioridade) | 5.5 |
| CG 5.7 (MEI) | 5.6 |
| CG 5.2 b (conteúdo) | 5.1 b |
| CG 11.1.2 (declaração inexata) | CG 11, alínea a |
| CG 10.1 | CG 10 (o 10.1 não aparece numerado no texto) |
| Bicicleta 3.1 c e 3.1 e | 3.1 a e 3.1 c |
| "CG 1.3" (despesas) | Despesas Emergenciais 1.3 (apenas esclarecer) |
| "Vendaval 2.1 e 3.1 a" (docs/08) | provável erro de grafia: 2.1 a e 3.1 a |
| Nome e link "v1.3" | V1.6 |

## URL pública da V1.6
**URL não localizada.** O site bloqueia robôs (Incapsula) e, pelo `docs/09`, os botões "Visualizar" não expõem o link. Não contornei o bloqueio. Para registrar a fonte, usar a página `https://www.bbseguros.com.br/seguros/seguro-residencial` ("CG Seguro Residencial - V1.6") e o arquivo local.

## Arquivos do repositório que precisam trocar citação
- Código: `src/casa_gemea/regras.py` (cabeçalho, linhas com 7.1 x/y, 5.4, 1.3), `src/casa_gemea/perguntas.py` (7.1 x/y, 11.1.2), `src/casa_gemea/entrega.py` (nome e link da fonte).
- Scripts: `scripts/02_aplicar_regras.py`, `scripts/04_contrato_json.py`.
- Documentos: `README.md`, `CLAUDE.md`, `docs/02_regras_seguro.md`, `docs/03_entrega.md`, `docs/04_contrato_json.md`, `docs/08_coberturas_adicionais.md`, `docs/fontes_externas.md`; opcionais: `docs/09_inventario_site_bb.md`, `docs/03_proposta_funcionalidades.md` (fecham a pendência).
- Saídas geradas (reproduzir com os scripts, não editar à mão): `entrega/template_resultado_times.csv` (16 linhas com 7.1 x), `entrega/template_coberturas_times.csv` (52 com "5.4 e 15.2", 31 com 10.1), `saidas/recomendacao_*.csv`, `saidas/coberturas_*.csv`, `saidas/contrato/*.json`. Substituir `saidas/catalogo_adicionais.csv` pelo `_v16`.
- Cuidado ao regenerar a entrega: só os textos mudam. Conferir que valores, faixas e número de linhas (138 e 1.283) ficam idênticos.
