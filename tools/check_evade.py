import json
import os
import sys

# add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tetrapod import Tetrapod

BASE = os.path.dirname(__file__)
SAMPLES = os.path.join(BASE, '..', 'tuning', 'evade_samples.json')


def load_samples(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    Tetrapod.default_load()
    samples = load_samples(SAMPLES)
    print('Loaded', len(samples), 'evade samples')
    for s in samples:
        text = s.get('text')
        is_spam, score, details = Tetrapod.is_spam(text)
        print(f"[{s.get('id')}]", 'SPAM' if is_spam else 'PASS', 'score=',
              score, 'text=', text)
        print('    note:', s.get('note'))
        print('    details:', details)
        print()


if __name__ == '__main__':
    main()
