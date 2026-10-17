-- Legal basis per point (points are stored as JSON objects), the legislation
-- applied, public information, and for UK analyses the service niche and the
-- legal limits that applied.
ALTER TABLE analysis_results
  ADD COLUMN IF NOT EXISTS legal_framework JSONB DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS public_info JSONB DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS uk_niche TEXT,
  ADD COLUMN IF NOT EXISTS legal_limits JSONB DEFAULT '[]'::jsonb;
