export type ValorResposta = string | number
export type Respostas = Record<string, ValorResposta>
export interface Campo { valor: string | number; selo: string; confianca: string; evidencia: string }
export interface Casa {
  tipo_imovel: Campo; vinculo: Campo; uso_imovel: Campo; area_m2: Campo;
  padrao_construtivo: Campo; material_parede: Campo; alerta_obra: Campo; conteudo: Campo;
  area_faixa_m2: [number, number]; conteudo_faixa: [number, number];
}
export interface Pergunta {
  id: string; pergunta: string; opcoes: { valor: string; rotulo: string }[];
  aceita_numero: boolean; impacto: string; motivo: string;
}
export interface Cobertura {
  cobertura: string; faixa_valor_min: number; faixa_valor_max: number; confianca: string;
  regra: string; justificativa: string; a_confirmar: string; observacao: string;
}
export interface Resultado {
  versao_contrato: string; imovel_id: string; cliente_id: string; status: string;
  elegibilidade: { status: string; motivo: string }; casa_gemea: Casa;
  recomendacao: {
    plano: string; justificativa_curta: string; confianca_geral: string; por_que_este_plano: string[];
    por_que_nao_plano_abaixo: string; por_que_nao_plano_acima: string;
    campos_que_podem_mudar_o_plano: string[];
  };
  coberturas: Cobertura[]; proximas_perguntas: Pergunta[];
  canal: { semaforo: string; sugerido: string }; respostas_aplicadas: string[];
  jornada: { campos_formulario_tradicional: number; perguntas_necessarias: number; perguntas_evitadas: number; percentual_evitado: number };
}
export interface Imovel { imovel_id: string; cliente_id: string; municipio: string; uf: string }
export interface Lista { imoveis: Imovel[]; campos_perguntaveis: string[]; versao_contrato: string }
export interface Registro { campo: string; pergunta: string; rotulo: string; valor: ValorResposta }
export type Canal = 'Cliente' | 'Gerente' | 'SAC' | 'Agente'
