"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/Header";
import { Filtros } from "@/components/Filtros";
import { LicitacaoCard } from "@/components/LicitacaoCard";
import { TabelaLicitacoes } from "@/components/TabelaLicitacoes";
import { AlertaModal } from "@/components/AlertaModal";
import { Licitacao, FiltrosLicitacao, PlacarDoDia } from "@/lib/types";
import { 
  BellRing, 
  Shield, 
  Sparkles, 
  Database, 
  Layers, 
  ArrowRight, 
  LayoutGrid, 
  Table, 
  Download,
  CalendarCheck
} from "lucide-react";

export default function Home() {
  const [licitacoes, setLicitacoes] = useState<Licitacao[]>([]);
  const [placar, setPlacar] = useState<PlacarDoDia>({
    totalLicitacoes: 0,
    totalResultados: 0,
    totalCotacoes: 0,
    totalValor: 0
  });
  const [carregando, setCarregando] = useState(true);
  const [modalAlertaAberto, setModalAlertaAberto] = useState(false);
  const [termoAlertaInicial, setTermoAlertaInicial] = useState("");
  const [origemDados, setOrigemDados] = useState<string>("carregando");
  const [modoVisualizacao, setModoVisualizacao] = useState<"cards" | "tabela">("cards");

  const [filtros, setFiltros] = useState<FiltrosLicitacao>({
    busca: "",
    estado: "",
    regiao: "",
    modalidade: "",
    esfera: "",
    tipoPublicacao: "TODOS",
    periodoAgenda: "todos",
    municipio: "",
    valorMin: undefined,
    valorMax: undefined,
    fonte: "",
    ordenacao: "disputa_asc"
  });

  const buscarLicitacoes = useCallback(async () => {
    setCarregando(true);
    try {
      const params = new URLSearchParams();
      if (filtros.busca) params.append("busca", filtros.busca);
      if (filtros.estado) params.append("estado", filtros.estado);
      if (filtros.regiao) params.append("regiao", filtros.regiao);
      if (filtros.modalidade) params.append("modalidade", filtros.modalidade);
      if (filtros.esfera) params.append("esfera", filtros.esfera);
      if (filtros.tipoPublicacao) params.append("tipoPublicacao", filtros.tipoPublicacao);
      if (filtros.periodoAgenda) params.append("periodoAgenda", filtros.periodoAgenda);
      if (filtros.municipio) params.append("municipio", filtros.municipio);
      if (filtros.valorMin) params.append("valorMin", filtros.valorMin.toString());
      if (filtros.valorMax) params.append("valorMax", filtros.valorMax.toString());
      if (filtros.fonte) params.append("fonte", filtros.fonte);
      if (filtros.ordenacao) params.append("ordenacao", filtros.ordenacao);

      const resp = await fetch(`/api/licitacoes?${params.toString()}`);
      const data = await resp.json();
      setLicitacoes(data.licitacoes || []);
      if (data.placar) {
        setPlacar(data.placar);
      }
      setOrigemDados(data.origem || "api");
    } catch (err) {
      console.error("Erro ao buscar licitações:", err);
    } finally {
      setCarregando(false);
    }
  }, [filtros]);

  useEffect(() => {
    buscarLicitacoes();
  }, [buscarLicitacoes]);

  const handleLimparFiltros = () => {
    setFiltros({
      busca: "",
      estado: "",
      regiao: "",
      modalidade: "",
      esfera: "",
      tipoPublicacao: "TODOS",
      periodoAgenda: "todos",
      municipio: "",
      valorMin: undefined,
      valorMax: undefined,
      fonte: "",
      ordenacao: "disputa_asc"
    });
  };

  const handleCriarAlertaDoTermo = (termo: string) => {
    setTermoAlertaInicial(termo);
    setModalAlertaAberto(true);
  };

  const exportarCSV = () => {
    if (licitacoes.length === 0) return;
    const cabecalho = ["UF", "Município", "Órgão", "Modalidade", "Processo", "Objeto", "Valor Estimado", "Data Disputa", "Link Edital"];
    const linhas = licitacoes.map((item) => [
      `"${item.estado}"`,
      `"${item.municipio}"`,
      `"${item.orgao.replace(/"/g, '""')}"`,
      `"${item.modalidade || ""}"`,
      `"${item.numero_processo || ""}"`,
      `"${item.objeto.replace(/"/g, '""')}"`,
      `"${item.valor_estimado || 0}"`,
      `"${item.data_disputa || ""}"`,
      `"${item.link_edital || ""}"`
    ]);

    const csvContent = "\uFEFF" + [cabecalho.join(";"), ...linhas.map((e) => e.join(";"))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `boletim_licitacoes_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col selection:bg-emerald-500 selection:text-slate-950">
      {/* Header com Placar do Dia (Universo Licitações Style) */}
      <Header
        onOpenAlertaModal={() => {
          setTermoAlertaInicial("");
          setModalAlertaAberto(true);
        }}
        placar={placar}
      />

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-8 pb-6 sm:pt-12 sm:pb-8 border-b border-slate-900 bg-gradient-to-b from-slate-900/50 via-slate-950 to-slate-950">
        <div className="absolute inset-0 bg-[radial-gradient(#10b98115_1px,transparent_1px)] [background-size:24px_24px] pointer-events-none" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold mb-3">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Busca por Radical &amp; Agregação Nacional de Editais</span>
            </div>
            <h1 className="text-2xl sm:text-4xl lg:text-5xl font-black text-white tracking-tight leading-tight">
              Portal e Radar Ativo de{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">
                Licitações Públicas
              </span>
            </h1>
            <p className="mt-3 text-sm sm:text-base text-slate-400 leading-relaxed">
              Mecanismo avançado inspirado no Universo Licitações: pesquisa semântica por radical da palavra, 
              cobertura nacional com foco em <strong>MA, PA, TO</strong> e todas as UFs, monitoramento de 
              <strong> Avisos, Resultados e Cotações</strong> com alertas ativos no WhatsApp.
            </p>

            <div className="mt-5 flex flex-wrap gap-4 text-xs font-medium text-slate-300">
              <div className="flex items-center gap-1.5">
                <Database className="h-4 w-4 text-emerald-400" />
                <span>PNCP &amp; Diários Oficiais</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Layers className="h-4 w-4 text-teal-400" />
                <span>Geolocalização PostGIS</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CalendarCheck className="h-4 w-4 text-cyan-400" />
                <span>Agenda de Disputas em Tempo Real</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Conteúdo Principal */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex-1 w-full space-y-5">
        {/* Painel de Filtros Avançados */}
        <Filtros
          filtros={filtros}
          onChangeFiltros={setFiltros}
          onBuscar={buscarLicitacoes}
          onLimpar={handleLimparFiltros}
          carregando={carregando}
        />

        {/* Barra de Controles de Exibição e Exportação */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
          <div className="flex items-center gap-2">
            <h2 className="text-base sm:text-lg font-bold text-white">Editais Encontrados</h2>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-800 text-emerald-400 border border-slate-700">
              {licitacoes.length} registros
            </span>
          </div>

          <div className="flex items-center gap-3">
            {/* Alternador de Modo Cards / Tabela */}
            <div className="flex items-center bg-slate-900 border border-slate-800 rounded-xl p-1 text-xs">
              <button
                type="button"
                onClick={() => setModoVisualizacao("cards")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                  modoVisualizacao === "cards"
                    ? "bg-slate-800 text-emerald-400 font-bold shadow"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                <LayoutGrid className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Cards</span>
              </button>

              <button
                type="button"
                onClick={() => setModoVisualizacao("tabela")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                  modoVisualizacao === "tabela"
                    ? "bg-slate-800 text-emerald-400 font-bold shadow"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                <Table className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Tabela Gerencial</span>
              </button>
            </div>

            {/* Exportar Boletim CSV */}
            <button
              type="button"
              onClick={exportarCSV}
              disabled={licitacoes.length === 0}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs font-semibold text-slate-300 hover:text-white transition-all disabled:opacity-40 cursor-pointer"
              title="Baixar Boletim em formato CSV"
            >
              <Download className="h-3.5 w-3.5 text-emerald-400" />
              <span className="hidden sm:inline">Exportar Boletim</span>
            </button>
          </div>
        </div>

        {/* Listagem de Resultados */}
        {carregando ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {[1, 2, 3, 4, 5, 6].map((idx) => (
              <div
                key={idx}
                className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5 space-y-4 animate-pulse"
              >
                <div className="flex justify-between">
                  <div className="h-5 bg-slate-800 rounded w-28" />
                  <div className="h-5 bg-slate-800 rounded w-20" />
                </div>
                <div className="h-4 bg-slate-800 rounded w-3/4" />
                <div className="space-y-2">
                  <div className="h-3 bg-slate-800/60 rounded" />
                  <div className="h-3 bg-slate-800/60 rounded" />
                  <div className="h-3 bg-slate-800/60 rounded w-5/6" />
                </div>
                <div className="h-14 bg-slate-950/80 rounded-xl" />
                <div className="h-9 bg-slate-800 rounded-lg" />
              </div>
            ))}
          </div>
        ) : licitacoes.length === 0 ? (
          <div className="text-center py-16 bg-slate-900/30 border border-slate-800/50 rounded-3xl p-8 space-y-4">
            <div className="h-16 w-16 mx-auto rounded-2xl bg-slate-800/80 flex items-center justify-center text-slate-400">
              <Shield className="h-8 w-8" />
            </div>
            <h3 className="text-lg font-bold text-white">Nenhum edital encontrado</h3>
            <p className="text-sm text-slate-400 max-w-md mx-auto">
              Tente termos mais amplos, altere a modalidade ou limpe os filtros para visualizar mais resultados.
            </p>
            <button
              onClick={handleLimparFiltros}
              className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-sm font-semibold text-white transition-colors cursor-pointer"
            >
              Limpar Filtros
            </button>
          </div>
        ) : modoVisualizacao === "tabela" ? (
          <TabelaLicitacoes
            licitacoes={licitacoes}
            onCriarAlertaDoTermo={handleCriarAlertaDoTermo}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {licitacoes.map((item) => (
              <LicitacaoCard
                key={item.id}
                licitacao={item}
                onCriarAlertaDoTermo={handleCriarAlertaDoTermo}
              />
            ))}
          </div>
        )}

        {/* Banner CTA Inferior de Alerta Ativo */}
        <section className="mt-10 rounded-3xl p-6 sm:p-8 bg-gradient-to-r from-emerald-950/40 via-slate-900 to-teal-950/40 border border-emerald-500/20 shadow-2xl flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="space-y-2 text-center md:text-left">
            <h3 className="text-xl sm:text-2xl font-bold text-white">
              Automatize o recebimento de editais no WhatsApp
            </h3>
            <p className="text-sm text-slate-300 max-w-xl">
              Nosso sistema cruza as publicações do PNCP e Diários Oficiais com as suas palavras-chave e dispara relatórios diários às 12:00 e 18:00 (Brasília).
            </p>
          </div>
          <button
            onClick={() => {
              setTermoAlertaInicial("");
              setModalAlertaAberto(true);
            }}
            className="shrink-0 flex items-center gap-2 px-6 py-3.5 rounded-xl bg-emerald-500 text-slate-950 font-bold text-sm shadow-xl shadow-emerald-500/25 hover:bg-emerald-400 transition-all cursor-pointer active:scale-95"
          >
            <BellRing className="h-4 w-4 stroke-[2.5]" />
            <span>Ativar Radar no WhatsApp</span>
            <ArrowRight className="h-4 w-4" />
          </button>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-8 text-center text-xs text-slate-500">
        <p>Radar Licitações &copy; 2026 - Plataforma de Inteligência e Monitoramento de Contratações Públicas.</p>
        <p className="mt-1 text-slate-600">Integrado ao PNCP e Diários Oficiais com inteligência artificial e geolocalização PostGIS.</p>
      </footer>

      {/* Modal de Alerta */}
      <AlertaModal
        isOpen={modalAlertaAberto}
        onClose={() => setModalAlertaAberto(false)}
        termoInicial={termoAlertaInicial}
      />
    </div>
  );
}
