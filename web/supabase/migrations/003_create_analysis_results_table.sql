-- Create analysis_results table
CREATE TABLE IF NOT EXISTS analysis_results (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  jurisdiction VARCHAR(20) NOT NULL,
  document_type VARCHAR(50) NOT NULL,
  language VARCHAR(10) DEFAULT 'en',
  strengths TEXT[] DEFAULT ARRAY[]::TEXT[],
  weaknesses TEXT[] DEFAULT ARRAY[]::TEXT[],
  legal_errors TEXT[] DEFAULT ARRAY[]::TEXT[],
  defense_strategy TEXT[] DEFAULT ARRAY[]::TEXT[],
  risk_level VARCHAR(20) NOT NULL,
  summary TEXT NOT NULL,
  recommendations TEXT[] DEFAULT ARRAY[]::TEXT[],
  cached_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_analysis_results_document_id (document_id),
  INDEX idx_analysis_results_user_id (user_id),
  INDEX idx_analysis_results_created_at (created_at),
  INDEX idx_analysis_results_risk_level (risk_level)
);

-- Add RLS policies
ALTER TABLE analysis_results ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own analysis results"
  ON analysis_results FOR SELECT
  USING (user_id = (SELECT id FROM users WHERE clerk_id = auth.uid()::text LIMIT 1));

CREATE POLICY "Users can create analysis results"
  ON analysis_results FOR INSERT
  WITH CHECK (user_id = (SELECT id FROM users WHERE clerk_id = auth.uid()::text LIMIT 1));

CREATE POLICY "Users can update their own analysis results"
  ON analysis_results FOR UPDATE
  USING (user_id = (SELECT id FROM users WHERE clerk_id = auth.uid()::text LIMIT 1));

CREATE POLICY "Users can delete their own analysis results"
  ON analysis_results FOR DELETE
  USING (user_id = (SELECT id FROM users WHERE clerk_id = auth.uid()::text LIMIT 1));
