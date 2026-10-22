-- ============================================================================
-- 1. EXTENSÕES OBRIGATÓRIAS
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================================
-- 2. TABELA: licitacoes (Criação ou Migração de Colunas Existentes)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.licitacoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    orgao TEXT,
    objeto TEXT,
    valor_estimado NUMERIC(15, 2),
    data_disputa TIMESTAMPTZ,
    link_edital TEXT,
    municipio VARCHAR(100),
    estado VARCHAR(2),
    modalidade VARCHAR(100) DEFAULT 'Pregão Eletrônico',
    regiao VARCHAR(30) DEFAULT 'Sudeste',
    esfera VARCHAR(30) DEFAULT 'Municipal',
    tipo_publicacao VARCHAR(50) DEFAULT 'AVISO',
    numero_processo VARCHAR(100),
    coordenadas GEOGRAPHY(Point, 4326),
    fonte VARCHAR(50) DEFAULT 'PNCP',
    id_externo VARCHAR(255) UNIQUE,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('America/Sao_Paulo', NOW()),
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('America/Sao_Paulo', NOW())
);

-- Migração resiliente: Adiciona colunas que possam faltar se a tabela já existia previamente
ALTER TABLE public.licitacoes ADD COLUMN IF NOT EXISTS orgao TEXT;
ALTER TABLE public.licitacoes ADD COLUMN IF NOT EXISTS objeto TEXT;
ALTER TABLE public.licitacoes ADD COLUMN IF NOT EXISTS valor_estimado NUMERIC(15, 2);
ALTER TABLE public.licitacoes ADD COLUMN IF NOT EXISTS data_disputa TIMESTAMPTZ;
ALTER TABLE public.licitacoes ADD COLUMN IF NOT EXISTS link_edital TEXT;
ALTER TABLE public.licitacoes ADD COLUMN IF NOT EXISTS municipio VARCHAR(100);
ALTER TABLE public.licitacoes ADD COLUMN IF NOT EXISTS estado VARCHAR(2);
ALTER TABLE public.licitacoes ADD COLUMN IF NOT EXISTS modalidade VARCHAR(100) DEFAULT 'Pregão Eletrônico';
ALTER TABLE public.licitacoes ADD COLUMN IF NOT EXISTS regiao VARCHAR(30) DEFAULT 'Sudeste';
ALTER TABLE public.licitacoes ADD COLUMN IF NOT EXISTS esfera VARCHAR(30) DEFAULT 'Municipal';
ALTER TABLE public.licitacoes ADD COLUMN IF NOT EXISTS tipo_publicacao VARCHAR(50) DEFAULT 'AVISO';
ALTER TABLE public.licitacoes ADD COLUMN IF NOT EXISTS numero_processo VARCHAR(100);
ALTER TABLE public.licitacoes ADD COLUMN IF NOT EXISTS coordenadas GEOGRAPHY(Point, 4326);
ALTER TABLE public.licitacoes ADD COLUMN IF NOT EXISTS fonte VARCHAR(50) DEFAULT 'PNCP';
ALTER TABLE public.licitacoes ADD COLUMN IF NOT EXISTS id_externo VARCHAR(255);
ALTER TABLE public.licitacoes ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT TIMEZONE('America/Sao_Paulo', NOW());
ALTER TABLE public.licitacoes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT TIMEZONE('America/Sao_Paulo', NOW());

-- Garante constraint UNIQUE em id_externo para upsert sem duplicação
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'licitacoes_id_externo_key'
    ) THEN
        ALTER TABLE public.licitacoes ADD CONSTRAINT licitacoes_id_externo_key UNIQUE (id_externo);
    END IF;
EXCEPTION
    WHEN OTHERS THEN NULL;
END $$;

-- Índices de alta performance
CREATE INDEX IF NOT EXISTS idx_licitacoes_coordenadas ON public.licitacoes USING GIST (coordenadas);
CREATE INDEX IF NOT EXISTS idx_licitacoes_estado_municipio ON public.licitacoes (estado, municipio);
CREATE INDEX IF NOT EXISTS idx_licitacoes_data_disputa ON public.licitacoes (data_disputa);

-- ============================================================================
-- 3. TABELA: usuarios
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome VARCHAR(255) NOT NULL,
    telefone_whatsapp VARCHAR(20) NOT NULL,
    plano_ativo BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('America/Sao_Paulo', NOW()),
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('America/Sao_Paulo', NOW())
);

ALTER TABLE public.usuarios ADD COLUMN IF NOT EXISTS telefone_whatsapp VARCHAR(20);
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'usuarios_telefone_whatsapp_key'
    ) THEN
        ALTER TABLE public.usuarios ADD CONSTRAINT usuarios_telefone_whatsapp_key UNIQUE (telefone_whatsapp);
    END IF;
EXCEPTION
    WHEN OTHERS THEN NULL;
END $$;

-- ============================================================================
-- 4. TABELA: alertas
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

-- ============================================================================
-- 5. POLÍTICAS DE SEGURANÇA (Row Level Security - RLS)
-- ============================================================================
ALTER TABLE public.licitacoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alertas ENABLE ROW LEVEL SECURITY;

-- Remove políticas anteriores para evitar duplicidades
DROP POLICY IF EXISTS "Leitura pública de licitações" ON public.licitacoes;
DROP POLICY IF EXISTS "Permitir importação de licitações" ON public.licitacoes;
DROP POLICY IF EXISTS "Acesso público a usuários" ON public.usuarios;
DROP POLICY IF EXISTS "Acesso público a alertas" ON public.alertas;

-- Política 1: Leitura pública universal
CREATE POLICY "Leitura pública de licitações" 
ON public.licitacoes FOR SELECT 
USING (true);

-- Política 2: Permite inserção e atualização de editais pelos coletores e APIs
CREATE POLICY "Permitir importação de licitações" 
ON public.licitacoes FOR ALL 
USING (true)
WITH CHECK (true);

-- Política 3: Cadastro e gerenciamento de alertas pelo WhatsApp
CREATE POLICY "Acesso público a usuários" 
ON public.usuarios FOR ALL 
USING (true)
WITH CHECK (true);

CREATE POLICY "Acesso público a alertas" 
ON public.alertas FOR ALL 
USING (true)
WITH CHECK (true);
