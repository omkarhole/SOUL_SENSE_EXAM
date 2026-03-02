"""
Seed test data for performance testing database indexes.

This script creates 50,000+ journal entries to test index performance
at scale, as recommended in the issue requirements.

Usage: python tests/seed_test_data.py [--count 50000] [--users 100]
"""
import sqlite3
import os
import sys
import random
from datetime import datetime, timedelta
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'soulsense.db')

# Sample data for realistic entries
CATEGORIES = ['work', 'personal', 'health', 'family', 'social', 'finance', 'hobby', 'other']
PRIVACY_LEVELS = ['private', 'shared', 'public']
SAMPLE_CONTENTS = [
    "Had a productive day at work. Completed the project ahead of schedule.",
    "Feeling a bit stressed about the upcoming deadline. Need to focus.",
    "Great workout session today! Feeling energized and motivated.",
    "Family dinner was wonderful. Quality time with loved ones.",
    "Meditation helped clear my mind. Feeling more centered now.",
    "Struggling with sleep lately. Need to establish better habits.",
    "Celebrated a small win today. Progress feels good!",
    "Overwhelmed by the workload. Taking it one step at a time.",
]


def create_test_users(cursor, count: int) -> List[int]:
    """Create test users and return their IDs."""
    user_ids = []
    
    for i in range(count):
        username = f"testuser_{i:04d}"
        password_hash = "test_hash_12345"
        created_at = datetime.now() - timedelta(days=random.randint(1, 365))
        
        cursor.execute(
            """INSERT INTO users (username, password_hash, created_at, is_active, is_deleted)
               VALUES (?, ?, ?, 1, 0)""",
            (username, password_hash, created_at.isoformat())
        )
        user_ids.append(cursor.lastrowid)
    
    return user_ids


def create_journal_entries(cursor, user_ids: List[int], count: int):
    """Create journal entries distributed across users."""
    entries_created = 0
    batch_size = 1000
    
    for i in range(count):
        user_id = random.choice(user_ids)
        username = f"testuser_{user_id % 10000:04d}"
        
        # Random date within last year
        days_ago = random.randint(0, 365)
        timestamp = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
        entry_date = timestamp.strftime('%Y-%m-%d')
        
        content = random.choice(SAMPLE_CONTENTS) + f" [Entry #{i}]"
        category = random.choice(CATEGORIES)
        privacy = random.choice(PRIVACY_LEVELS)
        mood_score = random.randint(1, 10)
        is_deleted = random.random() < 0.05  # 5% deleted
        
        cursor.execute(
            """INSERT INTO journal_entries 
               (user_id, username, content, category, timestamp, entry_date, 
                mood_score, privacy_level, is_deleted, word_count, sentiment_score)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, username, content, category, timestamp.isoformat(), 
             entry_date, mood_score, privacy, is_deleted, 
             len(content.split()), random.uniform(-1, 1))
        )
        
        entries_created += 1
        
        # Commit in batches for performance
        if entries_created % batch_size == 0:
            cursor.connection.commit()
            print(f"  Created {entries_created}/{count} entries...")
    
    cursor.connection.commit()
    return entries_created


def create_scores(cursor, user_ids: List[int], count: int):
    """Create score records for testing."""
    scores_created = 0
    
    for i in range(count):
        user_id = random.choice(user_ids)
        username = f"testuser_{user_id % 10000:04d}"
        
        total_score = random.randint(20, 100)
        age = random.randint(18, 80)
        timestamp = datetime.now() - timedelta(days=random.randint(0, 365))
        
        cursor.execute(
            """INSERT INTO scores 
               (user_id, username, total_score, age, timestamp, sentiment_score)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, username, total_score, age, timestamp.isoformat(), 
             random.uniform(-1, 1))
        )
        
        scores_created += 1
        if scores_created % 1000 == 0:
            cursor.connection.commit()
    
    cursor.connection.commit()
    return scores_created


def create_responses(cursor, user_ids: List[int], count: int):
    """Create response records for testing."""
    responses_created = 0
    
    for i in range(count):
        user_id = random.choice(user_ids)
        username = f"testuser_{user_id % 10000:04d}"
        
        question_id = random.randint(1, 50)
        response_value = random.randint(1, 5)
        timestamp = datetime.now() - timedelta(days=random.randint(0, 365))
        
        cursor.execute(
            """INSERT INTO responses 
               (user_id, username, question_id, response_value, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, username, question_id, response_value, timestamp.isoformat())
        )
        
        responses_created += 1
        if responses_created % 1000 == 0:
            cursor.connection.commit()
    
    cursor.connection.commit()
    return responses_created


def main():
    parser = argparse.ArgumentParser(description='Seed test data for performance testing')
    parser.add_argument('--journal-count', type=int, default=50000,
                       help='Number of journal entries to create (default: 50000)')
    parser.add_argument('--user-count', type=int, default=100,
                       help='Number of test users to create (default: 100)')
    parser.add_argument('--scores-count', type=int, default=10000,
                       help='Number of score records to create (default: 10000)')
    parser.add_argument('--responses-count', type=int, default=20000,
                       help='Number of response records to create (default: 20000)')
    parser.add_argument('--clean', action='store_true',
                       help='Clean existing test data before seeding')
    args = parser.parse_args()
    
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)
    
    print("=" * 70)
    print("SEEDING TEST DATA FOR PERFORMANCE TESTING")
    print("=" * 70)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Clean existing test data if requested
    if args.clean:
        print("\nCleaning existing test data...")
        cursor.execute("DELETE FROM journal_entries WHERE username LIKE 'testuser_%'")
        cursor.execute("DELETE FROM scores WHERE username LIKE 'testuser_%'")
        cursor.execute("DELETE FROM responses WHERE username LIKE 'testuser_%'")
        cursor.execute("DELETE FROM users WHERE username LIKE 'testuser_%'")
        conn.commit()
        print("  Cleaned existing test data")
    
    # Create test users
    print(f"\nCreating {args.user_count} test users...")
    user_ids = create_test_users(cursor, args.user_count)
    print(f"  Created {len(user_ids)} users")
    
    # Create journal entries
    print(f"\nCreating {args.journal_count} journal entries...")
    journal_count = create_journal_entries(cursor, user_ids, args.journal_count)
    print(f"  Created {journal_count} journal entries")
    
    # Create scores
    print(f"\nCreating {args.scores_count} score records...")
    scores_count = create_scores(cursor, user_ids, args.scores_count)
    print(f"  Created {scores_count} score records")
    
    # Create responses
    print(f"\nCreating {args.responses_count} response records...")
    responses_count = create_responses(cursor, user_ids, args.responses_count)
    print(f"  Created {responses_count} response records")
    
    # Verify counts
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    
    cursor.execute("SELECT COUNT(*) FROM journal_entries")
    total_journal = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM scores")
    total_scores = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM responses")
    total_responses = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE username LIKE 'testuser_%'")
    total_test_users = cursor.fetchone()[0]
    
    print(f"Total journal entries: {total_journal}")
    print(f"Total scores: {total_scores}")
    print(f"Total responses: {total_responses}")
    print(f"Total test users: {total_test_users}")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("SEEDING COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Run: python tests/test_db_indexes.py")
    print("  2. Run: python tests/benchmark_indexes.py")


if __name__ == '__main__':
    main()
