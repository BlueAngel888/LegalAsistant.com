CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  content TEXT,
  file_type TEXT,
  file_size INTEGER,
  file_path TEXT,
  document_type TEXT,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documents_user_id ON documents (user_id);
CREATE INDEX idx_documents_status ON documents (status);
CREATE INDEX idx_documents_created_at ON documents (created_at);
CREATE INDEX idx_documents_user_id_created_at ON documents (user_id, created_at);

ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own documents"
  ON documents FOR SELECT
  USING (auth.uid()::text = (SELECT clerk_id FROM users WHERE users.id = documents.user_id));

CREATE POLICY "Users can create their own documents"
  ON documents FOR INSERT
  WITH CHECK (auth.uid()::text = (SELECT clerk_id FROM users WHERE users.id = documents.user_id));

CREATE POLICY "Users can update their own documents"
  ON documents FOR UPDATE
  USING (auth.uid()::text = (SELECT clerk_id FROM users WHERE users.id = documents.user_id));

CREATE POLICY "Users can delete their own documents"
  ON documents FOR DELETE
  USING (auth.uid()::text = (SELECT clerk_id FROM users WHERE users.id = documents.user_id));
