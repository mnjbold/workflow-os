-- pgvector Second Brain
-- Semantic search over decisions, commands, and architecture notes
-- Run after 001_workflow_os_tables.sql

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Second brain entries with semantic embeddings
CREATE TABLE IF NOT EXISTS second_brain (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  eod_report_id UUID REFERENCES eod_reports(id) ON DELETE SET NULL,
  entry_type TEXT CHECK (entry_type IN ('decision','command','note','architecture')),
  content TEXT NOT NULL,
  tags TEXT[],
  embedding vector(1536),  -- OpenAI text-embedding-3-small dimensions
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vector similarity search index (IVFFLAT for speed on large datasets)
-- Adjust lists parameter based on dataset size: sqrt(rows) is a good starting point
CREATE INDEX IF NOT EXISTS second_brain_embedding_idx 
  ON second_brain 
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- GIN index for tag-based filtering
CREATE INDEX IF NOT EXISTS second_brain_tags_idx 
  ON second_brain 
  USING GIN (tags);

-- Index for entry type filtering
CREATE INDEX IF NOT EXISTS second_brain_entry_type_idx 
  ON second_brain (entry_type);

COMMENT ON TABLE second_brain IS 'Semantic knowledge base with vector embeddings for RAG queries';
COMMENT ON COLUMN second_brain.embedding IS 'OpenAI text-embedding-3-small (1536 dimensions) for semantic search';
