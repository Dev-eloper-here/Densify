"""
Densify - knapsack.py

Knapsack-Fill: har naye node ko 0/1 Knapsack (Dynamic Programming) se
sabse achhe tareeke se bharo, phir agla node.

  jab tak containers bache hain:
      naya node kholo
      bache hue containers mein se wo subset chuno jo node mein fit ho
      aur node ko sabse zyada bhare  (2-D 0/1 knapsack, DP)
      us subset ko node par rakho

DP ke liye resources ko chhote "units" mein ginte hain:
  CPU: 250 millicores = 1 unit,  Memory: 256 MiB = 1 unit
Container ki demand upar round hoti hai aur node ki capacity neeche,
isliye DP jo bhi chunega wo asal mein bhi fit hoga.
"""

from scheduler import Node, check_input, open_new_node

CPU_UNIT = 250   # millicores
MEM_UNIT = 256   # MiB


def units_up(x, unit):
    """Upar round karke units: 300m -> 2 units (500m)."""
    return -(-x // unit)


def best_subset(items, cpu_cap, mem_cap):
    """Ek node ke liye items ka sabse achha subset (unke index) lautao.

    2-D 0/1 Knapsack:
      dp[c][m] = c CPU-units aur m memory-units mein sabse zyada 'value'
      value    = container node ka kitna hissa bharta hai (CPU + memory)
    Anti-affinity: ek group se zyada se zyada EK container chuna ja sakta hai
    (multiple-choice knapsack). Bina group wala container apna alag group hai.
    Time: O(n * CU * MU),  CU x MU = DP table ka size (4 core, 8 GiB par 17 x 33)"""
    CU = cpu_cap // CPU_UNIT
    MU = mem_cap // MEM_UNIT

    # Items ko groups mein baanto
    groups = {}
    for idx, c in enumerate(items):
        key = c.group if c.group else f"#solo-{idx}"
        groups.setdefault(key, []).append(idx)
    group_list = list(groups.values())

    need = [(units_up(c.cpu, CPU_UNIT), units_up(c.mem, MEM_UNIT)) for c in items]
    # Value integer mein: cpu_units/CU + mem_units/MU ko CU*MU se guna kiya
    value = [cu * MU + mu * CU for cu, mu in need]

    dp = [[0] * (MU + 1) for _ in range(CU + 1)]     # abhi tak kuch nahi chuna
    picks = []                                       # har group ke liye: kis cell mein kaunsa item liya

    for g in group_list:
        new = [row[:] for row in dp]                 # default: is group se kuch mat lo
        pick = [[-1] * (MU + 1) for _ in range(CU + 1)]
        for idx in g:                                # ya is group ka EK item lo
            cu, mu = need[idx]
            for c in range(cu, CU + 1):
                for m in range(mu, MU + 1):
                    candidate = dp[c - cu][m - mu] + value[idx]
                    if candidate > new[c][m]:
                        new[c][m] = candidate
                        pick[c][m] = idx
        dp = new
        picks.append(pick)

    # Peeche se chalkar dekho kaunse items liye (reconstruction)
    chosen = []
    c, m = CU, MU
    for gi in range(len(group_list) - 1, -1, -1):
        idx = picks[gi][c][m]
        if idx != -1:
            chosen.append(idx)
            c -= need[idx][0]
            m -= need[idx][1]
    return chosen


def knapsack_fill(containers, cpu_cap, mem_cap):
    """Har node ko knapsack DP se bharo. Time: O(n * m * CU * MU)"""
    check_input(containers, cpu_cap, mem_cap)
    remaining = list(containers)
    nodes = []
    while remaining:
        node = open_new_node(nodes, cpu_cap, mem_cap)
        chosen = best_subset(remaining, cpu_cap, mem_cap)
        if not chosen:
            # Rounding ki wajah se DP kuch na chun paaye (bahut ajeeb sizes):
            # sabse pehla container akela rakh do, wo fit hota hi hai
            chosen = [0]
        for idx in chosen:
            node.place(remaining[idx])
        chosen_set = set(chosen)
        remaining = [c for i, c in enumerate(remaining) if i not in chosen_set]
    return nodes
