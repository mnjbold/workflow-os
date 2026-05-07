#!/usr/bin/env python3
"""
Second Brain Embeddings Manager
Generates and stores OpenAI embeddings for second_brain entries
Includes RAG query function for semantic search
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from openai import OpenAI

# Database connection
DB_URL = "postgresql://postgres:Go8nY1FJv3HFBuu2knpPR61GouE9W3Pj@3.138.157.9:5432/postgres"

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_embedding(text: str, model: str = "text-embedding-3-small") -> list[float]:
    """Generate embedding vector for text using OpenAI"""
    text = text.replace("\n", " ")
    response = client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding

def store_entry(content: str, entry_type: str, tags: list[str] = None, eod_report_id: str = None):
    """
    Store a new second_brain entry with embedding
    
    Args:
        content: The text content to store
        entry_type: One of 'decision', 'command', 'note', 'architecture'
        tags: Optional list of tags
        eod_report_id: Optional UUID linking to source EOD report
    """
    embedding = get_embedding(content)
    
    with psycopg2.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO second_brain (content, entry_type, tags, embedding, eod_report_id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (content, entry_type, tags or [], embedding, eod_report_id))
            
            entry_id = cur.fetchone()[0]
            conn.commit()
            print(f"✓ Stored entry {entry_id}")
            return entry_id

def update_embeddings_for_existing():
    """Generate embeddings for entries that don't have them yet"""
    with psycopg2.connect(DB_URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Find entries without embeddings
            cur.execute("SELECT id, content FROM second_brain WHERE embedding IS NULL")
            entries = cur.fetchall()
            
            print(f"Found {len(entries)} entries without embeddings")
            
            for entry in entries:
                embedding = get_embedding(entry['content'])
                cur.execute(
                    "UPDATE second_brain SET embedding = %s WHERE id = %s",
                    (embedding, entry['id'])
                )
                print(f"✓ Updated embedding for {entry['id']}")
            
            conn.commit()

def rag_query(question: str, top_k: int = 5, entry_type: str = None):
    """
    Semantic search over second_brain
    
    Args:
        question: Natural language query (e.g., "What was the telephony decision?")
        top_k: Number of results to return
        entry_type: Optional filter by type ('decision', 'command', 'note', 'architecture')
    
    Returns:
        List of matching entries with similarity scores
    """
    query_embedding = get_embedding(question)
    
    with psycopg2.connect(DB_URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Build query with optional type filter
            type_filter = "AND entry_type = %s" if entry_type else ""
            params = [query_embedding, top_k]
            if entry_type:
                params.insert(1, entry_type)
            
            cur.execute(f"""
                SELECT 
                    id,
                    content,
                    entry_type,
                    tags,
                    created_at,
                    1 - (embedding <=> %s::vector) AS similarity
                FROM second_brain
                WHERE embedding IS NOT NULL
                {type_filter}
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, params)
            
            results = cur.fetchall()
            return results

def print_rag_results(question: str, **kwargs):
    """Pretty print RAG query results"""
    print(f"\n🔍 Query: {question}\n")
    results = rag_query(question, **kwargs)
    
    if not results:
        print("No results found")
        return
    
    for i, result in enumerate(results, 1):
        print(f"{i}. [{result['entry_type'].upper()}] (similarity: {result['similarity']:.3f})")
        print(f"   {result['content'][:200]}...")
        print(f"   Tags: {', '.join(result['tags']) if result['tags'] else 'none'}")
        print(f"   Created: {result['created_at']}\n")

# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("""
Usage:
  # Update embeddings for existing entries
  python embed_and_store.py update
  
  # Add a new entry
  python embed_and_store.py add "decision" "We chose Twilio for telephony" "telephony,twilio"
  
  # Query the second brain
  python embed_and_store.py query "What was the telephony decision?"
  python embed_and_store.py query "What was the telephony decision?" --type decision
        """)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "update":
        update_embeddings_for_existing()
    
    elif command == "add":
        if len(sys.argv) < 4:
            print("Usage: python embed_and_store.py add <type> <content> [tags]")
            sys.exit(1)
        
        entry_type = sys.argv[2]
        content = sys.argv[3]
        tags = sys.argv[4].split(',') if len(sys.argv) > 4 else []
        
        store_entry(content, entry_type, tags)
    
    elif command == "query":
        if len(sys.argv) < 3:
            print("Usage: python embed_and_store.py query <question> [--type TYPE]")
            sys.exit(1)
        
        question = sys.argv[2]
        entry_type = None
        
        if "--type" in sys.argv:
            entry_type = sys.argv[sys.argv.index("--type") + 1]
        
        print_rag_results(question, entry_type=entry_type)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
