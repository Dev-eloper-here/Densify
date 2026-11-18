"""
Densify - analysis.py

Experiments (ADA ka "analysis" wala hissa):
  1. Quality: har algorithm kitne nodes leta hai, optimum se kitna door hai
  2. Runtime: input size (N) badhne par time kaise badhta hai
Random data fixed seed se banta hai, taaki har baar same result aaye.
"""

import random
import time

from scheduler import Container, first_fit, best_fit, first_fit_decreasing
from knapsack import knapsack_fill
from optimal import branch_and_bound, lower_bound

# Kubernetes mein aam taur par maange jaane wale requests
CPU_CHOICES = [250, 500, 750, 1000, 1500, 2000, 2500, 3000]          # millicores
MEM_CHOICES = [256, 512, 1024, 1536, 2048, 3072, 4096, 6144]          # MiB

GREEDY = {
    "First Fit": first_fit,
    "Best Fit": best_fit,
    "FFD": first_fit_decreasing,
    "Knapsack DP": knapsack_fill,
}


def random_containers(n, seed, replicas=False):
    """n random containers. Same seed = same containers.
    replicas=True: kuch containers 2-3 replicas wale groups mein (anti-affinity)."""
    rng = random.Random(seed)
    result = []
    while len(result) < n:
        cpu, mem = rng.choice(CPU_CHOICES), rng.choice(MEM_CHOICES)
        k = len(result)
        if replicas and rng.random() < 0.4:
            copies = min(rng.choice([2, 3]), n - k)
            for r in range(copies):
                result.append(Container(f"svc{k}-{r + 1}", cpu, mem, group=f"svc{k}"))
        else:
            result.append(Container(f"c{k}", cpu, mem))
    return result


def is_valid(nodes, containers, cpu_cap, mem_cap):
    """Answer sahi hai? (1) koi node overflow nahi, (2) ek node par ek group ka
    ek hi container, (3) har container exactly ek baar."""
    placed = []
    for nd in nodes:
        if sum(c.cpu for c in nd.containers) > cpu_cap:
            return False
        if sum(c.mem for c in nd.containers) > mem_cap:
            return False
        groups = [c.group for c in nd.containers if c.group]
        if len(groups) != len(set(groups)):          # anti-affinity toota
            return False
        placed.extend(id(c) for c in nd.containers)
    return sorted(placed) == sorted(id(c) for c in containers)


def time_ms(func, *args, repeat=3):
    """func ko kuch baar chala kar sabse kam time (milliseconds)."""
    best = None
    for _ in range(repeat):
        start = time.perf_counter()
        func(*args)
        t = (time.perf_counter() - start) * 1000
        best = t if best is None else min(best, t)
    return best


def quality_experiment(n, trials, cpu_cap, mem_cap, seed=0, time_limit=2.0):
    """Chhote N par: greedy vs exact optimum (Branch and Bound)."""
    rows = []
    for t in range(trials):
        cs = random_containers(n, seed + t)
        opt_nodes, info = branch_and_bound(cs, cpu_cap, mem_cap, time_limit)
        if not info["optimal"]:
            continue                       # optimum pakka nahi, is trial ko chhodo
        row = {"OPT": len(opt_nodes), "LB": info["lower_bound"]}
        for name, algo in GREEDY.items():
            row[name] = len(algo(cs, cpu_cap, mem_cap))
        rows.append(row)
    return rows


def runtime_experiment(sizes, trials, cpu_cap, mem_cap, seed=1000, algos=None):
    """Bade N par greedy algorithms ka time, aur lower bound se ratio."""
    algos = algos or GREEDY
    result = []
    for n in sizes:
        times = {name: [] for name in algos}
        ratio = {name: [] for name in algos}
        for t in range(trials):
            cs = random_containers(n, seed + t)
            lb = lower_bound(cs, cpu_cap, mem_cap)
            for name, algo in algos.items():
                times[name].append(time_ms(algo, cs, cpu_cap, mem_cap))
                ratio[name].append(len(algo(cs, cpu_cap, mem_cap)) / lb)
        result.append({
            "n": n,
            "time_ms": {k: sum(v) / len(v) for k, v in times.items()},
            "ratio_vs_lb": {k: sum(v) / len(v) for k, v in ratio.items()},
        })
    return result
