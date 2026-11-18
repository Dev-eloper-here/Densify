"""
Densify - test_densify.py
Edge cases aur correctness check. Chalane ke liye:  python test_densify.py
"""

from itertools import product

from scheduler import Container, first_fit, best_fit, first_fit_decreasing, merge_sort
from optimal import branch_and_bound
from analysis import random_containers, is_valid, GREEDY
from constraints import conflict_graph, welsh_powell, is_proper_colouring

CPU, MEM = 4000, 8192
ALL = dict(GREEDY, **{"B&B": lambda cs, c, m: branch_and_bound(cs, c, m)[0]})


def brute_force(containers, cpu_cap, mem_cap):
    """Har container ko har possible node number do (n^n tareeke), sabse kam
    nodes wala valid tareeka lo. Sirf bahut chhote n ke liye."""
    n = len(containers)
    best = n
    for labels in product(range(n), repeat=n):
        used = set(labels)
        if len(used) >= best:
            continue
        ok = True
        for b in used:
            group = [containers[i] for i in range(n) if labels[i] == b]
            if sum(c.cpu for c in group) > cpu_cap or sum(c.mem for c in group) > mem_cap:
                ok = False
                break
            tags = [c.group for c in group if c.group]
            if len(tags) != len(set(tags)):          # anti-affinity
                ok = False
                break
        if ok:
            best = len(used)
    return best


def test_empty():
    for name, algo in ALL.items():
        assert algo([], CPU, MEM) == [], name


def test_exact_fit():
    cs = [Container("full", CPU, MEM), Container("small", 250, 256)]
    for name, algo in ALL.items():
        assert len(algo(cs, CPU, MEM)) == 2, name


def test_too_big():
    cs = [Container("huge", CPU + 1, 256)]
    for name, algo in ALL.items():
        try:
            algo(cs, CPU, MEM)
            assert False, name + " ne error nahi diya"
        except ValueError:
            pass


def test_identical():
    cs = [Container(f"c{i}", 1000, 2048) for i in range(10)]   # 4 per node
    for name, algo in ALL.items():
        assert len(algo(cs, CPU, MEM)) == 3, name


def test_one_dimension_full():
    # CPU khatam hai lekin memory bachi hai -> naya node chahiye
    cs = [Container("cpu-heavy", 4000, 256), Container("tiny", 250, 256)]
    for name, algo in ALL.items():
        assert len(algo(cs, CPU, MEM)) == 2, name


def test_merge_sort():
    import random
    rng = random.Random(7)
    for _ in range(200):
        xs = [rng.randint(0, 50) for _ in range(rng.randint(0, 30))]
        assert merge_sort(xs, key=lambda x: x) == sorted(xs, reverse=True)


def test_valid_and_optimal():
    """Random inputs: har answer valid ho; B&B = brute force (n <= 7)."""
    checked = 0
    for seed in range(300):
        n = 1 + seed % 7
        cs = random_containers(n, seed)
        for name, algo in ALL.items():
            assert is_valid(algo(cs, CPU, MEM), cs, CPU, MEM), name
        bb_nodes, info = branch_and_bound(cs, CPU, MEM)
        assert info["optimal"]
        assert len(bb_nodes) == brute_force(cs, CPU, MEM), seed
        for name in GREEDY:
            assert len(ALL[name](cs, CPU, MEM)) >= len(bb_nodes)
        checked += 1
    return checked


def test_anti_affinity_optimal():
    """Replicas wale random inputs: sab valid; B&B = brute force (n <= 7)."""
    checked = 0
    for seed in range(200):
        n = 2 + seed % 6
        cs = random_containers(n, 50000 + seed, replicas=True)
        for name, algo in ALL.items():
            assert is_valid(algo(cs, CPU, MEM), cs, CPU, MEM), name
        bb_nodes, info = branch_and_bound(cs, CPU, MEM)
        assert info["optimal"] and len(bb_nodes) == brute_force(cs, CPU, MEM), seed
        checked += 1
    return checked


def test_replicas_spread():
    cs = [Container(f"web-{i}", 250, 256, "web") for i in range(4)]   # chhote, par ek group
    for name, algo in ALL.items():
        assert len(algo(cs, CPU, MEM)) == 4, name          # 4 alag nodes chahiye


def test_knapsack_bigger_inputs():
    for seed in range(20):
        cs = random_containers(60, 7000 + seed, replicas=seed % 2 == 0)
        assert is_valid(GREEDY["Knapsack DP"](cs, CPU, MEM), cs, CPU, MEM)


def test_welsh_powell():
    for seed in range(100):
        cs = random_containers(25, 9000 + seed, replicas=True)
        graph = conflict_graph(cs)
        colour, k = welsh_powell(graph)
        assert is_proper_colouring(graph, colour)
        biggest = max([sum(1 for c in cs if c.group == g) for g in {c.group for c in cs if c.group}],
                      default=1)
        assert k == max(biggest, 1)


if __name__ == "__main__":
    tests = [test_empty, test_exact_fit, test_too_big, test_identical,
             test_one_dimension_full, test_merge_sort, test_valid_and_optimal,
             test_anti_affinity_optimal, test_replicas_spread, test_knapsack_bigger_inputs,
             test_welsh_powell]
    for t in tests:
        out = t()
        extra = f" ({out} random inputs)" if out else ""
        print(f"PASS  {t.__name__}{extra}")
    print("Saare tests pass.")
