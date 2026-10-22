-- ============================================================================
-- 1. EXTENSÕES OBRIGATÓRIAS
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================================
-- 2. TABELA: licitacoes
-- Armazena os editais agregados via PNCP, Diários Oficiais e outros portais
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.licitacoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    orgao TEXT NOT NULL,
    objeto TEXT NOT NULL,
    valor_estimado NUMERIC(15, 2),
    data_disputa TIMESTAMPTZ,
    link_edital TEXT,
    municipio VARCHAR(100) NOT NULL,
    estado VARCHAR(2) NOT NULL,
    -- Colunas inspiradas na arquitetura do Universo Licitações
    modalidade VARCHAR(100) DEFAULT 'Pregão Eletrônico',
    regiao VARCHAR(30) DEFAULT 'Sudeste',
    esfera VARCHAR(30) DEFAULT 'Municipal', -- 'Federal', 'Estadual', 'Municipal'
    tipo_publicacao VARCHAR(50) DEFAULT 'AVISO', -- 'AVISO', 'RESULTADO', 'AGENDA', 'COTACAO'
    numero_processo VARCHAR(100),
    -- Coordenadas espaciais usando PostGIS (WGS 84 - SRID 4326)
    -- geography(Point, 4326) calcula distâncias automaticamente em metros/km
    coordenadas GEOGRAPHY(Point, 4326),
    fonte VARCHAR(50) DEFAULT 'PNCP', -- 'PNCP', 'DIARIO_OFICIAL', etc.
    id_externo VARCHAR(255) UNIQUE,   -- Previne duplicação de editais já importados
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('America/Sao_Paulo', NOW()),
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('America/Sao_Paulo', NOW())
);

-- Índices de alta performance
CREATE INDEX IF NOT EXISTS idx_licitacoes_coordenadas ON public.licitacoes USING GIST (coordenadas);
CREATE INDEX IF NOT EXISTS idx_licitacoes_estado_municipio ON public.licitacoes (estado, municipio);
CREATE INDEX IF NOT EXISTS idx_licitacoes_data_disputa ON public.licitacoes (data_disputa);
CREATE INDEX IF NOT EXISTS idx_licitacoes_objeto_trgm ON public.licitacoes USING gin (to_tsvector('portuguese', objeto));

-- ============================================================================
-- 3. TABELA: usuarios
-- Dados cadastrais e controle de acesso aos alertas
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.usuarios (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    nome VARCHAR(255) NOT NULL,
    telefone_whatsapp VARCHAR(20) NOT NULL,
    plano_ativo BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('America/Sao_Paulo', NOW()),
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('America/Sao_Paulo', NOW())
);

-- ============================================================================
-- 4. TABELA: alertas
-- Critérios de notificação ativa configurados pelos usuários
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.alertas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES public.usuarios(id) ON DELETE CASCADE,
    palavras_chave TEXT[] NOT NULL DEFAULT '{}',
    raio_km INTEGER DEFAULT 50,
    municipio_base VARCHAR(100),
    coordenadas_base GEOGRAPHY(Point, 4326),
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('America/Sao_Paulo', NOW()),
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('America/Sao_Paulo', NOW())
);

CREATE INDEX IF NOT EXISTS idx_alertas_usuario ON public.alertas(usuario_id);
CREATE INDEX IF NOT EXISTS idx_alertas_coordenadas ON public.alertas USING GIST (coordenadas_base);

-- ============================================================================
-- 5. POLÍTICAS DE SEGURANÇA (Row Level Security - RLS)
-- ============================================================================
ALTER TABLE public.licitacoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alertas ENABLE ROW LEVEL SECURITY;

-- Licitações: Leitura pública para todos os usuários autenticados e anônimos
CREATE POLICY "Leitura pública de licitações" 
ON public.licitacoes FOR SELECT 
USING (true);

-- Usuários: Cada usuário só gerencia seu próprio perfil
CREATE POLICY "Usuários gerenciam seu próprio perfil" 
ON public.usuarios FOR ALL 
USING (auth.uid() = id);

-- Alertas: Cada usuário só visualiza e edita os seus próprios alertas
CREATE POLICY "Usuários gerenciam seus próprios alertas" 
ON public.alertas FOR ALL 
USING (auth.uid() = usuario_id);
