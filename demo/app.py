"""Demo da Casa Gêmea no formato da jornada de cotação do Seguro Residencial.

Uso (na raiz do projeto):
    streamlit run demo/app.py

Quatro visões do mesmo motor (contrato JSON em src/casa_gemea/motor.py):
- Cliente: cotação no site/app, uma pergunta por vez, plano e faixas atualizados a cada resposta;
- Gerente: todos os sinais, selos, motivo e impacto de cada pergunta;
- SAC: roteiro para o atendente ler ao telefone;
- Agente: chamada e resposta em JSON.

Protótipo do datathon: não contrata nada e não usa a marca oficial (só cores aproximadas).
"""

import json
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from casa_gemea import regras  # noqa: E402
from casa_gemea.motor import VERSAO_CONTRATO, Motor  # noqa: E402

# ----------------------------------------------------------------------- identidade
# Cores aproximadas da marca (ajuste aqui se o time tiver o manual oficial).
COR = {
    "azul": "#465EFF",
    "azul_escuro": "#2A3BB7",
    "amarelo": "#FCFC30",
    "texto": "#1C1C3C",
    "cinza": "#F2F4FF",
    "borda": "#DDE1F5",
    "verde": "#0B8A4B",
    "laranja": "#D97706",
    "vermelho": "#C62828",
}

NOME_COBERTURA = {
    "INCENDIO_RAIO_EXPLOSAO_FUMACA": "Incêndio, raio, explosão e fumaça",
    "DANOS_POR_AGUA": "Danos por água",
    "VENDAVAL_GRANIZO": "Vendaval e granizo",
    "IMPACTO_VEICULOS_TERRESTRES": "Impacto de veículos",
    "QUEDA_AERONAVE": "Queda de aeronave",
    "DANOS_ELETRICOS": "Danos elétricos",
    "ROUBO_FURTO_ARROMBAMENTO": "Roubo e furto com arrombamento",
    "QUEBRA_DE_VIDROS": "Quebra de vidros",
    "RESPONSABILIDADE_CIVIL_FAMILIAR": "Responsabilidade civil familiar",
    "PERDA_PAGAMENTO_ALUGUEL": "Perda ou pagamento de aluguel",
    "DESPESAS_EMERGENCIAIS": "Despesas emergenciais",
}
DESCRICAO_PLANO = {
    "ESSENCIAL": "Proteção do imóvel contra incêndio, água, vendaval, impactos e danos elétricos.",
    "PRATICO": "Tudo do Essencial + roubo e furto com arrombamento + quebra de vidros.",
    "TOTAL": "Tudo do Prático + aluguel, responsabilidade civil familiar e despesas emergenciais.",
}
VALOR_LEGIVEL = {
    "APARTAMENTO": "Apartamento", "CASA": "Casa", "CASA_EM_CONDOMINIO": "Casa em condomínio",
    "INQUILINO": "Moro de aluguel", "PROPRIETARIO_FINANCIADO": "Próprio, financiado",
    "PROPRIETARIO_QUITADO": "Próprio, sem financiamento", "PROPRIETARIO_LOCADOR": "Próprio, alugado a terceiros",
    "MORADIA_HABITUAL": "Moradia habitual", "TEMPORADA_OU_SEGUNDA_RESIDENCIA": "Temporada / segunda residência",
    "ALUGADO_A_TERCEIROS": "Alugado a terceiros", "ECONOMICO": "Simples", "NORMAL": "Médio", "SUPERIOR": "Alto padrão",
    "ALVENARIA": "Alvenaria", "NAO_INFORMADO": "Não informado", "SEM_SINAL": "Sem sinal de obra",
    "REFORMA_LEVE": "Reforma leve", "REFORMA_MODERADA": "Possível reforma", "POSSIVEL_OBRA_RELEVANTE": "Possível obra",
    "OBRA_ESTRUTURAL": "Obra estrutural",
}
CAMPO_LEGIVEL = {
    "tipo_imovel": "Tipo do imóvel", "vinculo": "Sua relação com o imóvel", "uso_imovel": "Uso",
    "area_m2": "Área construída", "padrao_construtivo": "Acabamento", "material_parede": "Paredes",
    "alerta_obra": "Obras", "conteudo": "Bens no imóvel",
}
SELO = {  # rótulo para o cliente, cor
    "OBSERVADO": ("do seu cadastro", COR["azul"]),
    "ESTIMADO": ("estimado", COR["laranja"]),
    "A_CONFIRMAR": ("a confirmar", COR["vermelho"]),
    "CONFIRMADO": ("confirmado por você", COR["verde"]),
}
SEMAFORO = {
    "VERDE": ("Pronto para contratar", COR["verde"]),
    "AMARELO": ("Confirme alguns dados", COR["laranja"]),
    "VERMELHO": ("Um especialista vai te ajudar", COR["vermelho"]),
}
CASOS_DEMO = {
    "IMO_CASO_00003_01": "Possível locador com sinal de reforma",
    "IMO_CASO_00001_01": "Casa em condomínio, plano já estável",
    "IMO_CASO_00013_01": "Apartamento: valor dos bens decide o plano",
    "IMO_CASO_00016_01": "Possível obra relevante (pendente)",
}


