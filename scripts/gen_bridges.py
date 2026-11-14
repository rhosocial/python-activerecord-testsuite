# scripts/gen_bridges.py
"""Generate (or verify) the bridge files a backend needs for the shared suite.

A bridge is a file at the same feature-relative path as a testsuite test
module, containing one wildcard import. Keeping the path and stem identical is
what makes "this backend runs that feature" checkable rather than a matter of
trust.

Usage::

    python scripts/gen_bridges.py --feature-root ../tests/rhosocial/x_test/feature
    python scripts/gen_bridges.py --feature-root ... --check

``--check`` exits non-zero when a bridge is missing, so CI can enforce the
"every testsuite module is included" rule without rewriting files.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rhosocial.activerecord.testsuite.core.bridges import (  # noqa: E402
    bridge_target,
    expected_bridges,
    missing_bridges,
    testsuite_modules,
)

HEADER = """# {path}
# Generated bridge: do not add test logic here. Capability differences belong in
# the testsuite as @requires_protocol / @requires_functions markers.

from {target} import *  # noqa: F401,F403
"""


def generate(feature_root: Path, force: bool = False) -> list:
    created = []
    for module in testsuite_modules():
        target = feature_root / module
        if target.exists() and not force:
            continue
        dotted = bridge_target(f"feature/{module}")
        target.parent.mkdir(parents=True, exist_ok=True)
        header_path = str(target).replace("\\", "/")
        target.write_text(
            HEADER.format(path=header_path, target=dotted),
            encoding="utf-8",
        )
        created.append(module)
    return created


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feature-root", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    root = args.feature_root.resolve()
    if not root.is_dir():
        print(f"feature root not found: {root}", file=sys.stderr)
        return 2

    if args.check:
        missing = missing_bridges(root)
        print(f"expected {len(expected_bridges())} bridges, missing {len(missing)}")
        for path in missing:
            print(f"  missing: {path}")
        return 1 if missing else 0

    created = generate(root, force=args.force)
    print(f"created {len(created)} bridge(s) under {root}")
    for module in created:
        print(f"  + {module}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
