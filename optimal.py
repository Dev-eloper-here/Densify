"""
Densify - optimal.py

Sabse best (minimum nodes) answer nikalna: Branch and Bound.
Ye exponential time leta hai, isliye sirf chhote input (lagbhag 20 containers tak)
ke liye hai. Iska kaam: greedy algorithms ko check karna ki wo
optimum se kitna door hain.
"""

import math
import time

from scheduler import Node, size, check_input, merge_sort, first_fit_decreasing


def lower_bound(containers, cpu_cap, mem_cap):
    """Kam se kam kitne nodes lagenge hi lagenge.
    Total CPU / ek node ki CPU (upar round karo), memory ka bhi same.
    Anti-affinity: ek group ke k containers ko k alag nodes chahiye.
    Teeno mein jo sabse bada ho, utne nodes to chahiye hi."""
    total_cpu = sum(c.cpu for c in containers)
    total_mem = sum(c.mem for c in containers)
    return max(math.ceil(total_cpu / cpu_cap), math.ceil(total_mem / mem_cap),
               largest_group(containers))


def largest_group(containers):
    """Sabse bade anti-affinity group mein kitne containers hain (koi group nahi to 0)."""
    count = {}
    for c in containers:
        if c.group:
            count[c.group] = count.get(c.group, 0) + 1
    return max(count.values(), default=0)


def branch_and_bound(containers, cpu_cap, mem_cap, time_limit=5.0):
    """Saare possible placements ka tree explore karta hai, lekin jo raasta
    already mile best answer se behtar nahi ho sakta, use wahin kaat deta hai (prune).

    Returns: (nodes, info)
      info = {"optimal": True/False, "lower_bound", "explored", "pruned", "time_ms"}
      optimal=False matlab time limit khatam ho gayi, jo best mila wo de diya."""
    check_input(containers, cpu_cap, mem_cap)
    start = time.perf_counter()

    # Bade containers pehle: isse galat raaste jaldi pakde jaate hain
    items = merge_sort(containers, key=lambda c: size(c, cpu_cap, mem_cap))
    n = len(items)
    lb = lower_bound(items, cpu_cap, mem_cap)
    group_lb = largest_group(items)

    # Shuruaati answer (upper bound) FFD se. Isse behtar hi dhoondhna hai.
    best_nodes = first_fit_decreasing(items, cpu_cap, mem_cap)
    info = {"optimal": True, "lower_bound": lb, "explored": 0, "pruned": 0}

    # remaining_cpu[i] = items[i:] ki total CPU (aage ke bound ke liye)
    remaining_cpu = [0] * (n + 1)
    remaining_mem = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        remaining_cpu[i] = remaining_cpu[i + 1] + items[i].cpu
        remaining_mem[i] = remaining_mem[i + 1] + items[i].mem

    nodes = []                     # abhi ka partial placement

    def bound(i):
        """Is partial placement se aage, kam se kam kitne nodes lagenge?
        Jo containers bache hain, unhe pehle khule nodes ki khaali jagah mein
        maan lo; jo phir bhi bache, uske liye naye nodes."""
        free_cpu = sum(nd.cpu_cap - nd.cpu_used for nd in nodes)
        free_mem = sum(nd.mem_cap - nd.mem_used for nd in nodes)
        extra_cpu = max(0, math.ceil((remaining_cpu[i] - free_cpu) / cpu_cap))
        extra_mem = max(0, math.ceil((remaining_mem[i] - free_mem) / mem_cap))
        return max(len(nodes) + max(extra_cpu, extra_mem), group_lb)

    def search(i):
        nonlocal best_nodes
        if time.perf_counter() - start > time_limit:
            info["optimal"] = False
            return
        info["explored"] += 1

        if i == n:                                     # sab rakh diye
            if len(nodes) < len(best_nodes):
                best_nodes = copy_nodes(nodes)         # naya best mila
            return

        if bound(i) >= len(best_nodes):                # isse behtar nahi ho sakta
            info["pruned"] += 1
            return

        c = items[i]
        tried = set()
        # Option 1: kisi khule node mein rakho
        for node in nodes:
            # same bhare hue nodes (aur same groups) = same result
            state = (node.cpu_used, node.mem_used,
                     frozenset(x.group for x in node.containers if x.group))
            if state in tried:
                continue
            tried.add(state)
            if node.can_fit(c):
                node.place(c)
                search(i + 1)
                node.remove_last()                     # wapas lo (backtrack)
                if len(best_nodes) == lb:              # lower bound mil gaya, bas
                    return

        # Option 2: naya node kholo
        if len(nodes) + 1 < len(best_nodes):
            new = Node(f"node-{len(nodes) + 1}", cpu_cap, mem_cap)
            new.place(c)
            nodes.append(new)
            search(i + 1)
            nodes.pop()
        else:
            info["pruned"] += 1        # naya node kholna best se behtar nahi hoga

    if len(best_nodes) > lb:       # agar FFD already lower bound par hai to wahi optimum
        search(0)

    info["time_ms"] = round((time.perf_counter() - start) * 1000, 2)
    return best_nodes, info


def copy_nodes(nodes):
    """Abhi ke placement ki ek alag copy (warna backtrack mein badal jayegi)."""
    result = []
    for nd in nodes:
        new = Node(nd.name, nd.cpu_cap, nd.mem_cap)
        for c in nd.containers:
            new.place(c)
        result.append(new)
    return result
