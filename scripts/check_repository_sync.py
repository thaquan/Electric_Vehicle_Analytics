"""Compare fetched repository content, allowing independent mirror histories."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()


def check(left, right):
    result = {'checked_at_utc': datetime.now(timezone.utc).isoformat(),
              'scope': 'Fetched refs; fetch both remotes immediately before running', 'refs': {}}
    for ref in (left, right):
        result['refs'][ref] = {'commit': git('rev-parse', '--verify', ref + '^{commit}'),
                              'tree': git('rev-parse', '--verify', ref + '^{tree}')}
    result['changed_paths'] = git('diff', '--name-only', left, right, '--').splitlines()
    result['status'] = 'passed' if result['refs'][left]['tree'] == result['refs'][right]['tree'] else 'failed'
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--left', default='origin/main')
    parser.add_argument('--right', default='github/main')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = check(args.left, args.right)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'] == 'passed' else 1)
