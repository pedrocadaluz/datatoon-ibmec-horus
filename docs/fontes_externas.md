# Fontes externas

Todas as fontes são públicas. Acesso em 27/10/2026. Os arquivos ficam em `dados_externos/`.

| Fonte | Arquivo no projeto | Para que serve |
|---|---|---|
| Condições Gerais do Seguro Residencial BB Seguros | `dados_externos/condicoes_gerais_bb/` | Regras de cobertura, exclusões e limites |
| CUB R8-N por UF | `dados_externos/cub_r8n_por_uf.csv` | Custo de reconstrução por m² |
| Tabela CUB Sinduscon-MG | `dados_externos/fatores_cub_padrao.csv` | Fatores de tipo (casa × apartamento) e padrão |
| Monitor Mercantil | citado no texto | Distribuição de sinistros da carteira residencial |

## 1. Condições Gerais do Seguro Residencial (BB Seguros)

- **Documento principal:** Seguro Residencial: Condições Gerais e Especiais, **V1.6, vigente desde 11/08/2026** (página do produto: https://www.bbseguros.com.br/seguros/seguro-residencial; cópia local `cg_residencial_v1_6_2026-08.pdf`; a v1.3 de out/2024 foi usada na primeira versão e conferida em `docs/10_reconciliacao_cg.md`). Aliança do Brasil Seguros S.A. (BB Seguros), Processo SUSEP 15414.606453/2020-10, 171 páginas, publicado em out/2024.
- **Documento de apoio:** [Seguro Residencial v2.3](https://assets-bbseguros.cld.brasilseg.com.br/2024-08/SEGURO_RESIDENCIAL-V_23_0.pdf), Processo SUSEP 15414.003077/2009-93 (ago/2024). Consultado para comparar a regra de imóvel desocupado e de veraneio.
- **Licença:** documento contratual público, distribuído pela seguradora. Cópia local guardada para reprodutibilidade.
- **Método:** download do PDF e extração do texto com PyMuPDF; leitura dos itens de cobertura, exclusões, aceitação e limites.
- **Itens usados:** 3 e 4 (coberturas), 5.3 (partes comuns do condomínio), 5.6 (MEI), 6.1 (bens não cobertos), 7.1 w/x (obra e reforma), 7.1 y (desocupação acima de 30 dias), 10 (beneficiário), 11, alínea a (declaração inexata), 12 (aceitação), 15.1 (Primeiro Risco Absoluto), 15.2 (Segundo Risco em condomínio e financiamento habitacional), 34 (inspeção) e Condições Especiais de Roubo, Perda de Aluguel e Despesas Emergenciais.
- **Limitações:** o guia do datathon não informa a versão vigente do produto vendido com os nomes Essencial, Prático e Total; usamos a versão mais recente encontrada. Os limites em reais de cada plano não estão nas Condições Gerais: aparecem só na apólice ou no certificado.

## 2. CUB R8-N por UF

- **O que é:** Custo Unitário Básico de construção (NBR 12.721), projeto R8 (residencial de 8 pavimentos) de padrão normal, calculado mensalmente por cada Sinduscon estadual.
- **Onde foi obtido:** páginas de consulta do [myside.com.br](https://myside.com.br/guia-imoveis/cub-sp), que reproduzem o valor publicado por cada Sinduscon. O link de cada UF está no CSV.
- **Referência:** set/2026 (SP, DF, RJ, PR, MG, PE, RS) e ago/2026 (BA, CE).
- **Transformação:** nenhuma. Goiás usa o valor do DF, porque o Sinduscon-GO publica como principal a categoria R16-A (alto padrão), que não é comparável.
- **Limitações:** a fonte é secundária. O CUB não inclui fundações, elevadores, áreas externas, projetos e remuneração do construtor, então a reconstrução real tende a ser maior. Não substitui uma avaliação do imóvel.

## 3. Fatores de tipo e padrão (Sinduscon-MG)

- **Fonte:** [Tabela CUB/m² Sinduscon-MG, abril/2025](https://sinduscon-mg.org.br/wp-content/uploads/2025/05/tabela_cub_abril_2025.pdf).
- **Transformação:** cada valor dividido pelo R8-N de MG (R$ 2.333,48). Exemplos: R8-B = 0,903, R8-A = 1,224, R1-N (casa) = 1,208, R1-A = 1,505.
- **Uso:** apartamento usa o projeto R-8 e casa usa o R-1, em todas as UFs.
- **Limitações:** as razões entre padrões são de Minas Gerais e de 2025. Aplicá-las a outras UFs supõe que a proporção entre padrões é parecida.

## 4. Distribuição de sinistros da carteira residencial

- **Fonte:** [Monitor Mercantil, "Danos elétricos na metade dos sinistros residenciais", 21/07/2026](https://monitormercantil.com.br/?p=332625), com dados da BB Seguros de jan/2023 a mai/2026.
- **Números usados:** danos elétricos 53,3% dos sinistros; danos por água 14,6%; eventos climáticos (vendaval e granizo) 11,5%; roubo ou furto mediante arrombamento 2,1%.
- **Uso:** contexto nas justificativas e no pitch. Não entra em nenhum cálculo de faixa.
- **Limitações:** é a frequência de acionamentos, não o valor das perdas.

## Dados que não usamos

A base não traz índices de alagamento, vendaval ou furto por região, e não buscamos esses índices. As coordenadas são perturbadas e o CEP é fictício, então um cruzamento fino por localização não seria confiável.
