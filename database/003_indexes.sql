-- Performance Indexes
-- Run after 001 and 002 to optimize queries

-- EOD Reports indexes
CREATE INDEX IF NOT EXISTS eod_reports_date_idx ON eod_reports (report_date DESC);
CREATE INDEX IF NOT EXISTS eod_reports_health_idx ON eod_reports (overall_health);
CREATE INDEX IF NOT EXISTS eod_reports_folder_idx ON eod_reports (folder_id);
CREATE INDEX IF NOT EXISTS eod_reports_processed_idx ON eod_reports (processed_at DESC);

-- Action Items indexes
CREATE INDEX IF NOT EXISTS action_items_status_idx ON action_items (status);
CREATE INDEX IF NOT EXISTS action_items_priority_idx ON action_items (priority);
CREATE INDEX IF NOT EXISTS action_items_due_date_idx ON action_items (due_date);
CREATE INDEX IF NOT EXISTS action_items_owner_idx ON action_items (owner);
CREATE INDEX IF NOT EXISTS action_items_eod_idx ON action_items (eod_report_id);
CREATE INDEX IF NOT EXISTS action_items_channels_idx ON action_items USING GIN (channels);

-- Infra Events indexes
CREATE INDEX IF NOT EXISTS infra_events_severity_idx ON infra_events (severity);
CREATE INDEX IF NOT EXISTS infra_events_status_idx ON infra_events (status);
CREATE INDEX IF NOT EXISTS infra_events_service_idx ON infra_events (service);
CREATE INDEX IF NOT EXISTS infra_events_created_idx ON infra_events (created_at DESC);

-- Sentiment Log indexes
CREATE INDEX IF NOT EXISTS sentiment_log_date_idx ON sentiment_log (report_date DESC);
CREATE INDEX IF NOT EXISTS sentiment_log_patterns_idx ON sentiment_log USING GIN (patterns);

-- Morning Briefs indexes
CREATE INDEX IF NOT EXISTS morning_briefs_date_idx ON morning_briefs (brief_date DESC);

COMMENT ON INDEX eod_reports_date_idx IS 'Fast lookups by report date';
COMMENT ON INDEX action_items_status_idx IS 'Filter active vs completed items';
COMMENT ON INDEX infra_events_severity_idx IS 'Quick critical issue queries';
