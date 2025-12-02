import time
import statistics
import sys
import platform
from tetrapod import Tetrapod

# load dictionaries/config
Tetrapod.default_load()

# build a 120-character test message (realistic looking)
base = "안녕하세요. 지금 특가 이벤트! www.example.com 방문하세요. 연락처 010-1234-5678. "
if len(base) < 120:
    base = base + ("가" * (120 - len(base)))
msg = base[:120]

# warmup (first call may include lazy imports)
Tetrapod.is_spam(msg)

N = 1000
times = []
for i in range(N):
    t0 = time.perf_counter()
    Tetrapod.is_spam(msg)
    t1 = time.perf_counter()
    times.append(t1 - t0)

total = sum(times)
avg = total / N
median = statistics.median(times)
mn = min(times)
mx = max(times)

print(f"Python: {sys.version.splitlines()[0]}")
print(f"Platform: {platform.platform()}")
print(f"Message length: {len(msg)} chars")
print(f"Iterations: {N}")
print(f"Total time: {total:.6f} s")
print(f"Average: {avg*1000:.4f} ms per message")
print(f"Median: {median*1000:.4f} ms")
print(f"Min: {mn*1000:.4f} ms, Max: {mx*1000:.4f} ms")
