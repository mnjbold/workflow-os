-- workflow_os Core Tables
-- Run this first to establish the base schema

-- EOD reports received from Google Docs
CREATE TABLE IF NOT EXISTS eod_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  doc_id TEXT,
  folder_id TEXT,
  raw_content TEXT,
  parsed_json JSONB,
  enriched_json JSONB,
  overall_health TEXT CHECK (overall_health IN ('green', 'amber', 'red')),
  report_date DATE,
  processed_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Action items extracted from EOD reports
CREATE TABLE IF NOT EXISTS action_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  eod_report_id UUID REFERENCES eod_reports(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  owner TEXT,
  priority TEXT CHECK (priority IN ('P0','P1','P2','P3','P4')),
  due_date DATE,
  channels TEXT[],  -- ['slack', 'calendar', 'email', 'github']
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending','dispatched','completed','cancelled')),
  dispatch_results JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

-- Infrastructure events and errors
CREATE TABLE IF NOT EXISTS infra_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  eod_report_id UUID REFERENCES eod_reports(id) ON DELETE SET NULL,
  service TEXT,
  error_type TEXT,
  error_message TEXT,
  severity TEXT CHECK (severity IN ('critical','high','medium','low')),
  github_issue_number INT,
  github_issue_url TEXT,
  occurrence_count INT DEFAULT 1,
  status TEXT DEFAULT 'open',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sentiment tracking for team health monitoring
CREATE TABLE IF NOT EXISTS sentiment_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  eod_report_id UUID REFERENCES eod_reports(id) ON DELETE CASCADE,
  report_date DATE,
  tone TEXT,
  patterns TEXT[],
  compliance_flags TEXT[],
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Morning brief history
CREATE TABLE IF NOT EXISTS morning_briefs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brief_date DATE UNIQUE NOT NULL,
  content TEXT,
  pending_items INT,
  completed_yesterday INT,
  health_status TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE eod_reports IS 'Stores all EOD reports from Google Drive folder';
COMMENT ON TABLE action_items IS 'Actionable items extracted from EOD reports, dispatched to various channels';
COMMENT ON TABLE infra_events IS 'Infrastructure errors and issues, with GitHub issue tracking';
COMMENT ON TABLE sentiment_log IS 'Team sentiment analysis from EOD reports';
COMMENT ON TABLE morning_briefs IS 'Generated morning briefings sent to stakeholders';
