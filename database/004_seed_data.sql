-- Seed Data
-- Initial configuration for Bold Business workflow_os

-- Insert initial project configuration as a special EOD entry
INSERT INTO eod_reports (
  doc_id,
  folder_id,
  raw_content,
  parsed_json,
  overall_health,
  report_date,
  processed_at
) VALUES (
  'SYSTEM_CONFIG',
  '1oTfpoAddnGArr6M2bLojsYtRc7_Hd7QM',
  'Initial system configuration for Bold Business workflow_os',
  jsonb_build_object(
    'project', 'bold-amplify-ats',
    'folder_id', '1oTfpoAddnGArr6M2bLojsYtRc7_Hd7QM',
    'config', jsonb_build_object(
      'eod_check_interval', '1 hour',
      'action_dispatch_enabled', true,
      'github_org', 'bold-business',
      'slack_channel', '#dev-updates'
    )
  ),
  'green',
  CURRENT_DATE,
  NOW()
) ON CONFLICT DO NOTHING;

-- Seed some example second_brain entries (without embeddings - those come from embed_and_store.py)
INSERT INTO second_brain (entry_type, content, tags) VALUES
  (
    'architecture',
    'workflow_os processes EOD reports from Google Drive folder 1oTfpoAddnGArr6M2bLojsYtRc7_Hd7QM, extracts action items, and dispatches them to Slack, GitHub, Calendar, and Email channels based on priority and owner.',
    ARRAY['architecture', 'workflow', 'overview']
  ),
  (
    'decision',
    'Use pgvector for second brain to enable semantic search over decisions, commands, and architecture notes. OpenAI text-embedding-3-small provides good balance of quality and cost.',
    ARRAY['database', 'vector-search', 'ai']
  ),
  (
    'command',
    'To manually trigger EOD processing: python workflow_os.py --process-eod --folder-id 1oTfpoAddnGArr6M2bLojsYtRc7_Hd7QM',
    ARRAY['operations', 'manual-trigger']
  )
ON CONFLICT DO NOTHING;

COMMENT ON TABLE eod_reports IS 'System config stored as special SYSTEM_CONFIG doc_id entry';
