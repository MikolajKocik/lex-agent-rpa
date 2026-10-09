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
