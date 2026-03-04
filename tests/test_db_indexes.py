"""
Test Suite for Database Performance Indexes (Issue #955)

Run with: pytest tests/test_db_indexes.py -v
Or: python tests/test_db_indexes.py
"""
import sqlite3
import os
import sys
import time
import statistics
from typing import List, Tuple, Dict
import unittest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'soulsense.db')


class DatabaseIndexTests(unittest.TestCase):
    """Test suite for database indexes."""
    
    @classmethod
    def setUpClass(cls):
        """Set up database connection."""
        if not os.path.exists(DB_PATH):
            raise FileNotFoundError(f"Database not found at {DB_PATH}")
        cls.conn = sqlite3.connect(DB_PATH)
        cls.cursor = cls.conn.cursor()
    
    @classmethod
    def tearDownClass(cls):
        """Close database connection."""
        if hasattr(cls, 'conn'):
            cls.conn.close()
    
    def test_01_database_exists(self):
        """Verify database file exists."""
        self.assertTrue(os.path.exists(DB_PATH), "Database file should exist")
    
    def test_02_foreign_key_indexes_exist(self):
        """Verify indexes on foreign key columns."""
        expected_indexes = [
            ('journal_entries', 'ix_journal_entries_user_id'),
            ('scores', 'ix_scores_user_id'),
            ('responses', 'ix_responses_user_id'),
            ('assessment_results', 'ix_assessment_results_user_id'),
            ('otp_codes', 'ix_otp_codes_user_id'),
            ('password_history', 'ix_password_history_user_id'),
            ('refresh_tokens', 'ix_refresh_tokens_user_id'),
            ('analytics_events', 'ix_analytics_events_user_id'),
        ]
        
        for table, index_name in expected_indexes:
            with self.subTest(table=table, index=index_name):
                self.cursor.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='index' AND name=? AND tbl_name=?",
                    (index_name, table)
                )
                self.assertIsNotNone(self.cursor.fetchone(), 
                    f"Index {index_name} should exist on {table}")
    
    def test_03_timestamp_indexes_exist(self):
        """Verify indexes on timestamp columns."""
        expected_indexes = [
            ('scores', 'ix_scores_timestamp'),
            ('responses', 'ix_responses_timestamp'),
            ('journal_entries', 'ix_journal_entries_timestamp'),
            ('journal_entries', 'ix_journal_entries_entry_date'),
            ('assessment_results', 'ix_assessment_results_timestamp'),
            ('otp_codes', 'ix_otp_codes_expires_at'),
            ('refresh_tokens', 'ix_refresh_tokens_created_at'),
            ('refresh_tokens', 'ix_refresh_tokens_expires_at'),
        ]
        
        for table, index_name in expected_indexes:
            with self.subTest(table=table, index=index_name):
                self.cursor.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='index' AND name=? AND tbl_name=?",
                    (index_name, table)
                )
                self.assertIsNotNone(self.cursor.fetchone(),
                    f"Index {index_name} should exist on {table}")
    
    def test_04_status_category_indexes_exist(self):
        """Verify indexes on status and category columns."""
        expected_indexes = [
            ('challenges', 'ix_challenges_is_active'),
            ('challenges', 'ix_challenges_challenge_type'),
            ('journal_entries', 'ix_journal_entries_category'),
            ('journal_entries', 'ix_journal_entries_is_deleted'),
            ('journal_entries', 'ix_journal_entries_privacy_level'),
            ('otp_codes', 'ix_otp_codes_purpose'),
            ('otp_codes', 'ix_otp_codes_is_used'),
            ('refresh_tokens', 'ix_refresh_tokens_is_revoked'),
        ]
        
        for table, index_name in expected_indexes:
            with self.subTest(table=table, index=index_name):
                self.cursor.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='index' AND name=? AND tbl_name=?",
                    (index_name, table)
                )
                self.assertIsNotNone(self.cursor.fetchone(),
                    f"Index {index_name} should exist on {table}")
    
    def test_05_journal_entries_user_lookup_uses_index(self):
        """Verify user_id lookup on journal_entries uses index."""
        self.cursor.execute(
            "EXPLAIN QUERY PLAN SELECT * FROM journal_entries WHERE user_id = 1"
        )
        plan = self.cursor.fetchall()
        plan_str = str(plan)
        
        self.assertIn('ix_journal_entries_user_id', plan_str,
            "Query should use ix_journal_entries_user_id index")
        self.assertIn('SEARCH', plan_str,
            "Query plan should be SEARCH, not SCAN")
    
    def test_06_scores_timestamp_sort_uses_index(self):
        """Verify timestamp sorting on scores uses index."""
        self.cursor.execute(
            "EXPLAIN QUERY PLAN SELECT * FROM scores ORDER BY timestamp DESC LIMIT 10"
        )
        plan = self.cursor.fetchall()
        plan_str = str(plan)
        
        self.assertIn('ix_scores_timestamp', plan_str,
            "Query should use ix_scores_timestamp index")
    
    def test_07_responses_user_timestamp_uses_index(self):
        """Verify user_id + timestamp query uses index."""
        self.cursor.execute(
            "EXPLAIN QUERY PLAN SELECT * FROM responses WHERE user_id = 1 ORDER BY timestamp"
        )
        plan = self.cursor.fetchall()
        plan_str = str(plan)
        
        # Should use composite index or user_id index
        has_index = ('idx_response_user_timestamp' in plan_str or 
                     'ix_responses_user_id' in plan_str)
        self.assertTrue(has_index,
            "Query should use an index for user_id filter")
    
    def test_08_journal_entries_category_filter_uses_index(self):
        """Verify category filter on journal_entries uses index."""
        self.cursor.execute(
            "EXPLAIN QUERY PLAN SELECT * FROM journal_entries WHERE category = 'work'"
        )
        plan = self.cursor.fetchall()
        plan_str = str(plan)
        
        self.assertIn('ix_journal_entries_category', plan_str,
            "Query should use ix_journal_entries_category index")
    
    def test_09_otp_codes_expires_at_filter_uses_index(self):
        """Verify expires_at filter on OTP codes uses index."""
        self.cursor.execute(
            "EXPLAIN QUERY PLAN SELECT * FROM otp_codes WHERE expires_at > datetime('now')"
        )
        plan = self.cursor.fetchall()
        plan_str = str(plan)
        
        self.assertIn('ix_otp_codes_expires_at', plan_str,
            "Query should use ix_otp_codes_expires_at index")
    
    def test_10_refresh_tokens_revoked_filter_uses_index(self):
        """Verify is_revoked filter on refresh_tokens uses index."""
        self.cursor.execute(
            "EXPLAIN QUERY PLAN SELECT * FROM refresh_tokens WHERE is_revoked = 0"
        )
        plan = self.cursor.fetchall()
        plan_str = str(plan)
        
        self.assertIn('ix_refresh_tokens_is_revoked', plan_str,
            "Query should use ix_refresh_tokens_is_revoked index")
    
    def test_11_challenge_active_filter_uses_index(self):
        """Verify is_active filter on challenges uses index."""
        self.cursor.execute(
            "EXPLAIN QUERY PLAN SELECT * FROM challenges WHERE is_active = 1"
        )
        plan = self.cursor.fetchall()
        plan_str = str(plan)
        
        self.assertIn('ix_challenges_is_active', plan_str,
            "Query should use ix_challenges_is_active index")


