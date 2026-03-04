"""
Score Export Utility for SoulSense

This script queries the scores table from the database and exports it to a CSV file.
Supports filtering by username and date range for flexible data backup and analysis.

Features:
    - Export all scores or filter by username
    - Date range filtering (from/to dates)
    - CSV output with pandas for easy analysis
    - Simple command-line interface

Usage:
    # Export all scores
    python scripts/export_scores.py

    # Export scores for a specific user
    python scripts/export_scores.py --username john_doe

    # Export scores within a date range
    python scripts/export_scores.py --from-date 2026-01-01 --to-date 2026-01-22

    # Export to a custom file
    python scripts/export_scores.py --output data/my_scores.csv

    # Combine filters
    python scripts/export_scores.py --username john_doe --from-date 2026-01-01 --output exports/john_scores.csv
"""

import sys
import os
import argparse
import logging
from datetime import datetime
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import pandas as pd
except ImportError:
    print("Error: pandas is required. Install it with: pip install pandas")
    sys.exit(1)

from sqlalchemy import and_
from app.db import safe_db_context
from app.models import Score, UserSession

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def validate_date(date_string: str) -> bool:
    """Validate date string is in ISO format (YYYY-MM-DD)"""
    try:
        datetime.fromisoformat(date_string)
        return True
    except ValueError:
        return False


def export_scores(
    output_file: str = "exports/scores_export.csv",
    username: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> None:
    """
    Export scores from the database to a CSV file.
    
    Args:
        output_file: Path to the output CSV file
        username: Optional username to filter by
        from_date: Optional start date (ISO format: YYYY-MM-DD)
        to_date: Optional end date (ISO format: YYYY-MM-DD)
    """
    logger.info("Starting score export...")
    
    # Validate dates if provided
    if from_date and not validate_date(from_date):
        logger.error(f"Invalid from_date format: {from_date}. Use YYYY-MM-DD format.")
        return
    
    if to_date and not validate_date(to_date):
        logger.error(f"Invalid to_date format: {to_date}. Use YYYY-MM-DD format.")
        return
    
    # Build filters
    filters = []
    
    if username:
        filters.append(Score.username == username)
        logger.info(f"Filtering by username: {username}")
    
    if from_date:
        # Compare timestamps (ISO format strings compare correctly)
        filters.append(Score.timestamp >= from_date)
        logger.info(f"Filtering from date: {from_date}")
    
    if to_date:
        # Add one day to include the entire end date
        to_date_inclusive = f"{to_date}T23:59:59"
        filters.append(Score.timestamp <= to_date_inclusive)
        logger.info(f"Filtering to date: {to_date}")
    
    try:
        with safe_db_context() as session:
            # Query scores with filters
            query = session.query(Score, UserSession.user_id).join(UserSession, Score.session_id == UserSession.session_id)
            if filters:
                query = query.filter(and_(*filters))
            
            # Order by timestamp (newest first)
            query = query.order_by(Score.timestamp.desc())
            
            scores = query.all()
            
            if not scores:
                logger.warning("No scores found matching the criteria.")
                print("No scores found to export.")
                return
            
            logger.info(f"Found {len(scores)} score(s) to export.")
            
            # Convert to DataFrame
            data = []
            for score, user_id in scores:
                data.append({
                    'id': score.id,
                    'username': score.username,
                    'user_id': user_id,
                    'total_score': score.total_score,
                    'sentiment_score': score.sentiment_score,
                    'age': score.age,
                    'detailed_age_group': score.detailed_age_group,
                    'is_rushed': score.is_rushed,
                    'is_inconsistent': score.is_inconsistent,
                    'reflection_text': score.reflection_text,
                    'timestamp': score.timestamp
                })
            
            df = pd.DataFrame(data)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
            
            # Export to CSV
            df.to_csv(output_file, index=False)
            logger.info(f"Successfully exported {len(scores)} score(s) to {output_file}")
            print(f"\n✓ Successfully exported {len(scores)} score(s) to {output_file}")
            
            # Display summary statistics
            print("\n=== Export Summary ===")
            print(f"Total records: {len(scores)}")
            print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            print(f"Unique users: {df['username'].nunique()}")
            print(f"Average score: {df['total_score'].mean():.2f}")
            print(f"Score range: {df['total_score'].min()} - {df['total_score'].max()}")
            
    except Exception as e:
        logger.error(f"Error exporting scores: {str(e)}", exc_info=True)
        print(f"\n✗ Error exporting scores: {str(e)}")
        raise


def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(
        description="Export scores from SoulSense database to CSV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Export all scores:
    python scripts/export_scores.py

  Export for specific user:
    python scripts/export_scores.py --username john_doe

  Export with date range:
    python scripts/export_scores.py --from-date 2026-01-01 --to-date 2026-01-22

  Custom output file:
    python scripts/export_scores.py --output data/my_scores.csv
        """
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='exports/scores_export.csv',
        help='Output CSV file path (default: exports/scores_export.csv)'
    )
    
    parser.add_argument(
        '--username', '-u',
        type=str,
        default=None,
        help='Filter by username'
    )
    
    parser.add_argument(
        '--from-date', '-f',
        type=str,
        default=None,
        help='Filter from date (format: YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--to-date', '-t',
        type=str,
        default=None,
        help='Filter to date (format: YYYY-MM-DD)'
    )
    
    args = parser.parse_args()
    
    # Run export
    export_scores(
        output_file=args.output,
        username=args.username,
        from_date=args.from_date,
        to_date=args.to_date
    )


if __name__ == '__main__':
    main()