CONFIANCA = {"ALTA": "alta", "MEDIA": "média", "BAIXA": "baixa"}


def reais(v: float) -> str:
    return "R$ " + f"{v:,.0f}".replace(",", ".")


def legivel(v) -> str:
    if isinstance(v, (int, float)):
        return f"{v:,.0f}".replace(",", ".")
    return VALOR_LEGIVEL.get(v, str(v))


CSS = f"""
<style>
  html, body, [class*="css"] {{ font-family: "Nunito Sans", "Segoe UI", Arial, sans-serif; }}
  .block-container {{ padding-top: 0.5rem; max-width: 1180px; }}
  header[data-testid="stHeader"] {{ background: transparent; }}
  .bb-util {{ background: {COR['azul_escuro']}; color: #fff; font-size: 13px; padding: 6px 18px;
              display: flex; gap: 22px; border-radius: 0 0 8px 8px; }}
  .bb-util span {{ opacity: .9 }}
  .bb-nav {{ display: flex; align-items: center; justify-content: space-between; padding: 14px 6px;
             border-bottom: 1px solid {COR['borda']}; }}
  .bb-marca {{ display: flex; align-items: center; gap: 10px; font-weight: 800; font-size: 22px; color: {COR['azul']}; }}
  .bb-marca .selo {{ background: {COR['amarelo']}; color: {COR['azul']}; border-radius: 8px; padding: 2px 9px; }}
  .bb-menu {{ display: flex; gap: 22px; font-size: 15px; color: {COR['texto']}; }}
  .bb-area {{ border: 2px solid {COR['azul']}; color: {COR['azul']}; border-radius: 24px; padding: 6px 16px; font-weight: 700; font-size: 14px; }}
  .bb-trilha {{ font-size: 13px; color: #6b6f8a; margin: 10px 4px; }}
  .bb-hero {{ background: {COR['azul']}; color: #fff; border-radius: 18px; padding: 28px 32px; margin-bottom: 18px; }}
  .bb-hero h1 {{ color: {COR['amarelo']}; font-size: 34px; margin: 0 0 6px 0; padding: 0; }}
  .bb-hero p {{ font-size: 17px; margin: 0; max-width: 760px; }}
  .bb-aviso {{ background: {COR['amarelo']}; color: {COR['texto']}; display: inline-block; font-size: 12px;
               font-weight: 700; border-radius: 6px; padding: 2px 8px; margin-bottom: 10px; }}
  .bb-card {{ border: 1px solid {COR['borda']}; border-radius: 16px; padding: 18px 20px; background: #fff; margin-bottom: 14px; }}
  .bb-card h3 {{ margin: 0 0 10px 0; font-size: 19px; color: {COR['texto']}; }}
  .bb-passo {{ display: inline-block; background: {COR['azul']}; color: #fff; border-radius: 50%; width: 26px; height: 26px;
               text-align: center; line-height: 26px; font-weight: 800; margin-right: 8px; font-size: 14px; }}
  .bb-linha {{ display: flex; justify-content: space-between; gap: 10px; padding: 7px 0; border-bottom: 1px dashed {COR['borda']}; font-size: 15px; }}
  .bb-linha:last-child {{ border-bottom: none; }}
  .bb-badge {{ font-size: 11px; font-weight: 700; border-radius: 10px; padding: 2px 8px; color: #fff; white-space: nowrap; }}
  .bb-plano {{ border: 2px solid {COR['borda']}; border-radius: 16px; padding: 16px; height: 100%; background: #fff; }}
  .bb-plano.rec {{ border-color: {COR['azul']}; box-shadow: 0 6px 18px rgba(70,94,255,.18); }}
  .bb-plano .tag {{ background: {COR['amarelo']}; color: {COR['texto']}; font-weight: 800; font-size: 12px;
                    border-radius: 8px; padding: 2px 8px; display: inline-block; margin-bottom: 6px; }}
  .bb-plano h4 {{ margin: 2px 0 6px 0; color: {COR['azul']}; font-size: 20px; }}
  .bb-plano p {{ font-size: 14px; margin: 0; }}
  .bb-resumo {{ background: {COR['cinza']}; border-radius: 16px; padding: 18px 20px; }}
  .bb-resumo .plano {{ font-size: 26px; font-weight: 800; color: {COR['azul']}; }}
  .bb-status {{ border-radius: 10px; padding: 8px 12px; color: #fff; font-weight: 700; margin: 10px 0; text-align: center; }}
  .bb-pergunta {{ font-size: 18px; font-weight: 700; color: {COR['texto']}; margin-bottom: 4px; }}
  .bb-porque {{ font-size: 13px; color: #6b6f8a; margin-bottom: 10px; }}
  .bb-faixa {{ font-size: 15px; }}
  .bb-faixa b {{ color: {COR['azul']}; }}
  .bb-rodape {{ border-top: 1px solid {COR['borda']}; margin-top: 30px; padding: 16px 4px; font-size: 12px; color: #6b6f8a; }}
  .bb-sac {{ background: {COR['cinza']}; border-left: 6px solid {COR['azul']}; border-radius: 10px; padding: 18px 22px; font-size: 22px; }}
  div[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: 16px; border-color: {COR['borda']}; }}
  .bb-titulo {{ font-size: 19px; font-weight: 700; color: {COR['texto']}; margin: 2px 0 10px 0; }}
  div.stButton > button {{ border-radius: 24px; font-weight: 700; }}
  div.stButton > button[kind="primary"] {{ background: {COR['azul']}; border-color: {COR['azul']}; }}
</style>
"""


