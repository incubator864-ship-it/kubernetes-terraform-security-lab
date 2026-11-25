"""Run from repository root: python3 -m workbench."""
import argparse
import json
from pathlib import Path
from .engine import compare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("examples/source.json"))
    parser.add_argument("--ingested", type=Path, default=Path("examples/ingested.json"))
    parser.add_argument("--rule", type=Path, default=Path("rules/console-login.json"))
    parser.add_argument("--labels", type=Path, default=Path("examples/labels.json"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = compare(*(json.loads(path.read_text()) for path in
                           (args.source, args.ingested, args.rule, args.labels)))
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, "Invalid lab input: {}\n".format(error))
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    # Missing or malformed telemetry is an unhealthy run, even when there are fewer alerts.
    if result["removed_malicious_ids"]:
        return 3
    if result["missing_source_ids"] or result["versions"]["tuned"]["counts"]["gaps"]:
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
