# Etapa 11 — Consistência entre casos semelhantes
_Gerado por `scripts/11_consistencia.py` em 28/10/2026._

Imóveis com o mesmo tipo, vínculo, nível de bens (baixo < R$ 10 mil ≤ moderado < R$ 20 mil ≤ alto), pet e dependentes formam um grupo. Mede-se em quantos grupos (com 2 ou mais imóveis) todos recebem o mesmo plano.

| Base | Grupos | Consistentes | Imóveis em grupos consistentes |
|---|---|---|---|
| desenvolvimento | 113 | 103 (91,2%) | 2313 de 2568 (90,1%) |
| teste | 32 | 30 (93,8%) | 96 de 105 (91,4%) |

Dos 12 grupos com planos diferentes, 12 são explicados por um sinal da pontuação que fica fora do grupo (eletrônicos, vidraçaria ou desocupação). Nenhum grupo fica sem explicação.

## Grupos inconsistentes da base de teste

| Tipo | Vínculo | Bens | Pet | Dependentes | Imóveis | Planos | Sinais que variam |
|---|---|---|---|---|---|---|---|
| APARTAMENTO | PROPRIETARIO_FINANCIADO | MODERADO | não | sim | 2 | PRATICO 1; ESSENCIAL 1 | gasto com vidraçaria |
| APARTAMENTO | PROPRIETARIO_QUITADO | MODERADO | não | sim | 7 | ESSENCIAL 6; PRATICO 1 | eletrônicos acima de R$ 15 mil; gasto com vidraçaria |