class PerformanceBenchmarkTests(unittest.TestCase):
    """Performance benchmark tests (requires seeded database)."""
    
    @classmethod
    def setUpClass(cls):
        """Set up database connection."""
        if not os.path.exists(DB_PATH):
            raise FileNotFoundError(f"Database not found at {DB_PATH}")
        cls.conn = sqlite3.connect(DB_PATH)
        cls.cursor = cls.conn.cursor()
        
        # Get a sample user_id if exists
        cls.cursor.execute("SELECT id FROM users LIMIT 1")
        result = cls.cursor.fetchone()
        cls.test_user_id = result[0] if result else None
    
    @classmethod
    def tearDownClass(cls):
        """Close database connection."""
        if hasattr(cls, 'conn'):
            cls.conn.close()
    
    def _benchmark_query(self, query: str, params: tuple = (), iterations: int = 10) -> Dict:
        """Benchmark a query and return statistics."""
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            self.cursor.execute(query, params)
            self.cursor.fetchall()
            end = time.perf_counter()
            times.append((end - start) * 1000)  # ms
        
        return {
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'min': min(times),
            'max': max(times),
            'stdev': statistics.stdev(times) if len(times) > 1 else 0
        }
    
    @unittest.skipIf(True, "Performance tests - run manually with seeded data")
    def test_benchmark_journal_entries_user_lookup(self):
        """Benchmark user lookup performance on journal_entries."""
        if not self.test_user_id:
            self.skipTest("No users in database")
        
        stats = self._benchmark_query(
            "SELECT * FROM journal_entries WHERE user_id = ?",
            (self.test_user_id,)
        )
        
        print(f"\nJournal Entries User Lookup:")
        print(f"  Mean: {stats['mean']:.3f}ms")
        print(f"  Max: {stats['max']:.3f}ms")
        
        # With index, should be under 10ms even with large datasets
        self.assertLess(stats['mean'], 50, 
            "User lookup should be fast with index")
    
    @unittest.skipIf(True, "Performance tests - run manually with seeded data")
    def test_benchmark_scores_timestamp_sort(self):
        """Benchmark timestamp sorting on scores."""
        stats = self._benchmark_query(
            "SELECT * FROM scores ORDER BY timestamp DESC LIMIT 100"
        )
        
        print(f"\nScores Timestamp Sort:")
        print(f"  Mean: {stats['mean']:.3f}ms")
        print(f"  Max: {stats['max']:.3f}ms")
        
        self.assertLess(stats['mean'], 50,
            "Timestamp sort should be fast with index")


