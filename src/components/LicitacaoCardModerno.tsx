"use client";

import React, { useState } from "react";
import { 
  Building2, 
  MapPin, 
  Calendar, 
  ExternalLink, 
  DollarSign,
  FileText, 
  Share2, 
  BellRing, 
  ChevronDown, 
  ChevronUp,
  Sparkles,
  ShieldCheck,
  Tag
} from "lucide-react";

export interface LicitacaoCardModernoProps {
  orgao: string;
  objeto: string;
  localizacao: string;
  uf: string;
  abertura: string;
  modalidade: string;
  valorEstimado?: number | string | null;
  linkEdital?: string | null;
  fonte?: string;
  tipoPublicacao?: string;
  numeroProcesso?: string;
  esfera?: string;
  onCriarAlerta?: (termo: string) => void;
}

export function LicitacaoCardModerno({
  orgao,
  objeto,
  localizacao,
  uf,
  abertura,
  modalidade,
  valorEstimado,
  linkEdital,
  fonte = "PNCP",
  tipoPublicacao = "AVISO",
  numeroProcesso,
  esfera,
  onCriarAlerta
}: LicitacaoCardModernoProps) {
  const [expandido, setExpandido] = useState(false);

  // Formatação elegante de valor em Reais (R$)
  const formatarValor = (valor: number | string | null | undefined): string => {
    if (valor === null || valor === undefined || valor === "") {
      return "Valor não informado";
    }
    const num = typeof valor === "string" ? parseFloat(valor) : valor;
    if (isNaN(num) || num <= 0) {
      return "Valor não informado";
    }
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL"
    }).format(num);
  };

  const isValorInformado = (() => {
    if (valorEstimado === null || valorEstimado === undefined || valorEstimado === "") return false;
    const n = typeof valorEstimado === "string" ? parseFloat(valorEstimado) : valorEstimado;
    return !isNaN(n) && n > 0;
  })();

  const handleShareWhatsApp = () => {
    const texto = encodeURIComponent(
      `🚨 *Oportunidade de Licitação Encontrada*\n\n` +
      `🏛️ *Órgão:* ${orgao}\n` +
      `📍 *Local:* ${localizacao} - ${uf}\n` +
      `📋 *Modalidade:* ${modalidade}\n` +
      `💰 *Valor Estimado:* ${formatarValor(valorEstimado)}\n` +
      `📅 *Data de Abertura:* ${abertura || "Consulte o edital"}\n\n` +
      `📦 *Objeto:* ${objeto.slice(0, 150)}...\n\n` +
      `📄 *Link Oficial:* ${linkEdital || "https://pncp.gov.br"}`
    );
    window.open(`https://api.whatsapp.com/send?text=${texto}`, "_blank");
  };

  const isDOEMA = (fonte || "").toUpperCase().includes("DOEMA");

  return (
    <div className={`group relative bg-slate-900/80 backdrop-blur-md border rounded-2xl p-5 shadow-xl transition-all duration-300 flex flex-col justify-between hover:shadow-2xl ${
      isDOEMA 
        ? "border-amber-500/30 hover:border-amber-500/60 hover:bg-slate-900 shadow-amber-950/20" 
        : "border-slate-800 hover:border-emerald-500/50 hover:bg-slate-900 shadow-slate-950/30"
    }`}>
      {/* Glow de destaque no hover */}
      <div className={`absolute -inset-0.5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity blur-sm pointer-events-none ${
        isDOEMA ? "bg-amber-500/10" : "bg-emerald-500/10"
      }`} />

      <div className="relative z-10 space-y-3.5">
        {/* Cabeçalho: Localização + Fonte Oficial + Tipo */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          {/* Localização (Município e Estado) */}
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-slate-950/90 border border-slate-800 text-xs font-semibold text-slate-200">
            <MapPin className="h-3.5 w-3.5 text-emerald-400" />
            <span>{localizacao || "Município não informado"} - {uf || "BR"}</span>
          </div>

          {/* Badges de Fonte Oficial e Tipo */}
          <div className="flex items-center gap-1.5 flex-wrap">
            {/* Badge de Fonte */}
            {isDOEMA ? (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-[11px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm shadow-amber-950/30">
                <FileText className="h-3 w-3 text-amber-400" />
                DOEMA • MA
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-[11px] font-bold bg-blue-500/20 text-blue-300 border border-blue-500/40 shadow-sm shadow-blue-950/30">
                <ShieldCheck className="h-3 w-3 text-blue-400" />
                PNCP • Federal
              </span>
            )}

            {/* Badge Tipo de Publicação */}
            {tipoPublicacao === "COTACAO" ? (
              <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                COTAÇÃO RÁPIDA
              </span>
            ) : tipoPublicacao === "RESULTADO" ? (
              <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                RESULTADO
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                AVISO DE DISPUTA
              </span>
            )}
          </div>
        </div>

        {/* Órgão Promotor e Esfera */}
        <div className="space-y-1">
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <Building2 className="h-3.5 w-3.5 text-slate-400 shrink-0" />
            <h3 className="font-bold text-slate-200 text-sm line-clamp-1" title={orgao}>
              {orgao || "Órgão Público Responsável"}
            </h3>
          </div>

          <div className="flex items-center gap-2 text-[11px] text-slate-400">
            <span className="font-semibold text-emerald-400">{modalidade || "Pregão Eletrônico"}</span>
            {numeroProcesso && (
              <span className="font-mono text-slate-500">• {numeroProcesso}</span>
            )}
            {esfera && (
              <span className="px-1.5 py-0.2 rounded text-[10px] bg-slate-800 text-slate-300">
                {esfera}
              </span>
            )}
          </div>
        </div>

        {/* Objeto da Licitação */}
        <div className="text-slate-300 text-xs sm:text-sm leading-relaxed">
          <p className={expandido ? "" : "line-clamp-3"} title={objeto}>
            {objeto || "Objeto da licitação detalhado no edital oficial."}
          </p>
          {objeto && objeto.length > 140 && (
            <button
              type="button"
              onClick={() => setExpandido(!expandido)}
              className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 font-semibold mt-1.5 cursor-pointer transition-colors"
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
      </div>

      {/* Grid de Metadados: Valor Estimado e Data de Abertura */}
      <div className="relative z-10 mt-4 space-y-3">
        <div className="grid grid-cols-2 gap-2.5 p-3 rounded-xl bg-slate-950/70 border border-slate-800/80">
          {/* Valor Estimado */}
          <div className="space-y-0.5">
            <span className="flex items-center gap-1 text-[10px] font-bold tracking-wider uppercase text-slate-400">
              <DollarSign className="h-3 w-3 text-emerald-400" />
              Valor Estimado
            </span>
            <span className={`text-xs sm:text-sm font-black truncate block ${
              isValorInformado ? "text-emerald-400" : "text-slate-400 font-normal italic"
            }`}>
              {formatarValor(valorEstimado)}
            </span>
          </div>

          {/* Data de Disputa / Abertura */}
          <div className="space-y-0.5 border-l border-slate-800/80 pl-2.5">
            <span className="flex items-center gap-1 text-[10px] font-bold tracking-wider uppercase text-slate-400">
              <Calendar className="h-3 w-3 text-cyan-400" />
              Abertura / Disputa
            </span>
            <span className="text-xs sm:text-sm font-semibold text-slate-200 truncate block">
              {abertura || "Data a definir"}
            </span>
          </div>
        </div>

        {/* Rodapé de Ações: Acessar Edital + Compartilhar + Monitorar */}
        <div className="flex items-center gap-2 pt-1 border-t border-slate-800/80">
          {linkEdital ? (
            isDOEMA ? (
              <a
                href={linkEdital}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl bg-amber-500/15 hover:bg-amber-500/25 text-amber-200 border border-amber-500/40 text-xs font-bold transition-all shadow-sm shadow-amber-950/20 active:scale-95"
              >
                <FileText className="h-3.5 w-3.5 text-amber-400" />
                <span>Abrir Edição no DOEMA (PDF)</span>
                <ExternalLink className="h-3 w-3 opacity-70" />
              </a>
            ) : (
              <a
                href={linkEdital}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 text-blue-200 border border-blue-500/30 text-xs font-bold transition-all shadow-sm active:scale-95"
              >
                <Building2 className="h-3.5 w-3.5 text-blue-400" />
                <span>Acessar Edital no PNCP</span>
                <ExternalLink className="h-3 w-3 opacity-70" />
              </a>
            )
          ) : (
            <span className="flex-1 text-center py-2.5 px-3 text-xs text-slate-500 italic bg-slate-950/40 rounded-xl border border-slate-800/40">
              Edital em processamento oficial
            </span>
          )}

          {/* Compartilhar WhatsApp */}
          <button
            type="button"
            onClick={handleShareWhatsApp}
            title="Compartilhar oportunidade no WhatsApp"
            className="p-2.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-emerald-400 border border-slate-700/60 transition-all cursor-pointer active:scale-90"
          >
            <Share2 className="h-3.5 w-3.5" />
          </button>

          {/* Monitorar Alerta */}
          <button
            type="button"
            onClick={() => onCriarAlerta?.(objeto.slice(0, 30))}
            title="Receber alertas sobre produtos ou serviços semelhantes no WhatsApp"
            className="flex items-center gap-1 py-2.5 px-3 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-bold transition-all cursor-pointer active:scale-95"
          >
            <BellRing className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Monitorar</span>
          </button>
        </div>
      </div>
    </div>
  );
}
