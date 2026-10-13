CREATE TABLE IF NOT EXISTS analysis_results (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  analysis_type TEXT NOT NULL,
  status TEXT DEFAULT 'pending',
  result JSONB,
  summary TEXT,
  key_findings TEXT,
  risks TEXT,
  recommendations TEXT,
  processing_time_ms INTEGER,
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_analysis_results_user_id ON analysis_results (user_id);
CREATE INDEX idx_analysis_results_document_id ON analysis_results (document_id);
CREATE INDEX idx_analysis_results_status ON analysis_results (status);
CREATE INDEX idx_analysis_results_created_at ON analysis_results (created_at);
CREATE INDEX idx_analysis_results_analysis_type ON analysis_results (analysis_type);
CREATE INDEX idx_analysis_results_user_id_created_at ON analysis_results (user_id, created_at);

ALTER TABLE analysis_results ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own analysis results"
  ON analysis_results FOR SELECT
  USING (auth.uid()::text = (SELECT clerk_id FROM users WHERE users.id = analysis_results.user_id));

CREATE POLICY "Users can create analysis results for their documents"
  ON analysis_results FOR INSERT
  WITH CHECK (auth.uid()::text = (SELECT clerk_id FROM users WHERE users.id = analysis_results.user_id));

CREATE POLICY "Users can update their own analysis results"
  ON analysis_results FOR UPDATE
  USING (auth.uid()::text = (SELECT clerk_id FROM users WHERE users.id = analysis_results.user_id));

CREATE POLICY "Users can delete their own analysis results"
  ON analysis_results FOR DELETE
  USING (auth.uid()::text = (SELECT clerk_id FROM users WHERE users.id = analysis_results.user_id));
