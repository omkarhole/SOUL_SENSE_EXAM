#!/usr/bin/env python
"""
Migration Registry CLI Tools

Commands:
  generate-registry    - Generate and save checksums for all migrations
  verify-all          - Verify all migrations against registry
  register <file>     - Register a new migration
  detect-changes      - Detect modified or missing migrations
  validate-registry   - Validate registry file integrity
"""

import argparse
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.infra.migration_checksum_registry import ChecksumRegistry


def cmd_generate_registry(args):
    """Generate registry from current migration files."""
    registry = ChecksumRegistry()
    checksums = registry.compute_all_checksums()
    
    if not checksums:
        logger.warning("No migration files found")
        return 1
    
    success = registry.save_registry(checksums)
    if success:
        logger.info(f"✓ Registry generated with {len(checksums)} migrations")
        for migration_id in sorted(checksums.keys()):
            logger.info(f"  - {migration_id}: {checksums[migration_id].filename}")
        return 0
    else:
        logger.error("✗ Failed to save registry")
        return 1


def cmd_verify_all(args):
    """Verify all migrations against registry."""
    registry = ChecksumRegistry()
    result = registry.verify_all_migrations()
    
    logger.info(f"Total migrations: {result.total_migrations}")
    logger.info(f"Valid: {result.valid_count}")
    logger.info(f"Modified: {result.modified_count}")
    logger.info(f"Missing: {result.missing_count}")
    
    if result.modified_migrations:
        logger.warning("Modified migrations:")
        for mig in result.modified_migrations:
            logger.warning(f"  - {mig}")
    
    if result.missing_migrations:
        logger.warning("Missing migrations:")
        for mig in result.missing_migrations:
            logger.warning(f"  - {mig}")
    
    if result.passed:
        logger.info("✓ All migrations verified successfully")
        return 0
    else:
        logger.error(f"✗ Verification failed: {result.error_message}")
        return 1


def cmd_register(args):
    """Register a new migration."""
    if not args.file:
        logger.error("Please specify migration filename")
        return 1
    
    registry = ChecksumRegistry()
    success = registry.register_migration(args.file)
    
    if success:
        logger.info(f"✓ Migration '{args.file}' registered")
        return 0
    else:
        logger.error(f"✗ Failed to register migration '{args.file}'")
        return 1


def cmd_detect_changes(args):
    """Detect modifications or missing migrations."""
    registry = ChecksumRegistry()
    modified = registry.detect_modified_migrations()
    
    if modified:
        logger.warning(f"Found {len(modified)} modified/missing migrations:")
        for mig in modified:
            logger.warning(f"  - {mig}")
        return 1
    else:
        logger.info("✓ No modifications detected")
        return 0


def cmd_validate_registry(args):
    """Validate registry file format."""
    registry = ChecksumRegistry()
    reg_record = registry.load_registry()
    
    if reg_record is None:
        logger.error("✗ Registry file is missing or corrupted")
        return 1
    
    logger.info(f"Registry version: {reg_record.registry_version}")
    logger.info(f"Created: {reg_record.created_at}")
    logger.info(f"Last updated: {reg_record.last_updated}")
    logger.info(f"Migrations tracked: {len(reg_record.migrations)}")
    logger.info("✓ Registry is valid")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Migration Registry CLI Tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  python migration_registry_tools.py generate-registry\n"
               "  python migration_registry_tools.py verify-all\n"
               "  python migration_registry_tools.py register abc123_migration.py\n"
               "  python migration_registry_tools.py detect-changes"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # generate-registry
    subparsers.add_parser("generate-registry", help="Generate registry from current files")
    
    # verify-all
    subparsers.add_parser("verify-all", help="Verify all migrations")
    
    # register
    register_parser = subparsers.add_parser("register", help="Register new migration")
    register_parser.add_argument("file", help="Migration filename")
    
    # detect-changes
    subparsers.add_parser("detect-changes", help="Detect modified migrations")
    
    # validate-registry
    subparsers.add_parser("validate-registry", help="Validate registry file")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Dispatch to command handler
    handlers = {
        "generate-registry": cmd_generate_registry,
        "verify-all": cmd_verify_all,
        "register": cmd_register,
        "detect-changes": cmd_detect_changes,
        "validate-registry": cmd_validate_registry,
    }
    
    handler = handlers.get(args.command)
    if handler:
        return handler(args)
    else:
        logger.error(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
