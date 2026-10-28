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

export interface Perfil {
  arquetipo: string; rotulo: string; descricao: string; sinais: string[]; jornada: 'EXPRESS' | 'GUIADA' | 'HUMANA';
  jornada_motivo: string; tom: string; modo: string; relacionamento_seguridade: number;
}
export interface Necessidade { cobertura: string; indice: number; nivel: string; no_plano_recomendado: boolean; fatores: { pontos: number; fator: string }[] }
export interface Adicional {
  id: string; nome: string; necessidade: number; nivel: string; por_que_para_voce: string; clausula: string;
  dados_usados: string; pergunta: string | null; cuidado: string; faixa_valor_min?: number; faixa_valor_max?: number; regra_da_faixa?: string;
}
export interface Personalizacao {
  perfil: Perfil; necessidades: Necessidade[]; adicionais_sugeridos: Adicional[];
  assistencias: { base: string; destaque: { nome: string; por_que: string }[]; so_em_plano_maior: { nome: string; por_que: string }[]; beneficio_premium_sugerido: { nome: string; por_que: string } | null };
  alertas: { tipo: string; texto: string }[]; mensagem_do_app: { titulo: string; texto: string; tom: string };
  recibos: { dado: string; usado_para: string }[]; premissas: string[];
}
export interface PassoExplicacao {
  id: string; titulo: string; resultado?: string; motivo?: string; texto?: string; regra?: string;
  checagens?: { regra: string; ok: boolean; base: string; pendente?: boolean; estado?: string }[];
  pontos_pratico?: number; pontos_total?: number; sinais_pratico?: { pontos: number; sinal: string }[]; sinais_total?: { pontos: number; sinal: string }[];
  por_que_nao_o_de_baixo?: string; por_que_nao_o_de_cima?: string; campos_que_mudam_o_plano?: string[];
}
export interface Explicacao { passos: PassoExplicacao[]; limites_do_motor: string[] }
export interface ResultadoPersonalizado extends Resultado { personalizacao: Personalizacao; explicacao: Explicacao }
export interface Persona { id: string; nome: string; frase: string }
