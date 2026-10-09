CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS legal_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    blob_url VARCHAR(1024) NOT NULL, 
    document_type VARCHAR(100),
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_legal_documents_title_trgm 
ON legal_documents USING GIN (title gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_legal_documents_embedding_hnsw 
ON legal_documents USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS legal_acts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(512) NOT NULL,
    signature VARCHAR(100),
    publication_date DATE,
    status VARCHAR(50) DEFAULT 'obowiazujacy',
    blob_url VARCHAR(1024),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS legal_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    act_id UUID REFERENCES legal_acts(id) ON DELETE CASCADE,
    article_number VARCHAR(50) NOT NULL,
    paragraph VARCHAR(50),
    content TEXT NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_legal_chunks_act_id 
ON legal_chunks(act_id);

CREATE INDEX IF NOT EXISTS idx_legal_chunks_article_number 
ON legal_chunks(article_number);

CREATE INDEX IF NOT EXISTS idx_legal_chunks_content_trgm 
ON legal_chunks USING GIN (content gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_legal_chunks_embedding_hnsw 
ON legal_chunks USING hnsw (embedding vector_cosine_ops);
