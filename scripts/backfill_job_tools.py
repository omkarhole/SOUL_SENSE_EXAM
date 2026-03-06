#!/usr/bin/env python
"""
Backfill Job CLI Tools.

Commands for monitoring, validating, and managing backfill operations:
  status <backfill-id>        - Get backfill job status
  list --migration VERSION     - List backfill jobs for a migration
  metrics --migration VERSION  - Get metrics summary for a migration
  integrity <backfill-id>      - Validate data integrity
  rollback-info <backfill-id>  - Get rollback information
"""

import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.infra.backfill_job_registry import get_backfill_registry, BackfillStatus


def format_duration(start_iso: str, end_iso: str = None) -> str:
    """Format duration between two ISO timestamps."""
    if not start_iso:
        return "N/A"
    
    try:
        start = datetime.fromisoformat(start_iso.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_iso.replace('Z', '+00:00')) if end_iso else datetime.now().astimezone()
        duration = end - start
        seconds = duration.total_seconds()
        
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"
    except Exception:
        return "N/A"


def cmd_status(args) -> None:
    """Get backfill job status."""
    registry = get_backfill_registry()
    job = registry.get_job(args.backfill_id)
    
    if not job:
        print(f"✗ Backfill job not found: {args.backfill_id}")
        return
    
    duration = format_duration(job.started_at, job.completed_at)
    status_icon = "✓" if job.status == BackfillStatus.COMPLETED.value else "✗" if job.status == BackfillStatus.FAILED.value else "⧖"
    
    print(f"\n{status_icon} Backfill Job Status")
    print(f"  ID:                {job.backfill_id}")
    print(f"  Type:              {job.job_type}")
    print(f"  Migration:         {job.migration_version}")
    print(f"  Status:            {job.status.upper()}")
    print(f"  Records Processed: {job.metrics.records_processed}")
    print(f"  Records Failed:    {job.metrics.records_failed}")
    print(f"  Success Rate:      {job.metrics.success_rate}%")
    print(f"  Execution Time:    {duration}")
    print(f"  Rollback Capable:  {'Yes' if job.rollback_capable else 'No'}")
    
    if job.error_details:
        print(f"  Error:             {job.error_details}")
    print()


def cmd_list(args) -> None:
    """List backfill jobs for a migration."""
    registry = get_backfill_registry()
    jobs = registry.get_jobs_by_migration(args.migration)
    
    if not jobs:
        print(f"ℹ No backfill jobs found for migration: {args.migration}")
        return
    
    print(f"\n📋 Backfill Jobs for Migration {args.migration}")
    print(f"{'ID':<36}  {'Type':<25}  {'Status':<12}  {'Success Rate':<13}")
    print("-" * 90)
    
    for job in jobs:
        status_icon = "✓" if job.status == BackfillStatus.COMPLETED.value else "✗" if job.status == BackfillStatus.FAILED.value else "⧖"
        print(f"{job.backfill_id}  {job.job_type:<25}  {status_icon} {job.status:<10}  {job.metrics.success_rate}%")
    print()


def cmd_metrics(args) -> None:
    """Get metrics summary for a migration."""
    registry = get_backfill_registry()
    summary = registry.get_metrics_summary(args.migration)
    
    if not summary:
        print(f"ℹ No metrics available for migration: {args.migration}")
        return
    
    print(f"\n📊 Backfill Metrics Summary - {args.migration}")
    print(f"  Total Backfill Jobs:    {summary['job_count']}")
    print(f"  Total Records Processed: {summary['total_records_processed']:,}")
    print(f"  Total Records Failed:    {summary['total_records_failed']:,}")
    print(f"  Overall Success Rate:    {summary['overall_success_rate']}%")
    print()


def cmd_integrity(args) -> None:
    """Validate data integrity for a backfill job."""
    registry = get_backfill_registry()
    job = registry.get_job(args.backfill_id)
    
    if not job:
        print(f"✗ Backfill job not found: {args.backfill_id}")
        return
    
    if not job.metrics.checksum_before or not job.metrics.checksum_after:
        print(f"⚠ Checksums not available for backfill: {args.backfill_id}")
        return
    
    is_valid = job.metrics.checksum_before != job.metrics.checksum_after
    status = "✓ PASS" if is_valid else "✗ FAIL"
    
    print(f"\n{status} - Data Integrity Validation")
    print(f"  Backfill ID:        {args.backfill_id}")
    print(f"  Checksum Before:    {job.metrics.checksum_before}")
    print(f"  Checksum After:     {job.metrics.checksum_after}")
    print(f"  Data Changed:       {'Yes' if is_valid else 'No'}")
    print()


def cmd_rollback_info(args) -> None:
    """Get rollback information for a backfill job."""
    registry = get_backfill_registry()
    info = registry.generate_rollback_info(args.backfill_id)
    
    if not info:
        print(f"✗ Backfill job not found: {args.backfill_id}")
        return
    
    if not info['rollback_capable']:
        print(f"⚠ Rollback is not possible for this backfill: {args.backfill_id}")
        return
    
    print(f"\n↩ Rollback Information")
    print(f"  Backfill ID:        {info['backfill_id']}")
    print(f"  Job Type:           {info['job_type']}")
    print(f"  Migration:          {info['migration_version']}")
    print(f"  Records Affected:   {info['records_affected']}")
    print(f"  Checksum Before:    {info['checksum_before']}")
    print(f"  Checksum After:     {info['checksum_after']}")
    print(f"  Rollback Capable:   {'Yes' if info['rollback_capable'] else 'No'}")
    print(f"  Timestamp:          {info['timestamp']}")
    print("\nℹ To rollback, restore data from backup or use your rollback mechanism.")
    print()


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Backfill Job Observability CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/backfill_job_tools.py status a1b2c3d4-e5f6-7890-abcd-ef1234567890
  python scripts/backfill_job_tools.py list --migration 20260306_001
  python scripts/backfill_job_tools.py metrics --migration 20260306_001
  python scripts/backfill_job_tools.py integrity a1b2c3d4-e5f6-7890-abcd-ef1234567890
  python scripts/backfill_job_tools.py rollback-info a1b2c3d4-e5f6-7890-abcd-ef1234567890
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # status command
    status_parser = subparsers.add_parser('status', help='Get backfill job status')
    status_parser.add_argument('backfill_id', help='Backfill job ID')
    
    # list command
    list_parser = subparsers.add_parser('list', help='List backfill jobs for a migration')
    list_parser.add_argument('--migration', required=True, help='Migration version')
    
    # metrics command
    metrics_parser = subparsers.add_parser('metrics', help='Get metrics summary')
    metrics_parser.add_argument('--migration', required=True, help='Migration version')
    
    # integrity command
    integrity_parser = subparsers.add_parser('integrity', help='Validate data integrity')
    integrity_parser.add_argument('backfill_id', help='Backfill job ID')
    
    # rollback-info command
    rollback_parser = subparsers.add_parser('rollback-info', help='Get rollback information')
    rollback_parser.add_argument('backfill_id', help='Backfill job ID')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Dispatch to appropriate command
    commands = {
        'status': cmd_status,
        'list': cmd_list,
        'metrics': cmd_metrics,
        'integrity': cmd_integrity,
        'rollback-info': cmd_rollback_info,
    }
    
    handler = commands.get(args.command)
    if handler:
        handler(args)
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