def run_index_verification():
    """Run a quick verification of all indexes."""
    print("=" * 70)
    print("DATABASE INDEX VERIFICATION")
    print("=" * 70)
    
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Count indexes by table
    cursor.execute(
        "SELECT tbl_name, COUNT(*) FROM sqlite_master "
        "WHERE type='index' AND name LIKE 'ix_%' GROUP BY tbl_name"
    )
    results = cursor.fetchall()
    
    print("\nIndexes created per table:")
    total = 0
    for table, count in sorted(results):
        print(f"  {table:30s}: {count:2d} indexes")
        total += count
    print(f"\nTotal new indexes: {total}")
    
    # Verify key indexes exist
    print("\n" + "-" * 70)
    print("Verifying key indexes...")
    print("-" * 70)
    
    key_indexes = [
        ('journal_entries', 'ix_journal_entries_user_id', 'FK lookup'),
        ('scores', 'ix_scores_user_id', 'FK lookup'),
        ('responses', 'ix_responses_user_id', 'FK lookup'),
        ('journal_entries', 'ix_journal_entries_timestamp', 'Sorting'),
        ('scores', 'ix_scores_timestamp', 'Sorting'),
        ('challenges', 'ix_challenges_is_active', 'Filtering'),
        ('journal_entries', 'ix_journal_entries_category', 'Filtering'),
    ]
    
    all_pass = True
    for table, index, purpose in key_indexes:
        cursor.execute(
            "SELECT 1 FROM sqlite_master WHERE type='index' AND name=? AND tbl_name=?",
            (index, table)
        )
        exists = cursor.fetchone() is not None
        status = "OK" if exists else "MISSING"
        symbol = "[OK]" if exists else "[FAIL]"
        print(f"  {symbol} {table}.{index} ({purpose})")
        if not exists:
            all_pass = False
    
    conn.close()
    
    print("\n" + "=" * 70)
    if all_pass:
        print("ALL INDEXES VERIFIED SUCCESSFULLY")
    else:
        print("SOME INDEXES ARE MISSING - CHECK IMPLEMENTATION")
    print("=" * 70)
    
    return all_pass


def run_query_plan_tests():
    """Run query plan verification tests."""
    print("\n" + "=" * 70)
    print("QUERY PLAN VERIFICATION")
    print("=" * 70)
    
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    test_queries = [
        ("Journal user lookup", 
         "SELECT * FROM journal_entries WHERE user_id = 1",
         "ix_journal_entries_user_id"),
        ("Scores timestamp sort",
         "SELECT * FROM scores ORDER BY timestamp DESC LIMIT 10",
         "ix_scores_timestamp"),
        ("Responses user filter",
         "SELECT * FROM responses WHERE user_id = 1",
         "ix_responses_user_id"),
        ("Journal category filter",
         "SELECT * FROM journal_entries WHERE category = 'work'",
         "ix_journal_entries_category"),
        ("Challenge active filter",
         "SELECT * FROM challenges WHERE is_active = 1",
         "ix_challenges_is_active"),
    ]
    
    all_pass = True
    for test_name, query, expected_index in test_queries:
        cursor.execute(f"EXPLAIN QUERY PLAN {query}")
        plan = cursor.fetchall()
        plan_str = str(plan)
        
        uses_index = expected_index in plan_str
        uses_search = 'SEARCH' in plan_str
        
        status = "OK" if uses_index else "FAIL"
        symbol = "[OK]" if uses_index else "[FAIL]"
        
        print(f"\n{symbol} {test_name}")
        print(f"    Query: {query[:60]}...")
        print(f"    Plan: {plan_str[:80]}...")
        
        if not uses_index:
            print(f"    WARNING: Expected index {expected_index} not used!")
            all_pass = False
    
    conn.close()
    
    print("\n" + "=" * 70)
    if all_pass:
        print("ALL QUERIES USE INDEXES - OPTIMAL PERFORMANCE")
    else:
        print("SOME QUERIES NOT USING INDEXES - REVIEW NEEDED")
    print("=" * 70)
    
    return all_pass


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Test database indexes')
    parser.add_argument('--verify', action='store_true', 
                       help='Run index verification only')
    parser.add_argument('--plans', action='store_true',
                       help='Run query plan verification only')
    parser.add_argument('--all', action='store_true',
                       help='Run all tests')
    args = parser.parse_args()
    
    if args.verify:
        run_index_verification()
    elif args.plans:
        run_query_plan_tests()
    else:
        # Run verification tests
        run_index_verification()
        run_query_plan_tests()
        
        # Run unittest suite
        print("\n" + "=" * 70)
        print("RUNNING UNIT TESTS")
        print("=" * 70)
        unittest.main(argv=[''], verbosity=2, exit=False)
