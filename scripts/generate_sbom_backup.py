#!/usr/bin/env python3
"""
SBOM Generation Script for Soul Sense Exam Platform

This script generates Software Bill of Materials (SBOM) in CycloneDX format
for dependency tracking and supply chain security.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SBOMGenerator:
    """Generates SBOM using CycloneDX for Python projects."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_dir = project_root / "backend" / "fastapi"
        self.requirements_file = self.backend_dir / "requirements.txt"
        self.security_requirements = project_root / "requirements-security.txt"

    def check_dependencies(self) -> bool:
        """Check if required tools are installed."""
        try:
            subprocess.run([sys.executable, "-m", "cyclonedx_py", "--help"],
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("cyclonedx-py not found. Install with: pip install cyclonedx-bom")
            return False

    def generate_sbom(self, output_file: Path, format: str = "json") -> bool:
        """Generate SBOM using CycloneDX."""
        try:
            cmd = [
                sys.executable, "-m", "cyclonedx_py",
                "requirements",
                "--requirements-file", str(self.requirements_file),
                "--output", str(output_file),
                "--format", format
            ]

            # Add security requirements if they exist
            if self.security_requirements.exists():
                cmd.extend(["--requirements-file", str(self.security_requirements)])

            logger.info(f"Generating SBOM with command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.backend_dir)

            if result.returncode == 0:
                logger.info(f"SBOM generated successfully: {output_file}")
                return True
            else:
                logger.error(f"SBOM generation failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error generating SBOM: {e}")
            return False

    def validate_sbom(self, sbom_file: Path) -> bool:
        """Validate the generated SBOM file."""
        if not sbom_file.exists():
            logger.error(f"SBOM file does not exist: {sbom_file}")
            return False

        try:
            with open(sbom_file, 'r') as f:
                data = json.load(f)

            # Basic validation
            if "bomFormat" not in data or data["bomFormat"] != "CycloneDX":
                logger.error("Invalid SBOM format")
                return False

            if "specVersion" not in data:
                logger.error("Missing specVersion in SBOM")
                return False

            components = data.get("components", [])
            logger.info(f"SBOM contains {len(components)} components")
            return True

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in SBOM file: {e}")
            return False
        except Exception as e:
            logger.error(f"Error validating SBOM: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Generate SBOM for Soul Sense Exam Platform")
    parser.add_argument("--output", "-o", type=str, default="sbom.json",
                       help="Output file path for SBOM")
    parser.add_argument("--format", "-f", choices=["json", "xml"], default="json",
                       help="SBOM output format")
    parser.add_argument("--validate-only", action="store_true",
                       help="Only validate existing SBOM file")
    parser.add_argument("--project-root", type=str, default=".",
                       help="Project root directory")

    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    output_file = project_root / args.output

    generator = SBOMGenerator(project_root)

    if args.validate_only:
        if generator.validate_sbom(output_file):
            logger.info("SBOM validation passed")
            sys.exit(0)
        else:
            logger.error("SBOM validation failed")
            sys.exit(1)

    # Check dependencies
    if not generator.check_dependencies():
        sys.exit(1)

    # Generate SBOM
    if generator.generate_sbom(output_file, args.format):
        # Validate the generated SBOM
        if generator.validate_sbom(output_file):
            logger.info("SBOM generation and validation completed successfully")
            sys.exit(0)
        else:
            logger.error("SBOM generation succeeded but validation failed")
            sys.exit(1)
    else:
        logger.error("SBOM generation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()</content>
<parameter name="filePath">c:\Users\Gupta\Downloads\SOUL_SENSE_EXAM\scripts\generate_sbom.py