# ---------------------------------------------------------------------------- motor
@st.cache_resource(show_spinner="Carregando o motor da Casa Gêmea…")
def carregar_motor() -> Motor:
    return Motor()


def respostas_atuais(imovel_id: str) -> dict:
    return st.session_state.setdefault("respostas", {}).setdefault(imovel_id, {})


def consultar(motor: Motor, imovel_id: str) -> dict:
    entrada = {"versao_contrato": VERSAO_CONTRATO, "imovel_id": imovel_id, "respostas": respostas_atuais(imovel_id)}
    return motor.recomendar(entrada)


def responder(motor: Motor, imovel_id: str, campo: str, valor) -> None:
    """Aplica a resposta e registra o que mudou para mostrar ao usuário."""
    antes = consultar(motor, imovel_id)
    respostas_atuais(imovel_id)[campo] = valor
    depois = consultar(motor, imovel_id)
    if "erro" in depois:
        respostas_atuais(imovel_id).pop(campo)
        st.session_state["mensagem"] = ("erro", depois["erro"])
        return
    mudancas = []
    pa, pd_ = antes["recomendacao"]["plano"], depois["recomendacao"]["plano"]
    if pa != pd_:
        mudancas.append(f"o plano mudou de **{regras.NOME_PLANO.get(pa, '—')}** para **{regras.NOME_PLANO.get(pd_, '—')}**")
    ca, cd = antes["recomendacao"]["confianca_geral"], depois["recomendacao"]["confianca_geral"]
    if ca != cd:
        mudancas.append(f"a confiança foi de {CONFIANCA[ca]} para **{CONFIANCA[cd]}**")
    fa = next((c for c in antes["coberturas"] if c["cobertura"].startswith("INCENDIO")), None)
    fd = next((c for c in depois["coberturas"] if c["cobertura"].startswith("INCENDIO")), None)
    if fa and fd and (fa["faixa_valor_min"], fa["faixa_valor_max"]) != (fd["faixa_valor_min"], fd["faixa_valor_max"]):
        mudancas.append(f"a faixa de incêndio agora é {reais(fd['faixa_valor_min'])} a {reais(fd['faixa_valor_max'])}")
    if depois["elegibilidade"]["status"] == regras.INELEGIVEL:
        mudancas = ["o imóvel não pode ser segurado agora: " + depois["elegibilidade"]["motivo"]]
    st.session_state["mensagem"] = ("ok", "Cotação atualizada: " + "; ".join(mudancas) + "." if mudancas
                                    else "Resposta registrada: o plano e as faixas se mantêm.")


