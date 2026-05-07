import os
import json
from anthropic import Anthropic
from models import ParsedEOD, EnrichedEOD

HAIKU_SYSTEM_PROMPT = """You are an EOD report parser. Extract structured data from end-of-day engineering reports.

Parse the report into exactly 5 data layers:

1. **Action Items** - Tasks requiring follow-up
   - Extract: title, owner, priority (P0-P4), due date, delivery channels
   - Channels: slack (team updates), calendar (scheduled work), email (external stakeholders)

2. **Infra Events** - System issues, errors, incidents
   - Extract: service name, error type, severity (low/medium/high/critical)
   - Flag whether this should become a GitHub issue

3. **Sentiment** - Team health indicators
   - Tone: positive/neutral/negative/frustrated
   - Patterns: recurring themes, blockers
   - Compliance flags: things like "bypassed approval", "skipped review", "manual override"

4. **Second Brain** - Knowledge to persist
   - Type: decision (architectural choices), command (useful CLI/SSH), note (context)
   - Tag appropriately for later retrieval

5. **Management Suggestions** - Artifacts to create
   - Type: doc (RFC, postmortem), diagram (Mermaid architecture), share (status update)
   - Specify Google Drive destination folder

Return ONLY valid JSON matching this structure:
{
  "action_items": [{"title": "", "owner": "", "priority": "P1", "due": "", "channels": ["slack"]}],
  "infra_events": [{"service": "", "error": "", "severity": "high", "github_issue": true}],
  "sentiment": {"tone": "neutral", "patterns": [], "compliance_flags": []},
  "second_brain": [{"type": "decision", "content": "", "tags": []}],
  "management_suggestions": [{"type": "doc", "content": "", "drive_dest": ""}],
  "summary": {"date": "", "overall_health": "green"}
}

Be strict about JSON validity. Use empty arrays for missing data, never null."""

OPUS_ENRICHMENT_PROMPT = """You are a senior engineering manager reviewing a parsed EOD report.

Your task:
1. **Enrich context** - Add missing details, clarify ambiguous items
2. **Prioritize ruthlessly** - Re-rank action items by true urgency vs stated priority
3. **Identify patterns** - Spot recurring issues, systemic problems, team health signals
4. **Recommend escalations** - What needs immediate leadership attention?

Input: Parsed EOD JSON
Output: Enrichment object with keys:
- context_additions: {item_id: additional_context}
- priority_adjustments: {item_id: {original: "P2", suggested: "P0", reasoning: ""}}
- patterns_detected: [list of systemic issues]
- escalations: [items needing immediate attention with reasoning]

Return ONLY valid JSON."""


class EODParser:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
    
    async def parse_with_haiku(self, eod_content: str) -> ParsedEOD:
        """Parse EOD report using Claude Haiku."""
        try:
            message = self.client.messages.create(
                model="claude-haiku-4-20250514",
                max_tokens=4096,
                system=HAIKU_SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": f"Parse this EOD report:\n\n{eod_content}"
                }]
            )
            
            response_text = message.content[0].text
            parsed_json = json.loads(response_text)
            return ParsedEOD(**parsed_json)
        
        except json.JSONDecodeError as e:
            raise ValueError(f"Claude Haiku returned invalid JSON: {e}")
        except Exception as e:
            raise RuntimeError(f"Haiku parsing failed: {e}")
    
    async def enrich_with_opus(self, parsed: ParsedEOD) -> EnrichedEOD:
        """Enrich and prioritize using Claude Opus 4.7."""
        try:
            parsed_json = parsed.model_dump()
            
            message = self.client.messages.create(
                model="claude-opus-4-20250514",
                max_tokens=8192,
                system=OPUS_ENRICHMENT_PROMPT,
                messages=[{
                    "role": "user",
                    "content": f"Enrich and prioritize this parsed EOD:\n\n{json.dumps(parsed_json, indent=2)}"
                }]
            )
            
            response_text = message.content[0].text
            enrichment_data = json.loads(response_text)
            
            return EnrichedEOD(
                parsed=parsed,
                enrichment=enrichment_data.get("context_additions", {}),
                prioritization={
                    "adjustments": enrichment_data.get("priority_adjustments", {}),
                    "patterns": enrichment_data.get("patterns_detected", []),
                    "escalations": enrichment_data.get("escalations", [])
                }
            )
        
        except json.JSONDecodeError as e:
            # If Opus enrichment fails, return parsed data without enrichment
            return EnrichedEOD(parsed=parsed, enrichment={}, prioritization={})
        except Exception as e:
            raise RuntimeError(f"Opus enrichment failed: {e}")
