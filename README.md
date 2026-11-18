# Densify

**A Multi-Dimensional Container Scheduling Engine using Approximation Algorithms**
ADA project · B.Tech CSE, Semester III · Faculty of Technology, University of Delhi

Densify decides which server (node) each container should run on, so that no node runs out of CPU or memory and as few nodes as possible are used. This is the 2-D vector bin packing problem, which is NP-hard.

## Algorithms

| Algorithm | Paradigm | Time |
|---|---|---|
| First Fit | Greedy | O(n·m), worst O(n²) |
| Best Fit | Greedy | O(n·m), worst O(n²) |
| Merge sort | Divide and conquer | O(n log n) |
| First Fit Decreasing (FFD) | Greedy + sorting | O(n log n + n·m) |
| Knapsack-Fill | 0/1 knapsack, dynamic programming | O(n·m·W), W = DP table size |
| Welsh–Powell colouring (anti-affinity) | Graph algorithm | O(V² + E) |
| Lower bound | Math | O(n) |
| Branch and bound | Exact search with pruning | Exponential worst case |

n = containers, m = nodes opened.

**Anti-affinity:** containers with the same group (for example replicas `web-1`, `web-2`, `web-3`) are never placed on the same node. Every algorithm respects this rule; the conflict graph and its Welsh–Powell colouring show how many nodes the rule alone needs.

## Run it

```bash
python -m venv .venv
source .venv/Scripts/activate      # Windows Git Bash
pip install -r requirements.txt
fastapi dev main.py
```

Open http://127.0.0.1:8000 in a browser.

Terminal demo without the web app: `python demo.py`
Tests: `python test_densify.py`

## Files

| File | What it does |
|---|---|
| `scheduler.py` | Container and Node model; First Fit, Best Fit, merge sort, FFD |
| `knapsack.py` | Knapsack-Fill: fills each node with a 2-D 0/1 knapsack DP |
| `constraints.py` | Anti-affinity: conflict graph and Welsh–Powell colouring |
| `optimal.py` | Lower bound and branch and bound |
| `analysis.py` | Random input generator and experiments |
| `samples.py` | 15-microservice sample, replicas sample, node size |
| `main.py` | FastAPI backend (REST API) |
| `static/` | Web page: HTML, CSS, JavaScript, Chart.js |
| `demo.py` | Terminal demo |
| `test_densify.py` | Edge cases and correctness tests (branch and bound vs brute force) |

## Results (node: 4 vCPU, 8 GiB)

- 15-service sample: First Fit 6, Best Fit 6, FFD 5, Knapsack DP 4, optimal 4 nodes
- 200 random inputs with N = 20: FFD optimal in 84% of inputs, on average 2% above optimal
- Branch and bound matches brute force on 300 of 300 small inputs
