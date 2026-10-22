"use client";

import React, { useState } from "react";
import { X, BellRing, CheckCircle2, Phone, User, Tag, MapPin, Compass } from "lucide-react";

interface AlertaModalProps {
  isOpen: boolean;
  onClose: () => void;
  termoInicial?: string;
}

export function AlertaModal({ isOpen, onClose, termoInicial }: AlertaModalProps) {
  const [nome, setNome] = useState("");
  const [whatsapp, setWhatsapp] = useState("");
  const [palavraAtual, setPalavraAtual] = useState(termoInicial || "");
  const [palavrasChave, setPalavrasChave] = useState<string[]>(
    termoInicial ? [termoInicial] : ["material hospitalar", "engenharia"]
  );
  const [municipio, setMunicipio] = useState("");
  const [raioKm, setRaioKm] = useState<number>(50);
  const [enviando, setEnviando] = useState(false);
  const [sucesso, setSucesso] = useState(false);
  const [mensagemSucesso, setMensagemSucesso] = useState("");
  const [erro, setErro] = useState("");

  if (!isOpen) return null;

  const handleAddPalavra = () => {
    if (palavraAtual.trim() && !palavrasChave.includes(palavraAtual.trim())) {
      setPalavrasChave([...palavrasChave, palavraAtual.trim()]);
      setPalavraAtual("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      handleAddPalavra();
    }
  };

  const handleRemovePalavra = (palavra: string) => {
    setPalavrasChave(palavrasChave.filter((p) => p !== palavra));
  };

  const formatarWhatsapp = (valor: string) => {
    const numeros = valor.replace(/\D/g, "").slice(0, 11);
    if (numeros.length <= 2) return numeros;
    if (numeros.length <= 7) return `(${numeros.slice(0, 2)}) ${numeros.slice(2)}`;
    return `(${numeros.slice(0, 2)}) ${numeros.slice(2, 7)}-${numeros.slice(7)}`;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErro("");

    if (!nome.trim()) {
      setErro("Informe o seu nome completo.");
      return;
    }
    if (whatsapp.replace(/\D/g, "").length < 10) {
      setErro("Informe um número de WhatsApp válido com DDD.");
      return;
    }
    if (palavrasChave.length === 0) {
      setErro("Adicione ao menos uma palavra-chave para o radar.");
      return;
    }

    setEnviando(true);

    try {
      const response = await fetch("/api/alertas", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nome: nome.trim(),
          telefone_whatsapp: whatsapp,
          palavras_chave: palavrasChave,
          municipio_base: municipio.trim() || "Brasil",
          raio_km: raioKm
        })
      });

      const data = await response.json();

      if (response.ok) {
        setSucesso(true);
        setMensagemSucesso(data.message || "Radar de Licitações ativado com sucesso!");
      } else {
        setErro(data.error || "Ocorreu um erro ao salvar seu alerta.");
      }
    } catch {
      setErro("Falha na comunicação com o servidor.");
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-lg bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl shadow-emerald-950/20">
        {/* Botão Fechar */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
        >
          <X className="h-5 w-5" />
        </button>

        {sucesso ? (
          <div className="text-center py-6 space-y-4">
            <div className="h-16 w-16 mx-auto rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <CheckCircle2 className="h-9 w-9" />
            </div>
            <h3 className="text-xl font-bold text-white">Radar de Licitações Ativo!</h3>
            <p className="text-sm text-slate-300 leading-relaxed">
              {mensagemSucesso}
            </p>
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-400">
              Você receberá mensagens diárias no WhatsApp às <strong>12:00</strong> e <strong>18:00</strong> sempre que novos editais correspondentes forem publicados.
            </div>
            <button
              onClick={onClose}
              className="w-full py-3 rounded-xl bg-emerald-500 text-slate-950 font-bold text-sm hover:bg-emerald-400 transition-colors cursor-pointer"
            >
              Concluir
            </button>
          </div>
        ) : (
          <div>
            {/* Cabeçalho */}
            <div className="flex items-center gap-3 mb-6">
              <div className="h-10 w-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                <BellRing className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Criar Alerta no WhatsApp</h3>
                <p className="text-xs text-slate-400">
                  Receba editais em tempo real conforme palavras-chave e localização
                </p>
              </div>
            </div>

            {erro && (
              <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs">
                {erro}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Nome */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Seu Nome ou Empresa
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                  <input
                    type="text"
                    required
                    placeholder="Ex: Carlos Silva ou Construtora Alfa"
                    value={nome}
                    onChange={(e) => setNome(e.target.value)}
                    className="w-full pl-9 pr-3 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
              </div>

              {/* WhatsApp */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Número de WhatsApp
                </label>
                <div className="relative">
                  <Phone className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                  <input
                    type="text"
                    required
                    placeholder="(11) 98765-4321"
                    value={whatsapp}
                    onChange={(e) => setWhatsapp(formatarWhatsapp(e.target.value))}
                    className="w-full pl-9 pr-3 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
              </div>

              {/* Palavras-chave */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Palavras-chave de Interesse (pressione Enter para adicionar)
                </label>
                <div className="relative mb-2">
                  <Tag className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                  <input
                    type="text"
                    placeholder="Ex: uniforme, medicamento, software, pintura..."
                    value={palavraAtual}
                    onChange={(e) => setPalavraAtual(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className="w-full pl-9 pr-20 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                  <button
                    type="button"
                    onClick={handleAddPalavra}
                    className="absolute right-2 top-2 px-3 py-1 bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 rounded-lg"
                  >
                    Adicionar
                  </button>
                </div>

                <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
                  {palavrasChave.map((palavra) => (
                    <span
                      key={palavra}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium"
                    >
                      {palavra}
                      <button
                        type="button"
                        onClick={() => handleRemovePalavra(palavra)}
                        className="hover:text-red-400"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              {/* Município Base e Raio KM */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Município Base
                  </label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                    <input
                      type="text"
                      placeholder="Ex: Campinas"
                      value={municipio}
                      onChange={(e) => setMunicipio(e.target.value)}
                      className="w-full pl-9 pr-3 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="text-xs font-semibold text-slate-300 flex items-center gap-1">
                      <Compass className="h-3 w-3 text-slate-400" /> Raio Geográfico
                    </label>
                    <span className="text-xs font-bold text-emerald-400">{raioKm} km</span>
                  </div>
                  <input
                    type="range"
                    min="10"
                    max="500"
                    step="10"
                    value={raioKm}
                    onChange={(e) => setRaioKm(parseInt(e.target.value))}
                    className="w-full accent-emerald-500 h-2 bg-slate-800 rounded-lg cursor-pointer mt-3"
                  />
                </div>
              </div>

              <div className="pt-3">
                <button
                  type="submit"
                  disabled={enviando}
                  className="w-full py-3.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 font-bold text-sm shadow-lg shadow-emerald-500/20 hover:from-emerald-400 hover:to-teal-400 transition-all cursor-pointer active:scale-95 disabled:opacity-50"
                >
                  {enviando ? "Ativando Alertas..." : "Ativar Radar no WhatsApp"}
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
