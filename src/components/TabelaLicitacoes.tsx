"use client";

import React from "react";
import { Licitacao } from "@/lib/types";
import { ExternalLink, BellRing, Building2, FileText, Sparkles } from "lucide-react";

interface TabelaLicitacoesProps {
  licitacoes: Licitacao[];
  onCriarAlertaDoTermo: (termo: string) => void;
}

export function TabelaLicitacoes({ licitacoes, onCriarAlertaDoTermo }: TabelaLicitacoesProps) {
  const formatarValor = (valor: number | null) => {
    if (!valor) return "Não informado";
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL"
    }).format(valor);
  };

  const formatarData = (dataStr: string | null) => {
    if (!dataStr) return "-";
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

  return (
    <div className="w-full overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/80 shadow-xl">
      <table className="w-full text-left text-xs border-collapse">
        <thead>
          <tr className="border-b border-slate-800 bg-slate-950/80 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
            <th className="py-3.5 px-4">Fonte</th>
            <th className="py-3.5 px-4">Local</th>
            <th className="py-3.5 px-4">Modalidade / Processo</th>
            <th className="py-3.5 px-4">Órgão</th>
            <th className="py-3.5 px-4 max-w-xs">Objeto Licitado</th>
            <th className="py-3.5 px-4">Valor Estimado</th>
            <th className="py-3.5 px-4">Data Disputa</th>
            <th className="py-3.5 px-4 text-center">Ações</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60">
          {licitacoes.map((item) => (
            <tr
              key={item.id}
              className="hover:bg-slate-800/40 transition-colors group"
            >
              {/* Fonte Oficial */}
              <td className="py-3 px-4 whitespace-nowrap">
                {item.fonte === "DOEMA" ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[10px] font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30">
                    <FileText className="h-3 w-3 text-amber-400" />
                    DOEMA • MA
                  </span>
                ) : item.fonte === "PNCP" ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[10px] font-bold bg-blue-500/15 text-blue-300 border border-blue-500/30">
                    <Building2 className="h-3 w-3 text-blue-400" />
                    PNCP • Nacional
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[10px] font-bold bg-purple-500/15 text-purple-300 border border-purple-500/30">
                    <Sparkles className="h-3 w-3 text-purple-400" />
                    {item.fonte || "D.O."}
                  </span>
                )}
              </td>

              {/* Local */}
              <td className="py-3 px-4 whitespace-nowrap">
                <span className="font-bold text-white mr-1.5">{item.estado}</span>
                <span className="text-slate-400">{item.municipio}</span>
              </td>

              {/* Modalidade / Processo */}
              <td className="py-3 px-4 whitespace-nowrap">
                <div className="font-semibold text-slate-200">{item.modalidade || "Pregão Eletrônico"}</div>
                {item.numero_processo && (
                  <div className="text-[10px] text-slate-500 font-mono">{item.numero_processo}</div>
                )}
              </td>

              {/* Órgão */}
              <td className="py-3 px-4 text-slate-300 font-medium max-w-[200px] truncate" title={item.orgao}>
                {item.orgao}
              </td>

              {/* Objeto */}
              <td className="py-3 px-4 text-slate-300 max-w-sm">
                <p className="line-clamp-2 leading-relaxed" title={item.objeto}>
                  {item.objeto}
                </p>
              </td>

              {/* Valor Estimado */}
              <td className="py-3 px-4 whitespace-nowrap font-bold text-emerald-400">
                {formatarValor(item.valor_estimado)}
              </td>

              {/* Data Disputa */}
              <td className="py-3 px-4 whitespace-nowrap text-slate-300">
                {formatarData(item.data_disputa)}
              </td>

              {/* Ações */}
              <td className="py-3 px-4 whitespace-nowrap text-center">
                <div className="flex items-center justify-center gap-1.5">
                  {item.link_edital && (
                    <a
                      href={item.link_edital}
                      target="_blank"
                      rel="noopener noreferrer"
                      title="Acessar Edital Oficial"
                      className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  )}

                  <button
                    onClick={() => onCriarAlertaDoTermo(item.objeto.slice(0, 30))}
                    title="Monitorar no WhatsApp"
                    className="p-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 transition-colors cursor-pointer"
                  >
                    <BellRing className="h-3.5 w-3.5" />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
