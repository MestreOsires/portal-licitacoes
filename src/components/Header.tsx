"use client";

import React from "react";
import { Zap, BellRing, TrendingUp, CheckCircle, Clock } from "lucide-react";
import { PlacarDoDia } from "@/lib/types";

interface HeaderProps {
  onOpenAlertaModal: () => void;
  placar: PlacarDoDia;
}

export function Header({ onOpenAlertaModal, placar }: HeaderProps) {
  const formatarValorResumido = (val: number) => {
    if (val >= 1_000_000) return `R$ ${(val / 1_000_000).toFixed(1)}M`;
    if (val >= 1_000) return `R$ ${(val / 1_000).toFixed(0)}k`;
    return `R$ ${val.toFixed(0)}`;
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800 bg-slate-950/90 backdrop-blur-md">
      {/* Barra Superior - Placar do Dia (Universo Licitações Style) */}
      <div className="bg-slate-900/80 border-b border-slate-800/80 py-1.5 px-4 sm:px-6 lg:px-8 text-xs text-slate-300">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-4 flex-wrap">
            <span className="font-bold text-emerald-400 flex items-center gap-1.5">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              Placar do Dia:
            </span>
            <div className="flex items-center gap-1.5">
              <span className="text-slate-400">Avisos de Licitações:</span>
              <strong className="text-white font-bold">{placar.totalLicitacoes}</strong>
            </div>
            <div className="hidden sm:flex items-center gap-1.5">
              <span className="text-slate-400">Resultados/Homologações:</span>
              <strong className="text-amber-400 font-bold">{placar.totalResultados}</strong>
            </div>
            <div className="hidden md:flex items-center gap-1.5">
              <span className="text-slate-400">Cotações Rápidas:</span>
              <strong className="text-cyan-400 font-bold">{placar.totalCotacoes}</strong>
            </div>
            <div className="hidden lg:flex items-center gap-1.5">
              <span className="text-slate-400">Total em Disputa:</span>
              <strong className="text-emerald-400 font-bold">{formatarValorResumido(placar.totalValor)}</strong>
            </div>
          </div>

          <div className="flex items-center gap-3 text-slate-400 text-[11px]">
            <span>Captura Automática: <strong>12:00</strong> & <strong>18:00 (BSB)</strong></span>
          </div>
        </div>
      </div>

      {/* Barra Principal do Header */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-18 flex items-center justify-between">
        {/* Logo & Marca */}
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-emerald-500 via-teal-400 to-cyan-500 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Zap className="h-5 w-5 text-slate-950 stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-xl sm:text-2xl tracking-tight text-white">
                Radar<span className="text-emerald-400">Licitações</span>
              </span>
              <span className="hidden md:inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                PRO
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">
              Inteligência de mercado, busca por radical & agregação multi-fontes
            </p>
          </div>
        </div>

        {/* Botões de Ação */}
        <div className="flex items-center gap-3">
          <button
            onClick={onOpenAlertaModal}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 font-bold text-xs sm:text-sm shadow-md shadow-emerald-500/20 hover:from-emerald-400 hover:to-teal-400 transition-all cursor-pointer active:scale-95"
          >
            <BellRing className="h-4 w-4 stroke-[2.5]" />
            <span>Alerta no WhatsApp</span>
          </button>
        </div>
      </div>
    </header>
  );
}
