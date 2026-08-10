"""CLI entry points (validated configs; no source edits per experiment)."""
import argparse
import sys


def main(argv=None):
    p = argparse.ArgumentParser("ct2i-benchmark")
    sub = p.add_subparsers(dest="cmd", required=True)
    for c in ["preflight", "data-acquire", "freeze-targets", "make-splits",
              "run-tests", "run-smoke", "run-microbenchmark", "run-pilot",
              "run-simulation-1-checks", "run-simulation-2", "validate-artifacts"]:
        sp = sub.add_parser(c)
        sp.add_argument("--config", default=None)
        sp.add_argument("--out", default=None)
    args = p.parse_args(argv)
    from . import runners
    return runners.dispatch(args)


if __name__ == "__main__":
    sys.exit(main())
