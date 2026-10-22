import { NextResponse } from "next/server";
import { supabase, isSupabaseConfigured } from "@/lib/supabaseClient";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { nome, telefone_whatsapp, palavras_chave, municipio_base, raio_km } = body;

    if (!nome || !telefone_whatsapp || !palavras_chave || palavras_chave.length === 0) {
      return NextResponse.json(
        { error: "Nome, WhatsApp e palavras-chave são obrigatórios." },
        { status: 400 }
      );
    }

    const telLimpo = telefone_whatsapp.replace(/\D/g, "");

    // Se o Supabase estiver conectado
    if (isSupabaseConfigured && supabase) {
      // 1. Cria ou atualiza o usuário
      const { data: usuario, error: userError } = await supabase
        .from("usuarios")
        .upsert(
          {
            nome,
            telefone_whatsapp: telLimpo,
            plano_ativo: true
          },
          { onConflict: "telefone_whatsapp" }
        )
        .select()
        .single();

      if (userError) {
        console.error("Erro ao salvar usuário:", userError);
      }

      const usuarioId = usuario?.id;

      // 2. Cria o alerta
      if (usuarioId) {
        const { data: alerta, error: alertaError } = await supabase
          .from("alertas")
          .insert({
            usuario_id: usuarioId,
            palavras_chave,
            municipio_base: municipio_base || "Não especificado",
            raio_km: raio_km || 50,
            ativo: true
          })
          .select()
          .single();

        if (alertaError) {
          console.error("Erro ao criar alerta:", alertaError);
        }
      }
    }

    return NextResponse.json({
      success: true,
      message: `Alerta para ${nome} cadastrado com sucesso! Notificações ativas para o WhatsApp ${telLimpo}.`
    });
  } catch (error: unknown) {
    console.error("Erro no cadastro de alerta:", error);
    return NextResponse.json(
      { error: "Erro interno ao cadastrar alerta." },
      { status: 500 }
    );
  }
}
