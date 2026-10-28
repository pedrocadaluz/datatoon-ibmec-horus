# Validação da interface Casa Gêmea

28/10/2026. Ambiente Windows, Python 3.13.5, Node 24.14.0, npm 11.9.0 e Chrome instalado.

- `api/.venv/Scripts/python.exe -m unittest api.test_api -v`: 8 testes aprovados. Compara 138 planos, elegibilidades e confianças, e todas as faixas do contrato com `entrega/template_resultado_times.csv` e `entrega/template_coberturas_times.csv` atuais.
- `npm --prefix web test`: 8 testes aprovados. Jornadas reais de 3 semáforos, confirmação, inelegibilidade, Não sei, quatro canais, teclado, texto ampliado, falha de rede, troca rápida de caso, JSON concorrente e campo numérico sem vazamento entre imóveis.
- `npm --prefix web run build`: TypeScript e build Vite aprovados.
- axe WCAG A/AA: nenhuma violação automática detectada nos quatro canais em desktop e no Cliente a 390px. Não equivale a certificação manual completa.
- Revisão independente com achados corrigidos: estado do valor exato, metadados de estimativa nas perguntas, limite numérico de transporte e mensagem de rede em português.

## Capturas

| Arquivo | O que mostra |
|---|---|
| `cliente-inicial.png` | Casa Gêmea, plano Total, contador do motor e destaque de aluguel |
| `cliente-confirmado.png` | Jornada concluída, Prático e faixa de incêndio 505.300 a 633.500 |
| `caso-verde.png`, `caso-amarelo.png`, `caso-vermelho.png` | Casos reais dos três semáforos na visão SAC |
| `celular-inelegivel.png` | Responsividade e encerramento por obra estrutural |
| `faixa-larga.png` | Aviso de incerteza numa cobertura cuja razão máximo/mínimo supera 4 |
| `sac-estimativa.png` | Pergunta de área com selo e confiança junto da estimativa |

Os números das imagens são dados sintéticos do motor real. Fontes, textos e CSVs foram consumidos por leitura; o frontend não calcula regras de seguro. Sem commit ou push.
