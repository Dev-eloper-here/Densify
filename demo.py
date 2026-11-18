"""
Densify - demo.py
Terminal mein teeno algorithms chala kar result dikhata hai.
Chalane ke liye:  python demo.py
"""

from scheduler import first_fit, best_fit, first_fit_decreasing
from knapsack import knapsack_fill
from optimal import branch_and_bound, lower_bound
from samples import MICROSERVICES, NODE_CPU, NODE_MEM


def bar(used, cap, width=20):
    """Text wala progress bar, jaise  [########------------]"""
    filled = round(width * used / cap)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def show(title, nodes):
    print(f"\n=== {title}: {len(nodes)} nodes ===")
    for node in nodes:
        cpu_pct = 100 * node.cpu_used / node.cpu_cap
        mem_pct = 100 * node.mem_used / node.mem_cap
        print(f"{node.name}  CPU {bar(node.cpu_used, node.cpu_cap)} {cpu_pct:5.1f}%"
              f"   MEM {bar(node.mem_used, node.mem_cap)} {mem_pct:5.1f}%")
        names = ", ".join(c.name for c in node.containers)
        print(f"         {names}")


if __name__ == "__main__":
    algorithms = [
        ("First Fit", first_fit),
        ("Best Fit", best_fit),
        ("First Fit Decreasing", first_fit_decreasing),
        ("Knapsack DP (Knapsack-Fill)", knapsack_fill),
    ]
    for title, algo in algorithms:
        nodes = algo(MICROSERVICES, NODE_CPU, NODE_MEM)
        show(title, nodes)

    # Sabse best answer, Branch and Bound se
    nodes, info = branch_and_bound(MICROSERVICES, NODE_CPU, NODE_MEM)
    show("Optimal (Branch and Bound)", nodes)
    print(f"\nLower bound = {lower_bound(MICROSERVICES, NODE_CPU, NODE_MEM)} nodes")
    print(f"Optimal pakka hai? {info['optimal']} | explored = {info['explored']}, "
          f"pruned = {info['pruned']}, time = {info['time_ms']} ms")
