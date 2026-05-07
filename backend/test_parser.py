"""
Quick validation test for EOD parser structure.
Run with: python3 test_parser.py
"""

import json
from models import ParsedEOD, ActionItem, InfraEvent, Sentiment, SecondBrainEntry, ManagementSuggestion, Summary

# Sample parsed EOD data matching the expected schema
sample_parsed = {
    "action_items": [
        {
            "title": "Fix prod API timeout",
            "owner": "alice",
            "priority": "P0",
            "due": "2025-05-08",
            "channels": ["slack", "calendar"]
        }
    ],
    "infra_events": [
        {
            "service": "auth-service",
            "error": "Connection pool exhausted",
            "severity": "high",
            "github_issue": True
        }
    ],
    "sentiment": {
        "tone": "stressed",
        "patterns": ["repeated timeout issues", "manual intervention required"],
        "compliance_flags": ["bypassed approval for hotfix"]
    },
    "second_brain": [
        {
            "type": "command",
            "content": "ssh prod-db-1 'pg_stat_activity | grep idle'",
            "tags": ["postgresql", "debugging", "production"]
        },
        {
            "type": "decision",
            "content": "Decided to scale DB connection pool from 10->50 instead of vertical scaling",
            "tags": ["architecture", "database", "scaling"]
        }
    ],
    "management_suggestions": [
        {
            "type": "doc",
            "content": "Write postmortem for 3hr API outage on 2025-05-07",
            "drive_dest": "Team Docs/Postmortems/2025/"
        },
        {
            "type": "diagram",
            "content": "Create Mermaid diagram showing auth service connection flow",
            "drive_dest": "Architecture Diagrams/"
        }
    ],
    "summary": {
        "date": "2025-05-07",
        "overall_health": "amber"
    }
}

def test_parsing():
    """Test that sample data validates against Pydantic models."""
    try:
        parsed = ParsedEOD(**sample_parsed)
        print("✓ ParsedEOD model validation passed")
        
        # Test individual components
        assert len(parsed.action_items) == 1
        assert parsed.action_items[0].priority == "P0"
        print("✓ Action items validated")
        
        assert len(parsed.infra_events) == 1
        assert parsed.infra_events[0].github_issue == True
        print("✓ Infra events validated")
        
        assert parsed.sentiment.tone == "stressed"
        assert len(parsed.sentiment.compliance_flags) == 1
        print("✓ Sentiment validated")
        
        assert len(parsed.second_brain) == 2
        assert parsed.second_brain[0].type == "command"
        print("✓ Second brain validated")
        
        assert len(parsed.management_suggestions) == 2
        print("✓ Management suggestions validated")
        
        assert parsed.summary.overall_health == "amber"
        print("✓ Summary validated")
        
        # Test JSON serialization
        json_output = parsed.model_dump()
        json_str = json.dumps(json_output, indent=2)
        print("\n✓ JSON serialization successful")
        print(f"\nSample output preview:\n{json_str[:300]}...\n")
        
        print("=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        print("\nParser models are structurally sound and ready for Claude integration.")
        
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        raise

if __name__ == "__main__":
    test_parsing()
