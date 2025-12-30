"""Command-line interface for Phish JSON formatter."""

import argparse
import sys
from pathlib import Path

from .phish_json_formatter import format_dir, format_file


def main() -> int:
    """Run the formatter CLI."""
    parser = argparse.ArgumentParser(
        description="Format raw Phish show JSON to normalized schema",
        prog="phish_json_formatter"
    )
    
    parser.add_argument(
        "--in",
        "--input",
        dest="input",
        required=True,
        help="Input file or directory path"
    )
    parser.add_argument(
        "--out",
        "--output",
        dest="output",
        required=True,
        help="Output file or directory path"
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    try:
        if input_path.is_file():
            print(f"Formatting single file: {input_path}")
            format_file(input_path, output_path)
            print(f"[OK] Output written to: {output_path}")
        elif input_path.is_dir():
            print(f"Formatting directory: {input_path}")
            format_dir(input_path, output_path)
            print(f"[OK] All files processed. Output in: {output_path}")
        else:
            print(f"[ERROR] Input path does not exist: {input_path}", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
