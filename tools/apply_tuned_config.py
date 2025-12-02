import json
import os
import shutil
import datetime

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_PATH = os.path.join(BASE, 'config', 'spam-config.json')
TUNED_PATH = os.path.join(BASE, 'config', 'spam-config.tuned.json')


def deep_merge(a, b):
    """Recursively merge b into a and return a new dict.

    - If a key maps to dicts in both, merge recursively.
    - Otherwise, b's value overwrites a's value.
    """
    if not isinstance(a, dict):
        return b
    out = dict(a)
    for k, v in b.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def backup_file(path):
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    dst = path + '.bak.' + ts
    shutil.copy2(path, dst)
    return dst


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def summarize_changes(orig, tuned, merged):
    changed = {}
    # keys in tuned that differ from orig
    for k in tuned:
        if k not in orig or orig.get(k) != tuned.get(k):
            changed[k] = {'from': orig.get(k), 'to': tuned.get(k)}
    return changed


def main():
    if not os.path.exists(TUNED_PATH):
        print('No tuned config found at', TUNED_PATH)
        return 1
    if not os.path.exists(CONFIG_PATH):
        print('No base config found at', CONFIG_PATH)
        return 1

    orig = load_json(CONFIG_PATH)
    tuned = load_json(TUNED_PATH)

    merged = deep_merge(orig, tuned)

    # summarize
    changes = summarize_changes(orig, tuned, merged)
    if not changes:
        print(
            'Tuned config does not change any top-level keys vs base config.')
    else:
        print('Top-level changes to be applied:')
        for k, v in changes.items():
            print('-', k)
            print('    from:', v['from'])
            print('    to  :', v['to'])

    # backup
    backup = backup_file(CONFIG_PATH)
    print('Backed up original config to', backup)

    # write merged
    write_json(CONFIG_PATH, merged)
    print('Wrote merged config to', CONFIG_PATH)

    # also write a copy next to tuned for traceability
    merged_path = os.path.join(os.path.dirname(TUNED_PATH),
                               'spam-config.merged.json')
    write_json(merged_path, merged)
    print('Wrote merged copy to', merged_path)

    return 0


if __name__ == '__main__':
    exit(main())
