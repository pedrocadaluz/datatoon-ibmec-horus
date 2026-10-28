# Documentação do projeto

Cada relatório de etapa é gerado pelo script de mesmo número (exceto os de pesquisa, que são manuais). Rode os scripts na raiz do projeto.

| Documento | O que é | Origem |
|---|---|---|
| `01_casa_gemea.md` | Casa Gêmea: inferências, modelo de área, limitações | `scripts/01_construir_casa_gemea.py` |
| `02_regras_seguro.md` | Elegibilidade, escolha de plano, faixas por cobertura, canal | `scripts/02_aplicar_regras.py` |
| `03_entrega.md` | Templates oficiais preenchidos (coberturas fixas e adicionais com faixa) e 14 testes de formato | `scripts/03_gerar_entrega.py` |
| `04_contrato_json.md` | Contrato de entrada e saída do motor e jornada de exemplo | `scripts/04_contrato_json.py` |
| `05_pesquisa_marca_bb.md` | Marca e primeira tela de cotação do BB Seguros (cores, tipografia, tom) | Pesquisa manual |
| `06_auditoria_proxy.md` | Idade e renda não vazam para o plano (contrafactual, associação, previsibilidade) | `scripts/06_auditoria_proxy.py` |
| `07_analise_colunas.md` | Análise coluna a coluna das tabelas e arquétipos (em andamento) | `scripts/07_analise_colunas.py` |
| `08_coberturas_adicionais.md` | Catálogo de coberturas adicionais e assistências nas Condições Gerais | Leitura das CG |
| `09_inventario_site_bb.md` | O que o site do BB Seguros já oferece e as lacunas | Pesquisa manual |
| `10_reconciliacao_cg.md` | Mapa de cláusulas v1.3 para V1.6 (em andamento) | Leitura das CG |
| `14_cores_site_bb.md` | Levantamento das cores do site do BB Seguros | Pesquisa manual |
| `15_consistencia.md` | Consistência entre casos semelhantes: imóveis parecidos recebem o mesmo plano? | `scripts/11_consistencia.py` |
| `fontes_externas.md` | Fontes públicas: CG, CUB, Sinduscon, Monitor Mercantil | Manual |

Convenção: documentos numerados seguem a ordem de construção; novos itens entram no fim da tabela.
