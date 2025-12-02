import json
import os
import sys

# Ensure project root is on sys.path so we can import top-level modules when running
# this script from the tools/ folder (e.g. `python .\tools\tune.py`).
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tetrapod import Tetrapod

BASE = os.path.dirname(__file__) or '.'
SAMPLES = os.path.join(BASE, '..', 'tuning', 'samples.json')
CONFIG = os.path.join(BASE, '..', 'config', 'spam-config.json')
OUT = os.path.join(BASE, '..', 'config', 'spam-config.tuned.json')

# Simple grid search over a few params
keyword_weights = [1, 2, 3]
urgent_boosts = [0, 1, 2, 3]
repeat_boosts = [0, 1, 2, 3]
thresholds = [2, 3, 4, 5]


def load_samples(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def score_config(cfg, samples):
    Tetrapod.default_load()
    # override runtime config with provided cfg dict
    Tetrapod.spam_config.update(cfg)
    correct = 0
    for s in samples:
        is_spam, score, details = Tetrapod.is_spam(s['text'],
                                                   threshold=cfg.get(
                                                       'threshold', 3))
        if bool(is_spam) == bool(s['spam']):
            correct += 1
    return correct


def main():
    samples = load_samples(SAMPLES)
    # baseline config
    Tetrapod.default_load()
    base_cfg = Tetrapod.spam_config.copy()

    best = None
    best_score = -1
    total = len(samples)
    tried = 0
    for kw in keyword_weights:
        for ub in urgent_boosts:
            for rb in repeat_boosts:
                for th in thresholds:
                    cfg = base_cfg.copy()
                    cfg['weights'] = cfg.get('weights', {}).copy()
                    cfg['weights']['keyword'] = kw
                    cfg['urgent_money_boost'] = ub
                    cfg['repeat_name_boost'] = rb
                    cfg['threshold'] = th
                    tried += 1
                    correct = score_config(cfg, samples)
                    if correct > best_score:
                        best_score = correct
                        best = cfg.copy()
    print(f'Tried {tried} configs, best accuracy: {best_score}/{total}')
    print('Best config:')
    print(json.dumps(best, ensure_ascii=False, indent=2))
    # write tuned config
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(best, f, ensure_ascii=False, indent=2)
    print('Wrote tuned config to', OUT)


if __name__ == '__main__':
    main()