def mostrar_mensagem() -> None:
    if "mensagem" in st.session_state:
        tipo, texto = st.session_state.pop("mensagem")
        (st.error if tipo == "erro" else st.success)(texto)


# --------------------------------------------------------------------------- blocos
def cabecalho() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
        """
        <div class="bb-util"><span>Contratar um Seguro</span><span>Acionar e Acompanhar</span><span>Solicitar Assistência</span></div>
        <div class="bb-nav">
          <div class="bb-marca"><span class="selo">BB</span> Seguros</div>
          <div class="bb-menu"><span>Pra Você</span><span>Para Empresas</span><span>Para o Rural</span><span>Central de Ajuda</span></div>
          <div class="bb-area">Área do Cliente</div>
        </div>
        <div class="bb-trilha">Página Inicial › Seguros › Residencial › <b>Cotação</b></div>
        """,
        unsafe_allow_html=True,
    )


def hero() -> None:
    st.markdown(
        """
        <div class="bb-hero">
          <div class="bb-aviso">PROTÓTIPO · Datathon Proteção Inteligente — não é o site oficial</div>
          <h1>Seguro Residencial</h1>
          <p>Sua cotação já começa pronta: usamos o que você já tem com o banco e perguntamos
          <b>só o que muda o resultado</b>. Você vê por que cada plano foi indicado.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def titulo(n: int, texto: str) -> None:
    st.markdown(f'<div class="bb-titulo"><span class="bb-passo">{n}</span>{texto}</div>', unsafe_allow_html=True)


def badge(selo: str) -> str:
    rotulo, cor = SELO.get(selo, (selo.lower(), "#888"))
    return f'<span class="bb-badge" style="background:{cor}">{rotulo}</span>'


def card_casa(saida: dict) -> None:
    casa = saida["casa_gemea"]
    linhas = []
    for campo in ["tipo_imovel", "vinculo", "uso_imovel", "area_m2", "padrao_construtivo", "conteudo"]:
        c = casa[campo]
        if campo == "area_m2":
            lo, hi = casa["area_faixa_m2"]
            valor = f"{legivel(c['valor'])} m²" + ("" if lo == hi else f" <span style='color:#6b6f8a'>(entre {legivel(lo)} e {legivel(hi)})</span>")
        elif campo == "conteudo":
            lo, hi = casa["conteudo_faixa"]
            valor = reais(c["valor"]) if lo == hi else f"{reais(lo)} a {reais(hi)}"
        else:
            valor = legivel(c["valor"])
        linhas.append(f'<div class="bb-linha"><span>{CAMPO_LEGIVEL[campo]}</span><span><b>{valor}</b> {badge(c["selo"])}</span></div>')
    st.markdown(
        f'<div class="bb-card"><h3><span class="bb-passo">1</span>Sua casa, como o banco a vê</h3>{"".join(linhas)}</div>',
        unsafe_allow_html=True,
    )


def card_pergunta(motor: Motor, imovel_id: str, saida: dict, chave: str) -> None:
    perguntas = saida["proximas_perguntas"]
    total = len(perguntas) + len([k for k in respostas_atuais(imovel_id)])
    with st.container(border=True):
        _pergunta(motor, imovel_id, saida, chave, perguntas, total)


def _pergunta(motor, imovel_id, saida, chave, perguntas, total) -> None:
    titulo(2, "Confirme alguns dados")
    if saida["elegibilidade"]["status"] == regras.INELEGIVEL:
        st.error(saida["elegibilidade"]["motivo"])
    elif not perguntas:
        st.success("Tudo confirmado. Nenhuma outra resposta mudaria o seu plano ou os valores.")
    else:
        p = perguntas[0]
        st.progress((total - len(perguntas)) / max(total, 1), text=f"Faltam {len(perguntas)} confirmação(ões)")
        st.markdown(f'<div class="bb-pergunta">{p["pergunta"]}</div>'
                    f'<div class="bb-porque">Por que perguntamos: {p["motivo"]}.</div>', unsafe_allow_html=True)
        opcoes = p["opcoes"]
        colunas = st.columns(len(opcoes))
        for col, op in zip(colunas, opcoes):
            if col.button(op["rotulo"], key=f"{chave}-{p['id']}-{op['valor']}", use_container_width=True):
                responder(motor, imovel_id, p["id"], op["valor"])
                st.rerun()
        if p["aceita_numero"]:
            unidade = "m²" if p["id"] == "area_m2" else "R$"
            c1, c2 = st.columns([3, 1])
            valor = c1.number_input(f"Ou informe o valor exato ({unidade})", min_value=0, step=10 if unidade == "m²" else 1000,
                                    key=f"{chave}-num-{p['id']}")
            c2.write("")
            if c2.button("Informar", key=f"{chave}-numbtn-{p['id']}", use_container_width=True) and valor > 0:
                responder(motor, imovel_id, p["id"], valor)
                st.rerun()


def cards_planos(saida: dict) -> None:
    rec = saida["recomendacao"]
    plano = rec["plano"]
    with st.container(border=True):
        titulo(3, "Feito para você: compare os planos")
        if not plano:
            st.info("Sem plano disponível para este imóvel no momento.")
            return
        _planos(rec, plano)


def _planos(rec: dict, plano: str) -> None:
    colunas = st.columns(3)
    for col, p in zip(colunas, regras.ORDEM_PLANOS):
        recomendado = p == plano
        col.markdown(
            f'<div class="bb-plano {"rec" if recomendado else ""}">'
            f'{"<span class=tag>Recomendado para você</span>" if recomendado else "<span style=height:22px;display:block></span>"}'
            f'<h4>{regras.NOME_PLANO[p]}</h4><p>{DESCRICAO_PLANO[p]}</p></div>',
            unsafe_allow_html=True,
        )
    i = regras.ORDEM_PLANOS.index(plano)
    st.write("")
    if rec["por_que_este_plano"]:
        st.markdown(f"**Por que o {regras.NOME_PLANO[plano]}:** " + "; ".join(rec["por_que_este_plano"]) + ".")
    if i > 0:
        st.markdown(f"**Por que não o {regras.NOME_PLANO[regras.ORDEM_PLANOS[i - 1]]}:** {rec['por_que_nao_plano_abaixo']}")
    if i < 2:
        st.markdown(f"**Por que não o {regras.NOME_PLANO[regras.ORDEM_PLANOS[i + 1]]}:** {rec['por_que_nao_plano_acima']}")


def card_coberturas(saida: dict, chave: str) -> None:
    with st.container(border=True):
        _coberturas(saida)


def _coberturas(saida: dict) -> None:
    titulo(4, "Valores de cobertura sugeridos")
    st.caption("Limite máximo de indenização sugerido para cada cobertura. Você escolhe o valor dentro da faixa; "
               "quanto mais dados confirmados, mais estreita a faixa.")
    abas = st.tabs(["Coberturas", "Como calculamos"])
    with abas[0]:
        for c in saida["coberturas"]:
            col1, col2 = st.columns([3, 2])
            col1.markdown(f"**{NOME_COBERTURA[c['cobertura']]}**")
            faixa = reais(c["faixa_valor_min"]) if c["faixa_valor_min"] == c["faixa_valor_max"] else \
                f"{reais(c['faixa_valor_min'])} a {reais(c['faixa_valor_max'])}"
            col2.markdown(f'<div class="bb-faixa"><b>{faixa}</b></div>', unsafe_allow_html=True)
    with abas[1]:
        for c in saida["coberturas"]:
            with st.expander(NOME_COBERTURA[c["cobertura"]]):
                st.markdown(f"**Regra:** {c['regra']}  \n**Justificativa:** {c['justificativa']}")
                if c["observacao"]:
                    st.markdown(f"**Atenção:** {c['observacao']}")


def card_resumo(saida: dict, chave: str) -> None:
    rec, canal = saida["recomendacao"], saida["canal"]
    rotulo, cor = SEMAFORO[canal["semaforo"]]
    if saida["elegibilidade"]["status"] == regras.INELEGIVEL:
        rotulo, cor = "Não é possível contratar agora", COR["vermelho"]
    incendio = next((c for c in saida["coberturas"] if c["cobertura"].startswith("INCENDIO")), None)
    st.markdown(
        f'<div class="bb-resumo"><div style="font-size:13px;color:#6b6f8a">Plano indicado</div>'
        f'<div class="plano">{regras.NOME_PLANO.get(rec["plano"], "—")}</div>'
        f'<div style="font-size:14px">Confiança da recomendação: <b>{CONFIANCA[rec["confianca_geral"]]}</b></div>'
        + (f'<div style="font-size:14px">Incêndio: <b>{reais(incendio["faixa_valor_min"])} a {reais(incendio["faixa_valor_max"])}</b></div>' if incendio else "")
        + f'<div class="bb-status" style="background:{cor}">{rotulo}</div></div>',
        unsafe_allow_html=True,
    )
    pode = canal["semaforo"] == "VERDE" and saida["elegibilidade"]["status"] == regras.ELEGIVEL
    if st.button("Contratar agora" if pode else "Falar com especialista", type="primary", use_container_width=True, key=f"{chave}-contratar"):
        st.toast("Protótipo: nenhuma contratação é efetivada." if pode else "Protótipo: o atendimento seguiria com o gerente.")
    st.caption("Não usamos sua idade nem sua renda para definir plano ou valores.")


def rodape() -> None:
    st.markdown(
        '<div class="bb-rodape">Protótipo acadêmico do Datathon Proteção Inteligente (BBDW + Ibmec). Dados fictícios. '
        'Regras baseadas nas Condições Gerais do Seguro Residencial BB Seguros v1.3 (Processo SUSEP 15414.606453/2020-10). '
        'Não é um site oficial e não realiza contratações.</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------- visões
def visao_cliente(motor: Motor, imovel_id: str) -> None:
    hero()
    mostrar_mensagem()
    saida = consultar(motor, imovel_id)
    esquerda, direita = st.columns([2.1, 1])
    with esquerda:
        card_casa(saida)
        card_pergunta(motor, imovel_id, saida, "cli")
        cards_planos(saida)
        card_coberturas(saida, "cli")
    with direita:
        card_resumo(saida, "cli")


def visao_gerente(motor: Motor, imovel_id: str) -> None:
    st.subheader("Painel do gerente · Cotação Residencial")
    mostrar_mensagem()
    saida = consultar(motor, imovel_id)
    rec = saida["recomendacao"]
    m = st.columns(5)
    m[0].metric("Plano", regras.NOME_PLANO.get(rec["plano"], "—"))
    m[1].metric("Confiança", CONFIANCA[rec["confianca_geral"]].capitalize())
    m[2].metric("Semáforo", saida["canal"]["semaforo"])
    m[3].metric("Canal sugerido", saida["canal"]["sugerido"].replace("_", " ").title())
    m[4].metric("Elegibilidade", saida["elegibilidade"]["status"].replace("_", " ").title())
    if saida["elegibilidade"]["motivo"]:
        st.warning(saida["elegibilidade"]["motivo"])
    if rec["campos_que_podem_mudar_o_plano"]:
        st.info("Campos que ainda podem mudar o plano: " + ", ".join(CAMPO_LEGIVEL.get(c, c) for c in rec["campos_que_podem_mudar_o_plano"]))

    st.markdown("#### Casa Gêmea")
    casa = saida["casa_gemea"]
    st.dataframe(
        [{"Campo": CAMPO_LEGIVEL[c], "Valor": legivel(casa[c]["valor"]), "Selo": casa[c]["selo"],
          "Confiança": casa[c]["confianca"], "Evidência": casa[c]["evidencia"]} for c in CAMPO_LEGIVEL],
        use_container_width=True, hide_index=True,
    )

    st.markdown("#### Perguntas em ordem de impacto")
    if not saida["proximas_perguntas"]:
        st.success("Nada mais a perguntar.")
    for p in saida["proximas_perguntas"]:
        c1, c2, c3 = st.columns([3, 2, 1])
        c1.markdown(f"**{p['pergunta']}**  \n<span style='font-size:13px;color:#6b6f8a'>Impacto: {p['impacto']} · {p['motivo']}</span>",
                    unsafe_allow_html=True)
        rotulos = {op["rotulo"]: op["valor"] for op in p["opcoes"]}
        escolha = c2.selectbox("Resposta", list(rotulos), key=f"ger-{imovel_id}-{p['id']}", label_visibility="collapsed")
        if c3.button("Registrar", key=f"ger-btn-{imovel_id}-{p['id']}", use_container_width=True):
            responder(motor, imovel_id, p["id"], rotulos[escolha])
            st.rerun()

    st.markdown("#### Plano e comparação")
    i = regras.ORDEM_PLANOS.index(rec["plano"]) if rec["plano"] else None
    if i is not None:
        st.markdown(f"**Motivos:** {'; '.join(rec['por_que_este_plano']) or 'proteção básica'}  \n"
                    + (f"**Plano abaixo:** {rec['por_que_nao_plano_abaixo']}  \n" if i > 0 else "")
                    + (f"**Plano acima:** {rec['por_que_nao_plano_acima']}" if i < 2 else ""))
    st.markdown("#### Coberturas")
    st.dataframe(
        [{"Cobertura": NOME_COBERTURA[c["cobertura"]], "Mín (R$)": c["faixa_valor_min"], "Máx (R$)": c["faixa_valor_max"],
          "Confiança": c["confianca"], "Regra": c["regra"], "A confirmar": c["a_confirmar"]} for c in saida["coberturas"]],
        use_container_width=True, hide_index=True,
    )


def visao_sac(motor: Motor, imovel_id: str) -> None:
    st.subheader("Roteiro do atendente · Central de Relacionamento")
    mostrar_mensagem()
    saida = consultar(motor, imovel_id)
    rec = saida["recomendacao"]
    st.markdown(f"Cliente **{saida['cliente_id']}** · plano indicado **{regras.NOME_PLANO.get(rec['plano'], '—')}** "
                f"· confiança **{CONFIANCA[rec['confianca_geral']]}** · {SEMAFORO[saida['canal']['semaforo']][0]}")
    perguntas = saida["proximas_perguntas"]
    if saida["elegibilidade"]["status"] == regras.INELEGIVEL:
        st.markdown(f'<div class="bb-sac">Leia: “No momento não conseguimos seguir com a contratação. {saida["elegibilidade"]["motivo"]}”</div>',
                    unsafe_allow_html=True)
        return
    if not perguntas:
        incendio = next((c for c in saida["coberturas"] if c["cobertura"].startswith("INCENDIO")), None)
        texto = (f"Leia: “Com as suas respostas, o plano indicado é o <b>{regras.NOME_PLANO[rec['plano']]}</b>"
                 + (f", com cobertura de incêndio entre {reais(incendio['faixa_valor_min'])} e {reais(incendio['faixa_valor_max'])}" if incendio else "")
                 + ". Posso seguir com a contratação?”")
        st.markdown(f'<div class="bb-sac">{texto}</div>', unsafe_allow_html=True)
        return
    p = perguntas[0]
    opcoes = " / ".join(op["rotulo"] for op in p["opcoes"])
    st.markdown(f'<div class="bb-sac">Leia: “{p["pergunta"]}”<br><span style="font-size:16px">Opções: {opcoes}</span></div>',
                unsafe_allow_html=True)
    st.caption(f"Se o cliente perguntar por quê: {p['motivo']}.")
    st.markdown("**Registre a resposta do cliente:**")
    colunas = st.columns(len(p["opcoes"]))
    for col, op in zip(colunas, p["opcoes"]):
        if col.button(op["rotulo"], key=f"sac-{p['id']}-{op['valor']}", use_container_width=True):
            responder(motor, imovel_id, p["id"], op["valor"])
            st.rerun()
    st.caption(f"Faltam {len(perguntas)} pergunta(s). As demais não mudariam a recomendação.")


def visao_agente(motor: Motor, imovel_id: str) -> None:
    st.subheader("Agentes autônomos · Contrato JSON")
    st.caption("O agente envia o imóvel e as respostas coletadas; o motor devolve a recomendação e a próxima pergunta. "
               "Edite a entrada e envie.")
    entrada_padrao = {"versao_contrato": VERSAO_CONTRATO, "imovel_id": imovel_id, "respostas": respostas_atuais(imovel_id)}
    texto = st.text_area("Entrada", json.dumps(entrada_padrao, ensure_ascii=False, indent=2), height=180, key=f"ag-{imovel_id}")
    try:
        entrada = json.loads(texto)
    except json.JSONDecodeError as e:
        st.error(f"JSON inválido: {e}")
        return
    st.markdown("**Saída**")
    st.json(motor.recomendar(entrada), expanded=2)


# ----------------------------------------------------------------------------- página
def main() -> None:
    st.set_page_config(page_title="Seguro Residencial · Casa Gêmea", page_icon="🏠", layout="wide")
    motor = carregar_motor()

    with st.sidebar:
        st.markdown("### Demo Casa Gêmea")
        visao = st.radio("Canal", ["Cliente (site/app)", "Gerente", "SAC (telefone)", "Agente (JSON)"])
        ids = list(motor.casas.index)
        rotulo = lambda i: f"{i.replace('IMO_', '')} · {CASOS_DEMO[i]}" if i in CASOS_DEMO else i.replace("IMO_", "")
        ordem = list(CASOS_DEMO) + [i for i in ids if i not in CASOS_DEMO]
        imovel_id = st.selectbox("Cliente / imóvel", ordem, format_func=rotulo)
        if st.button("Recomeçar este cliente", use_container_width=True):
            st.session_state.setdefault("respostas", {})[imovel_id] = {}
            st.rerun()
        respostas = respostas_atuais(imovel_id)
        if respostas:
            st.markdown("**Respostas dadas**")
            for k, v in respostas.items():
                st.caption(f"{k}: {v}")
        st.divider()
        st.caption("Todas as visões usam o mesmo motor e as mesmas respostas: mude de canal no meio da jornada.")

    cabecalho()
    {"Cliente (site/app)": visao_cliente, "Gerente": visao_gerente,
     "SAC (telefone)": visao_sac, "Agente (JSON)": visao_agente}[visao](motor, imovel_id)
    rodape()


main()
