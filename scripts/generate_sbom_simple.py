#!/usr/bin/env python3
"""Simple SBOM Generator Test"""

import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Simple SBOM Generator")
    parser.add_argument("--output", "-o", default="sbom.json", help="Output file")
    args = parser.parse_args()
    print(f"Would generate SBOM to: {args.output}")
    print("SBOM generation script works!")

if __name__ == "__main__":
    main()