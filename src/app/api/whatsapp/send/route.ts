import { NextResponse } from "next/server";

export async function POST(request: Request) {
  try {
    const { numero, mensagem } = await request.json();

    if (!numero || !mensagem) {
      return NextResponse.json(
        { error: "Número e mensagem são obrigatórios." },
        { status: 400 }
      );
    }

    const whatsappApiUrl = process.env.WHATSAPP_API_URL;
    const whatsappApiKey = process.env.WHATSAPP_API_KEY;

    const numeroLimpo = numero.replace(/\D/g, "");

    // Se as credenciais do WhatsApp estiverem configuradas, envia via API REST
    if (whatsappApiUrl && whatsappApiKey && !whatsappApiUrl.includes("gateway.com")) {
      const resp = await fetch(whatsappApiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          apikey: whatsappApiKey,
          Authorization: `Bearer ${whatsappApiKey}`
        },
        body: JSON.stringify({
          number: numeroLimpo.startsWith("55") ? numeroLimpo : `55${numeroLimpo}`,
          text: mensagem,
          message: mensagem
        })
      });

      const data = await resp.json();
      return NextResponse.json({ success: true, apiResponse: data });
    }

    // Modo simulação para desenvolvimento local
    return NextResponse.json({
      success: true,
      simulado: true,
      destinatario: numeroLimpo,
      preview: mensagem,
      message: "Mensagem simulada com sucesso (configure WHATSAPP_API_KEY no .env para envios reais)."
    });
  } catch (err: unknown) {
    console.error("Erro no envio de WhatsApp:", err);
    return NextResponse.json(
      { error: "Erro interno no serviço de WhatsApp." },
      { status: 500 }
    );
  }
}
