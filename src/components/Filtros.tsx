"use client";

import React, { useState } from "react";
import { 
  Search, 
  MapPin, 
  DollarSign, 
  Filter, 
  RefreshCw, 
  Landmark, 
  SlidersHorizontal,
  ChevronDown,
  ChevronUp,
  Globe2,
  CalendarDays,
  ArrowUpDown,
  FileCheck2
} from "lucide-react";
import { FiltrosLicitacao } from "@/lib/types";

interface FiltrosProps {
  filtros: FiltrosLicitacao;
  onChangeFiltros: (novosFiltros: FiltrosLicitacao) => void;
  onBuscar: () => void;
  onLimpar: () => void;
  carregando: boolean;
}

const ESTADOS_BRASIL = [
  "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
  "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
  "RS", "RO", "RR", "SC", "SP", "SE", "TO"
];

const REGIOES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"];

const MODALIDADES = [
  "Pregão Eletrônico",
  "Concorrência Eletrônica",
  "Dispensa Eletrônica",
  "Inexigibilidade",
  "Leilão",
  "Diálogo Competitivo",
  "Tomada de Preços"
];

const ESFERAS = ["Federal", "Estadual", "Municipal"];

export function Filtros({
  filtros,
  onChangeFiltros,
  onBuscar,
  onLimpar,
  carregando
}: FiltrosProps) {
  const [expandido, setExpandido] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onBuscar();
  };

  const handleTabTipo = (tipo: string) => {
    onChangeFiltros({ ...filtros, tipoPublicacao: tipo });
  };

  const tipoAtual = filtros.tipoPublicacao || "TODOS";

  return (
    <div className="w-full bg-slate-900/90 border border-slate-800 rounded-2xl p-4 sm:p-5 shadow-xl shadow-slate-950/40 space-y-4">
      {/* Abas Superiores - Inspiradas no Universo Licitações (Avisos, Resultados, Agenda, Cotações) */}
      <div className="flex items-center gap-1 sm:gap-2 overflow-x-auto pb-1 border-b border-slate-800 text-xs font-semibold scrollbar-none">
        <button
          type="button"
          onClick={() => handleTabTipo("TODOS")}
          className={`px-3 py-1.5 rounded-lg whitespace-nowrap transition-all cursor-pointer ${
            tipoAtual === "TODOS"
              ? "bg-emerald-500 text-slate-950 font-bold shadow-md shadow-emerald-500/20"
              : "text-slate-400 hover:text-white hover:bg-slate-800"
          }`}
        >
          Todas as Publicações
        </button>

        <button
          type="button"
          onClick={() => handleTabTipo("AVISO")}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg whitespace-nowrap transition-all cursor-pointer ${
            tipoAtual === "AVISO"
              ? "bg-emerald-500 text-slate-950 font-bold shadow-md shadow-emerald-500/20"
              : "text-slate-400 hover:text-white hover:bg-slate-800"
          }`}
        >
          <FileCheck2 className="h-3.5 w-3.5" />
          <span>Avisos de Licitação</span>
        </button>

        <button
          type="button"
          onClick={() => handleTabTipo("RESULTADO")}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg whitespace-nowrap transition-all cursor-pointer ${
            tipoAtual === "RESULTADO"
              ? "bg-amber-400 text-slate-950 font-bold shadow-md shadow-amber-400/20"
              : "text-slate-400 hover:text-white hover:bg-slate-800"
          }`}
        >
          <span>Resultados / Homologações</span>
        </button>

        <button
          type="button"
          onClick={() => handleTabTipo("AGENDA")}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg whitespace-nowrap transition-all cursor-pointer ${
            tipoAtual === "AGENDA"
              ? "bg-cyan-400 text-slate-950 font-bold shadow-md shadow-cyan-400/20"
              : "text-slate-400 hover:text-white hover:bg-slate-800"
          }`}
        >
          <CalendarDays className="h-3.5 w-3.5" />
          <span>Agenda de Disputas</span>
        </button>

        <button
          type="button"
          onClick={() => handleTabTipo("COTACAO")}
          className={`px-3 py-1.5 rounded-lg whitespace-nowrap transition-all cursor-pointer ${
            tipoAtual === "COTACAO"
              ? "bg-purple-400 text-slate-950 font-bold shadow-md shadow-purple-400/20"
              : "text-slate-400 hover:text-white hover:bg-slate-800"
          }`}
        >
          Cotações / Dispensas
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Barra de Busca com Stemming / Radical */}
        <div>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400">
              <Search className="h-5 w-5" />
            </div>
            <input
              type="text"
              placeholder="Digite produtos ou serviços (separados por vírgula, ex: 'medicamento, respirador, pavimentação')..."
              value={filtros.busca || ""}
              onChange={(e) => onChangeFiltros({ ...filtros, busca: e.target.value })}
              className="w-full pl-12 pr-28 py-3.5 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all"
            />
            <div className="absolute right-2 top-2">
              <button
                type="submit"
                disabled={carregando}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-500 text-slate-950 font-bold text-xs hover:bg-emerald-400 transition-all cursor-pointer shadow"
              >
                {carregando ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Search className="h-3.5 w-3.5" />}
                <span>Buscar</span>
              </button>
            </div>
          </div>
          <p className="mt-1.5 text-[11px] text-slate-500 pl-1">
            * <strong>Busca inteligente por radical:</strong> encontra automaticamente variações no singular e plural (ex: &quot;computador&quot; localiza &quot;computadores&quot;, sem distinção de acentos).
          </p>
        </div>

        {/* Linha de Filtros Principais */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Região Geográfica */}
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
              <Globe2 className="h-4 w-4" />
            </div>
            <select
              value={filtros.regiao || ""}
              onChange={(e) => onChangeFiltros({ ...filtros, regiao: e.target.value })}
              className="w-full pl-10 pr-8 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 appearance-none cursor-pointer"
            >
              <option value="">Todas as Regiões</option>
              {REGIOES.map((r) => (
                <option key={r} value={r}>
                  Região {r}
                </option>
              ))}
            </select>
          </div>

          {/* Estado / UF */}
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
              <MapPin className="h-4 w-4" />
            </div>
            <select
              value={filtros.estado || ""}
              onChange={(e) => onChangeFiltros({ ...filtros, estado: e.target.value })}
              className="w-full pl-10 pr-8 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 appearance-none cursor-pointer"
            >
              <option value="">Todos os Estados (UF)</option>
              <optgroup label="Prioritários">
                <option value="MA">Maranhão (MA)</option>
                <option value="PA">Pará (PA)</option>
                <option value="TO">Tocantins (TO)</option>
              </optgroup>
              <optgroup label="Demais Estados">
                {ESTADOS_BRASIL.filter((u) => !["MA", "PA", "TO"].includes(u)).map((uf) => (
                  <option key={uf} value={uf}>
                    {uf}
                  </option>
                ))}
              </optgroup>
            </select>
          </div>

          {/* Modalidade de Licitação */}
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
              <Filter className="h-4 w-4" />
            </div>
            <select
              value={filtros.modalidade || ""}
              onChange={(e) => onChangeFiltros({ ...filtros, modalidade: e.target.value })}
              className="w-full pl-10 pr-8 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 appearance-none cursor-pointer"
            >
              <option value="">Todas as Modalidades</option>
              {MODALIDADES.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>

          {/* Agenda / Período */}
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
              <CalendarDays className="h-4 w-4" />
            </div>
            <select
              value={filtros.periodoAgenda || "todos"}
              onChange={(e) => onChangeFiltros({ ...filtros, periodoAgenda: e.target.value })}
              className="w-full pl-10 pr-8 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 appearance-none cursor-pointer"
            >
              <option value="todos">Qualquer Data de Disputa</option>
              <option value="hoje">Disputas Hoje</option>
              <option value="amanha">Disputas Amanhã</option>
              <option value="7dias">Próximos 7 dias</option>
              <option value="30dias">Próximos 30 dias</option>
            </select>
          </div>
        </div>

        {/* Painel Avançado Retrátil */}
        {expandido && (
          <div className="pt-3 border-t border-slate-800/80 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 animate-fade-in">
            {/* Esfera */}
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                <Landmark className="h-4 w-4" />
              </div>
              <select
                value={filtros.esfera || ""}
                onChange={(e) => onChangeFiltros({ ...filtros, esfera: e.target.value })}
                className="w-full pl-10 pr-8 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 appearance-none cursor-pointer"
              >
                <option value="">Todas as Esferas</option>
                {ESFERAS.map((esf) => (
                  <option key={esf} value={esf}>
                    Esfera {esf}
                  </option>
                ))}
              </select>
            </div>

            {/* Município */}
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                <MapPin className="h-4 w-4" />
              </div>
              <input
                type="text"
                placeholder="Filtrar por cidade..."
                value={filtros.municipio || ""}
                onChange={(e) => onChangeFiltros({ ...filtros, municipio: e.target.value })}
                className="w-full pl-10 pr-3 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-500 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            {/* Valor Mínimo */}
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                <DollarSign className="h-4 w-4" />
              </div>
              <input
                type="number"
                placeholder="Valor Estimado Mínimo"
                value={filtros.valorMin || ""}
                onChange={(e) =>
                  onChangeFiltros({
                    ...filtros,
                    valorMin: e.target.value ? parseFloat(e.target.value) : undefined
                  })
                }
                className="w-full pl-10 pr-3 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-500 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            {/* Ordenação */}
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                <ArrowUpDown className="h-4 w-4" />
              </div>
              <select
                value={filtros.ordenacao || "disputa_asc"}
                onChange={(e) => onChangeFiltros({ ...filtros, ordenacao: e.target.value as FiltrosLicitacao["ordenacao"] })}
                className="w-full pl-10 pr-8 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 appearance-none cursor-pointer"
              >
                <option value="disputa_asc">Data Disputa (Mais Próxima)</option>
                <option value="disputa_desc">Data Disputa (Mais Distante)</option>
                <option value="valor_desc">Maior Valor Estimado</option>
                <option value="valor_asc">Menor Valor Estimado</option>
              </select>
            </div>
          </div>
        )}

        {/* Rodapé de Ações dos Filtros */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-800/80">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setExpandido(!expandido)}
              className="flex items-center gap-1.5 text-xs text-emerald-400 hover:text-emerald-300 font-semibold py-1 px-2 rounded-lg hover:bg-slate-800 transition-colors cursor-pointer"
            >
              <SlidersHorizontal className="h-3.5 w-3.5" />
              <span>{expandido ? "Ocultar Filtros Avançados" : "Mais Filtros (Esfera, Município, Ordenação)"}</span>
              {expandido ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
            </button>
          </div>

          <button
            type="button"
            onClick={onLimpar}
            className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 py-1 px-2.5 rounded-lg hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Limpar Filtros</span>
          </button>
        </div>
      </form>
    </div>
  );
}
