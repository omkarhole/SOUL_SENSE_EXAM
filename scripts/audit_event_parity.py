#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Android / iOS Event Parity Audit Script

This script performs automated comparison of analytics events between
Android and iOS platforms to ensure 100% event parity.

Usage:
    python scripts/audit_event_parity.py
    python scripts/audit_event_parity.py --format markdown --output reports/
    python scripts/audit_event_parity.py --json --output report.json

Author: Mobile Platform Team
Version: 1.0
"""

import argparse
import io
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Fix encoding on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


@dataclass
class EventDefinition:
    """Represents an analytics event definition."""
    name: str
    constant_name: str
    platform: str
    category: str
    line_number: int
    description: str = ""
    
    def __hash__(self):
        return hash(self.name)
    
    def __eq__(self, other):
        if isinstance(other, EventDefinition):
            return self.name == other.name
        return False


@dataclass
class ParityReport:
    """Represents the parity audit report."""
    audit_date: str
    android_events: List[EventDefinition] = field(default_factory=list)
    ios_events: List[EventDefinition] = field(default_factory=list)
    schema_events: List[str] = field(default_factory=list)
    
    # Analysis results
    matched_events: List[EventDefinition] = field(default_factory=list)
    android_only: List[EventDefinition] = field(default_factory=list)
    ios_only: List[EventDefinition] = field(default_factory=list)
    schema_mismatches: List[str] = field(default_factory=list)
    
    @property
    def total_expected(self) -> int:
        """Total expected events (union of all events)."""
        all_events = set(e.name for e in self.android_events + self.ios_events)
        return len(all_events)
    
    @property
    def matched_count(self) -> int:
        """Number of events present on both platforms."""
        return len(self.matched_events)
    
    @property
    def parity_score(self) -> float:
        """Calculate parity score as percentage."""
        if self.total_expected == 0:
            return 100.0
        return round((self.matched_count / self.total_expected) * 100, 2)
    
    @property
    def status(self) -> str:
        """Determine overall status based on parity score."""
        score = self.parity_score
        if score == 100:
            return "✅ PERFECT"
        elif score >= 95:
            return "⚠️ GOOD"
        elif score >= 90:
            return "🔶 WARNING"
        else:
            return "🚨 CRITICAL"


class EventParser:
    """Parser for extracting events from platform source files."""
    
    # Regex patterns for extracting events
    ANDROID_PATTERN = re.compile(
        r'public\s+static\s+final\s+String\s+(\w+)\s*=\s*"([^"]+)";',
        re.MULTILINE
    )
    
    IOS_PATTERN = re.compile(
        r'public\s+static\s+let\s+(\w+)\s*=\s*"([^"]+)"',
        re.MULTILINE
    )
    
    CATEGORY_PATTERN = re.compile(
        r'//\s*={10,}\s*\n//\s*(\w[\w\s]+)\s*\n//\s*={10,}',
        re.MULTILINE
    )
    
    DESCRIPTION_PATTERN = re.compile(
        r'/\*\*\s*([^*]+)\*/\s*\n\s*public\s+static',
        re.MULTILINE
    )

    @staticmethod
    def parse_android(filepath: str) -> List[EventDefinition]:
        """Parse Android AnalyticsEvents.java file."""
        events = []
        content = Path(filepath).read_text(encoding='utf-8')
        
        # Build category map from line numbers
        categories = {}
        current_category = "Uncategorized"
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if 'SCREEN VIEW' in line.upper() and '===' in lines[i-2] if i > 1 else False:
                current_category = "Screen View Events"
            elif 'USER INTERACTION' in line.upper():
                current_category = "User Interaction Events"
            elif 'AUTHENTICATION' in line.upper():
                current_category = "Authentication Events"
            elif 'PAYMENT' in line.upper():
                current_category = "Payment Events"
            elif 'FEATURE USAGE' in line.upper():
                current_category = "Feature Usage Events"
            elif 'SYSTEM' in line.upper():
                current_category = "System Events"
            elif 'SESSION' in line.upper():
                current_category = "Session Events"
            elif 'ERROR' in line.upper():
                current_category = "Error Events"
            
            # Parse event definition
            match = re.search(
                r'public\s+static\s+final\s+String\s+(\w+)\s*=\s*"([^"]+)"',
                line
            )
            if match:
                const_name, event_name = match.groups()
                events.append(EventDefinition(
                    name=event_name,
                    constant_name=const_name,
                    platform="android",
                    category=current_category,
                    line_number=i
                ))
        
        return events

    @staticmethod
    def parse_ios(filepath: str) -> List[EventDefinition]:
        """Parse iOS AnalyticsEvents.swift file."""
        events = []
        content = Path(filepath).read_text(encoding='utf-8')
        
        current_category = "Uncategorized"
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if 'SCREEN VIEW' in line.upper() and '===' in lines[i-2] if i > 1 else False:
                current_category = "Screen View Events"
            elif 'USER INTERACTION' in line.upper():
                current_category = "User Interaction Events"
            elif 'AUTHENTICATION' in line.upper():
                current_category = "Authentication Events"
            elif 'PAYMENT' in line.upper():
                current_category = "Payment Events"
            elif 'FEATURE USAGE' in line.upper():
                current_category = "Feature Usage Events"
            elif 'SYSTEM' in line.upper():
                current_category = "System Events"
            elif 'SESSION' in line.upper():
                current_category = "Session Events"
            elif 'ERROR' in line.upper():
                current_category = "Error Events"
            
            # Parse event definition
            match = re.search(
                r'public\s+static\s+let\s+(\w+)\s*=\s*"([^"]+)"',
                line
            )
            if match:
                const_name, event_name = match.groups()
                events.append(EventDefinition(
                    name=event_name,
                    constant_name=const_name,
                    platform="ios",
                    category=current_category,
                    line_number=i
                ))
        
        return events

    @staticmethod
    def parse_schema(filepath: str) -> List[str]:
        """Parse JSON schema to extract expected event names."""
        content = Path(filepath).read_text(encoding='utf-8')
        schema = json.loads(content)
        
        # Extract enum values from event_name property
        event_enum = schema.get('properties', {}).get('event_name', {}).get('enum', [])
        return event_enum


class ParityAuditor:
    """Performs parity audit between platforms."""
    
    def __init__(
        self,
        android_file: str,
        ios_file: str,
        schema_file: str
    ):
        self.android_file = android_file
        self.ios_file = ios_file
        self.schema_file = schema_file
        self.parser = EventParser()
    
    def run_audit(self) -> ParityReport:
        """Execute the full parity audit."""
        report = ParityReport(
            audit_date=datetime.now().isoformat()
        )
        
        # Parse all sources
        report.android_events = self.parser.parse_android(self.android_file)
        report.ios_events = self.parser.parse_ios(self.ios_file)
        report.schema_events = self.parser.parse_schema(self.schema_file)
        
        # Compare events
        android_names = {e.name: e for e in report.android_events}
        ios_names = {e.name: e for e in report.ios_events}
        
        all_event_names = set(android_names.keys()) | set(ios_names.keys())
        
        for event_name in all_event_names:
            in_android = event_name in android_names
            in_ios = event_name in ios_names
            
            if in_android and in_ios:
                report.matched_events.append(android_names[event_name])
            elif in_android:
                report.android_only.append(android_names[event_name])
            elif in_ios:
                report.ios_only.append(ios_names[event_name])
        
        # Check schema compliance
        schema_set = set(report.schema_events)
        for event_name in all_event_names:
            if event_name not in schema_set:
                report.schema_mismatches.append(event_name)
        
        return report


class ReportFormatter:
    """Formats parity reports in various output formats."""
    
    @staticmethod
    def to_console(report: ParityReport) -> str:
        """Format report for console output."""
        lines = [
            "=" * 70,
            "📱 ANDROID / iOS EVENT PARITY AUDIT REPORT",
            "=" * 70,
            f"Audit Date: {report.audit_date}",
            f"Status: {report.status}",
            f"Parity Score: {report.parity_score}%",
            "",
            "-" * 70,
            "📊 SUMMARY",
            "-" * 70,
            f"Total Expected Events: {report.total_expected}",
            f"Android Events: {len(report.android_events)}",
            f"iOS Events: {len(report.ios_events)}",
            f"Matched Events: {report.matched_count}",
            f"Android Only: {len(report.android_only)}",
            f"iOS Only: {len(report.ios_only)}",
            f"Schema Mismatches: {len(report.schema_mismatches)}",
            "",
        ]
        
        if report.android_only:
            lines.extend([
                "-" * 70,
                "❌ ANDROID-ONLY EVENTS (Missing in iOS)",
                "-" * 70,
            ])
            for event in report.android_only:
                lines.append(f"  • {event.name} ({event.constant_name})")
            lines.append("")
        
        if report.ios_only:
            lines.extend([
                "-" * 70,
                "❌ iOS-ONLY EVENTS (Missing in Android)",
                "-" * 70,
            ])
            for event in report.ios_only:
                lines.append(f"  • {event.name} ({event.constant_name})")
            lines.append("")
        
        if report.schema_mismatches:
            lines.extend([
                "-" * 70,
                "⚠️  SCHEMA MISMATCHES (Not in schema)",
                "-" * 70,
            ])
            for event_name in report.schema_mismatches:
                lines.append(f"  • {event_name}")
            lines.append("")
        
        if report.parity_score == 100:
            lines.extend([
                "-" * 70,
                "✅ ALL EVENTS MATCH PERFECTLY!",
                "-" * 70,
            ])
        
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    @staticmethod
    def to_markdown(report: ParityReport) -> str:
        """Format report as Markdown."""
        lines = [
            "# 📱 Event Parity Audit Report",
            "",
            f"**Audit Date**: {report.audit_date}",
            f"**Status**: {report.status}",
            f"**Parity Score**: {report.parity_score}%",
            "",
            "## 📊 Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Total Expected Events | {report.total_expected} |",
            f"| Android Events | {len(report.android_events)} |",
            f"| iOS Events | {len(report.ios_events)} |",
            f"| Matched Events | {report.matched_count} |",
            f"| Android Only | {len(report.android_only)} |",
            f"| iOS Only | {len(report.ios_only)} |",
            f"| Schema Mismatches | {len(report.schema_mismatches)} |",
            "",
        ]
        
        if report.android_only:
            lines.extend([
                "## ❌ Android-Only Events",
                "",
                "| Event Name | Constant | Category | Line |",
                "|------------|----------|----------|------|",
            ])
            for event in report.android_only:
                lines.append(f"| {event.name} | {event.constant_name} | {event.category} | {event.line_number} |")
            lines.append("")
        
        if report.ios_only:
            lines.extend([
                "## ❌ iOS-Only Events",
                "",
                "| Event Name | Constant | Category | Line |",
                "|------------|----------|----------|------|",
            ])
            for event in report.ios_only:
                lines.append(f"| {event.name} | {event.constant_name} | {event.category} | {event.line_number} |")
            lines.append("")
        
        if report.schema_mismatches:
            lines.extend([
                "## ⚠️ Schema Mismatches",
                "",
                "These events are not defined in the shared schema:",
                "",
            ])
            for event_name in report.schema_mismatches:
                lines.append(f"- `{event_name}`")
            lines.append("")
        
        # Matched events table
        lines.extend([
            "## ✅ Matched Events",
            "",
            "| Event Name | Android Constant | iOS Constant | Category |",
            "|------------|------------------|--------------|----------|",
        ])
        
        android_map = {e.name: e for e in report.android_events}
        ios_map = {e.name: e for e in report.ios_events}
        
        for event in sorted(report.matched_events, key=lambda e: e.name):
            android_const = android_map.get(event.name, event).constant_name
            ios_const = ios_map.get(event.name, event).constant_name
            lines.append(f"| `{event.name}` | `{android_const}` | `{ios_const}` | {event.category} |")
        
        lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def to_json(report: ParityReport) -> str:
        """Format report as JSON."""
        data = {
            "audit_date": report.audit_date,
            "status": report.status,
            "parity_score": report.parity_score,
            "summary": {
                "total_expected": report.total_expected,
                "android_count": len(report.android_events),
                "ios_count": len(report.ios_events),
                "matched_count": report.matched_count,
                "android_only_count": len(report.android_only),
                "ios_only_count": len(report.ios_only),
                "schema_mismatches_count": len(report.schema_mismatches)
            },
            "android_only": [
                {
                    "name": e.name,
                    "constant": e.constant_name,
                    "category": e.category,
                    "line": e.line_number
                }
                for e in report.android_only
            ],
            "ios_only": [
                {
                    "name": e.name,
                    "constant": e.constant_name,
                    "category": e.category,
                    "line": e.line_number
                }
                for e in report.ios_only
            ],
            "schema_mismatches": report.schema_mismatches,
            "matched_events": [
                {
                    "name": e.name,
                    "category": e.category
                }
                for e in report.matched_events
            ]
        }
        return json.dumps(data, indent=2)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Android / iOS Event Parity Audit Tool"
    )
    parser.add_argument(
        "--android",
        default="mobile-app/android/app/src/main/java/com/soulsense/AnalyticsEvents.java",
        help="Path to Android AnalyticsEvents.java file"
    )
    parser.add_argument(
        "--ios",
        default="mobile-app/ios/SoulSense/AnalyticsEvents.swift",
        help="Path to iOS AnalyticsEvents.swift file"
    )
    parser.add_argument(
        "--schema",
        default="shared/analytics/event_schema.json",
        help="Path to event schema JSON file"
    )
    parser.add_argument(
        "--format",
        choices=["console", "markdown", "json"],
        default="console",
        help="Output format"
    )
    parser.add_argument(
        "--output",
        help="Output file path (default: stdout)"
    )
    parser.add_argument(
        "--fail-on-mismatch",
        action="store_true",
        help="Exit with non-zero code if mismatches found"
    )
    
    args = parser.parse_args()
    
    # Resolve paths relative to project root
    project_root = Path(__file__).parent.parent
    
    android_path = project_root / args.android
    ios_path = project_root / args.ios
    schema_path = project_root / args.schema
    
    # Verify files exist
    errors = []
    if not android_path.exists():
        errors.append(f"Android file not found: {android_path}")
    if not ios_path.exists():
        errors.append(f"iOS file not found: {ios_path}")
    if not schema_path.exists():
        errors.append(f"Schema file not found: {schema_path}")
    
    if errors:
        print("ERROR: Missing required files:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)
    
    # Run audit
    auditor = ParityAuditor(
        android_file=str(android_path),
        ios_file=str(ios_path),
        schema_file=str(schema_path)
    )
    
    report = auditor.run_audit()
    
    # Format output
    formatter = ReportFormatter()
    
    if args.format == "markdown":
        output = formatter.to_markdown(report)
    elif args.format == "json":
        output = formatter.to_json(report)
    else:
        output = formatter.to_console(report)
    
    # Write output
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding='utf-8')
        print(f"Report written to: {output_path}")
    else:
        print(output)
    
    # Exit with error code if requested and mismatches found
    if args.fail_on_mismatch and (report.android_only or report.ios_only):
        sys.exit(1)
    
    if report.parity_score < 90:
        sys.exit(2)  # Critical parity failure
    elif report.parity_score < 100:
        sys.exit(1)  # Non-perfect parity


if __name__ == "__main__":
    main()
