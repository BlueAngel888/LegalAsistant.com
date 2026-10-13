-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  file_name TEXT NOT NULL,
  file_size INTEGER NOT NULL,
  file_type TEXT NOT NULL,
  document_type VARCHAR(50) NOT NULL,
  jurisdiction VARCHAR(20),
  language VARCHAR(10) DEFAULT 'en',
  content TEXT,
  status VARCHAR(20) DEFAULT 'PENDING',
  uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_documents_user_id (user_id),
  INDEX idx_documents_status (status),
  INDEX idx_documents_created_at (created_at)
);

-- Add RLS policies
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own documents"
  ON documents FOR SELECT
  USING (user_id = (SELECT id FROM users WHERE clerk_id = auth.uid()::text LIMIT 1));

CREATE POLICY "Users can create documents"
  ON documents FOR INSERT
  WITH CHECK (user_id = (SELECT id FROM users WHERE clerk_id = auth.uid()::text LIMIT 1));

CREATE POLICY "Users can update their own documents"
  ON documents FOR UPDATE
  USING (user_id = (SELECT id FROM users WHERE clerk_id = auth.uid()::text LIMIT 1));

CREATE POLICY "Users can delete their own documents"
  ON documents FOR DELETE
  USING (user_id = (SELECT id FROM users WHERE clerk_id = auth.uid()::text LIMIT 1));
