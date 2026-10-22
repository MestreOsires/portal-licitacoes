"use client";

import React, { useState } from "react";
import { 
  Building2, 
  MapPin, 
  Calendar, 
  ExternalLink, 
  Sparkles, 
  BellRing,
  ChevronDown,
  ChevronUp,
  FileText,
  Share2
} from "lucide-react";
import { Licitacao } from "@/lib/types";

interface LicitacaoCardProps {
  licitacao: Licitacao;
  onCriarAlertaDoTermo: (termo: string) => void;
}

export function LicitacaoCard({ licitacao, onCriarAlertaDoTermo }: LicitacaoCardProps) {
  const [expandido, setExpandido] = useState(false);

  const formatarValor = (valor: number | null) => {
    if (!valor) return "Valor não divulgado";
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL"
    }).format(valor);
  };

  const formatarData = (dataStr: string | null) => {
    if (!dataStr) return "Data não informada";
    try {
      const data = new Date(dataStr);
      return new Intl.DateTimeFormat("pt-BR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      }).format(data);
    } catch {
      return dataStr;
    }
  };

  const getBadgeTipo = (tipo?: string) => {
    if (tipo === "RESULTADO") {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
          RESULTADO / HOMOLOGAÇÃO
        </span>
      );
    }
    if (tipo === "COTACAO") {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20">
          COTAÇÃO RÁPIDA
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
        AVISO DE LICITAÇÃO
      </span>
    );
  };

  const handleShareWhatsApp = () => {
    const texto = encodeURIComponent(
      `🚨 *Edital no Radar Licitações*\n🏛️ *Órgão:* ${licitacao.orgao}\n📍 *Local:* ${licitacao.municipio} - ${licitacao.estado}\n💰 *Valor:* ${formatarValor(licitacao.valor_estimado)}\n📅 *Disputa:* ${formatarData(licitacao.data_disputa)}\n\n📄 *Link:* ${licitacao.link_edital || "https://pncp.gov.br"}`
    );
    window.open(`https://api.whatsapp.com/send?text=${texto}`, "_blank");
  };

  return (
    <div className="group bg-slate-900/70 border border-slate-800 hover:border-slate-700 hover:bg-slate-900 rounded-2xl p-5 shadow-lg shadow-slate-950/20 transition-all duration-200 flex flex-col justify-between">
      <div>
        {/* Cabeçalho do Card: Badges de Localização, Tipo e Modalidade */}
        <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
          <div className="flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300">
            <MapPin className="h-3.5 w-3.5 text-emerald-400" />
            <span>{licitacao.municipio} - {licitacao.estado}</span>
          </div>

          <div className="flex items-center gap-1.5 flex-wrap">
            {getBadgeTipo(licitacao.tipo_publicacao)}

            {/* Badge distintivo de Fonte Oficial (DOEMA x PNCP) */}
            {licitacao.fonte === "DOEMA" ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-[11px] font-bold bg-amber-500/15 text-amber-300 border border-amber-500/40 shadow-sm shadow-amber-950/40">
                <FileText className="h-3.5 w-3.5 text-amber-400" />
                DOEMA • Diário Oficial MA
              </span>
            ) : licitacao.fonte === "PNCP" ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-[11px] font-bold bg-blue-500/15 text-blue-300 border border-blue-500/40 shadow-sm shadow-blue-950/40">
                <Building2 className="h-3.5 w-3.5 text-blue-400" />
                PNCP • Portal Nacional
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-[11px] font-bold bg-purple-500/15 text-purple-300 border border-purple-500/40">
                <Sparkles className="h-3.5 w-3.5 text-purple-400" />
                {licitacao.fonte || "Diário Oficial"}
              </span>
            )}
          </div>
        </div>

        {/* Modalidade e Número do Processo (Estilo Universo Licitações) */}
        <div className="flex items-center gap-2 text-xs text-slate-400 mb-2">
          <FileText className="h-3.5 w-3.5 text-teal-400" />
          <span className="font-semibold text-slate-300">
            {licitacao.modalidade || "Pregão Eletrônico"}
          </span>
          {licitacao.numero_processo && (
            <span className="text-[11px] text-slate-500 font-mono">
              • {licitacao.numero_processo}
            </span>
          )}
          {licitacao.esfera && (
            <span className="px-1.5 py-0.2 rounded text-[10px] bg-slate-800/80 text-slate-400">
              {licitacao.esfera}
            </span>
          )}
        </div>

        {/* Órgão Promotor */}
        <div className="flex items-start gap-2 mb-2 text-slate-300">
          <Building2 className="h-4 w-4 mt-0.5 shrink-0 text-slate-400" />
          <h3 className="font-semibold text-sm line-clamp-1 text-slate-200" title={licitacao.orgao}>
            {licitacao.orgao}
          </h3>
        </div>

        {/* Objeto da Licitação */}
        <p className={`text-sm text-slate-300 leading-relaxed mb-3 ${expandido ? "" : "line-clamp-3"}`}>
          {licitacao.objeto}
        </p>

        {licitacao.objeto && licitacao.objeto.length > 140 && (
          <button
            onClick={() => setExpandido(!expandido)}
            className="flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 mb-3 cursor-pointer"
          >
            {expandido ? (
              <>
                <ChevronUp className="h-3.5 w-3.5" /> Ver menos
              </>
            ) : (
              <>
                <ChevronDown className="h-3.5 w-3.5" /> Ver descrição completa
              </>
            )}
          </button>
        )}
      </div>

      <div>
        {/* Informações de Valor e Data de Disputa */}
        <div className="grid grid-cols-2 gap-2 p-3 bg-slate-950/60 rounded-xl border border-slate-800/80 mb-4">
          <div>
            <span className="block text-[11px] font-medium text-slate-400 uppercase tracking-wider">
              Valor Estimado
            </span>
            <span className="text-sm font-bold text-emerald-400">
              {formatarValor(licitacao.valor_estimado)}
            </span>
          </div>

          <div>
            <span className="block text-[11px] font-medium text-slate-400 uppercase tracking-wider">
              Data de Disputa
            </span>
            <div className="flex items-center gap-1 text-xs font-medium text-slate-200 mt-0.5">
              <Calendar className="h-3.5 w-3.5 text-slate-400" />
              <span>{formatarData(licitacao.data_disputa)}</span>
            </div>
          </div>
        </div>

        {/* Ações do Card */}
        <div className="flex items-center gap-2 pt-2 border-t border-slate-800">
          {licitacao.link_edital ? (
            licitacao.fonte === "DOEMA" ? (
              <a
                href={licitacao.link_edital}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg bg-amber-500/15 hover:bg-amber-500/25 text-amber-200 border border-amber-500/30 text-xs font-bold transition-all shadow-sm"
              >
                <FileText className="h-3.5 w-3.5 text-amber-400" />
                <span>Abrir Edição no DOEMA (PDF)</span>
                <ExternalLink className="h-3 w-3 opacity-70" />
              </a>
            ) : (
              <a
                href={licitacao.link_edital}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 text-blue-200 border border-blue-500/30 text-xs font-bold transition-all shadow-sm"
              >
                <Building2 className="h-3.5 w-3.5 text-blue-400" />
                <span>Acessar Edital no PNCP</span>
                <ExternalLink className="h-3.5 w-3.5 opacity-70" />
              </a>
            )
          ) : (
            <span className="flex-1 text-center py-2 px-3 text-xs text-slate-500">
              Edital em processamento
            </span>
          )}

          <button
            onClick={handleShareWhatsApp}
            title="Compartilhar no WhatsApp"
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-emerald-400 transition-colors cursor-pointer"
          >
            <Share2 className="h-3.5 w-3.5" />
          </button>

          <button
            onClick={() => onCriarAlertaDoTermo(licitacao.objeto.slice(0, 30))}
            title="Receber alertas sobre produtos ou serviços semelhantes no WhatsApp"
            className="flex items-center gap-1 py-2 px-3 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-medium transition-colors cursor-pointer"
          >
            <BellRing className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Monitorar</span>
          </button>
        </div>
      </div>
    </div>
  );
}
