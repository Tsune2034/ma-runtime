"""
Mann-Whitney U test: Creative Paradox (research vs. creative semantic_jump)
Reproduces the statistic reported in CIIE v0.2, Section 6.3.
"""
import json
from collections import defaultdict

records = []
with open('../data/pilot_results_openrouter.jsonl') as f:
    for line in f:
        line = line.strip()
        if line:
            records.append(json.loads(line))

cats = defaultdict(list)
for r in records:
    sj = r.get('semantic_jump')
    if sj is not None:
        cats[r['category']].append(sj)

research = cats['research']
creative = cats['creative']

print(f"research n={len(research)}: {sorted(research)}")
print(f"creative n={len(creative)}: {sorted(creative)}")

# Manual Mann-Whitney U
def mann_whitney_u(x, y):
    u = 0
    for xi in x:
        for yi in y:
            if xi > yi:
                u += 1
            elif xi == yi:
                u += 0.5
    return u

U = mann_whitney_u(research, creative)
n1, n2 = len(research), len(creative)
mu_U = n1 * n2 / 2
sigma_U = ((n1 * n2 * (n1 + n2 + 1)) / 12) ** 0.5
z = (U - mu_U) / sigma_U

import math
# Two-tailed p-value (normal approximation)
p = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))

print(f"\nMann-Whitney U = {U}")
print(f"z = {z:.4f}")
print(f"p (two-tailed) ≈ {p:.4f}")
print(f"Interpretation: {'not significant' if p > 0.05 else 'significant'} at alpha=0.05")
