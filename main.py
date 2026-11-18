"""
Densify - main.py  (FastAPI backend)

Browser is server se JSON mein baat karta hai:
  GET  /                 -> web page (static/index.html)
  GET  /api/sample       -> sample data (microservices, ya replicas wala)
  GET  /api/random?n=20  -> n random containers (replicas=true: anti-affinity groups ke saath)
  POST /api/schedule     -> containers bhejo, har algorithm ka placement wapas lo
  GET  /api/experiment   -> random inputs par algorithms ka comparison

Chalane ke liye:  fastapi dev main.py   phir browser mein  http://127.0.0.1:8000
"""

import time

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from scheduler import Container, first_fit, best_fit, first_fit_decreasing
from optimal import branch_and_bound, lower_bound, largest_group
from constraints import conflict_graph, welsh_powell
from samples import MICROSERVICES, REPLICATED, NODE_CPU, NODE_MEM
from analysis import GREEDY, random_containers, quality_experiment, runtime_experiment

app = FastAPI(title="Densify")


# ---------------------------------------------------------------
# Request ka shape (Pydantic): galat data aaya to FastAPI khud error dega
# ---------------------------------------------------------------

class ContainerIn(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    cpu: int = Field(gt=0)        # millicores, 0 se bada
    mem: int = Field(gt=0)        # MiB, 0 se bada
    group: str = Field("", max_length=40)   # anti-affinity group (khaali = koi rule nahi)


class ScheduleRequest(BaseModel):
    node_cpu: int = Field(gt=0)
    node_mem: int = Field(gt=0)
    containers: list[ContainerIn] = Field(max_length=500)


# ---------------------------------------------------------------
# Helper: Python objects ko JSON-friendly dict mein badalna
# ---------------------------------------------------------------

def container_dict(c):
    return {"name": c.name, "cpu": c.cpu, "mem": c.mem, "group": c.group}


def nodes_to_json(nodes):
    return [{
        "name": nd.name,
        "cpu_used": nd.cpu_used,
        "mem_used": nd.mem_used,
        "containers": [container_dict(c) for c in nd.containers],
    } for nd in nodes]


def run_timed(algo, containers, cpu_cap, mem_cap):
    """Algorithm chalao aur time (ms) naapo."""
    start = time.perf_counter()
    nodes = algo(containers, cpu_cap, mem_cap)
    ms = (time.perf_counter() - start) * 1000
    return nodes, round(ms, 3)


# ---------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------

@app.get("/api/sample")
def get_sample(which: str = "microservices"):
    data = REPLICATED if which == "replicas" else MICROSERVICES
    return {
        "node_cpu": NODE_CPU,
        "node_mem": NODE_MEM,
        "containers": [container_dict(c) for c in data],
    }


@app.get("/api/random")
def get_random(n: int = Query(20, ge=1, le=500), seed: int = 0, replicas: bool = False):
    cs = random_containers(n, seed, replicas)
    return {
        "node_cpu": NODE_CPU,
        "node_mem": NODE_MEM,
        "containers": [container_dict(c) for c in cs],
    }


@app.post("/api/schedule")
def schedule(req: ScheduleRequest):
    containers = [Container(c.name, c.cpu, c.mem, c.group.strip()) for c in req.containers]
    cap = (req.node_cpu, req.node_mem)

    results = {}
    try:
        for name, algo in GREEDY.items():          # First Fit, Best Fit, FFD, Knapsack DP
            nodes, ms = run_timed(algo, containers, *cap)
            results[name] = {"nodes": nodes_to_json(nodes), "count": len(nodes),
                             "time_ms": ms}

        # Exact answer: zyada se zyada 3 second, phir jo best mila
        start = time.perf_counter()
        nodes, info = branch_and_bound(containers, *cap, time_limit=3.0)
        results["Optimal"] = {"nodes": nodes_to_json(nodes), "count": len(nodes),
                              "time_ms": round((time.perf_counter() - start) * 1000, 3),
                              "proven": info["optimal"],
                              "explored": info["explored"], "pruned": info["pruned"]}
    except ValueError as e:                 # koi container node se bada hai
        raise HTTPException(status_code=400, detail=str(e))

    # Anti-affinity: conflict graph aur Welsh-Powell colouring
    graph = conflict_graph(containers)
    colour, colours = welsh_powell(graph)
    anti_affinity = {
        "groups": len({c.group for c in containers if c.group}),
        "edges": sum(len(v) for v in graph.values()) // 2,
        "colours": colours,
        "largest_group": largest_group(containers),
    }

    return {
        "node_cpu": req.node_cpu,
        "node_mem": req.node_mem,
        "lower_bound": lower_bound(containers, *cap),
        "anti_affinity": anti_affinity,
        "results": results,
    }


@app.get("/api/experiment")
def experiment(n: int = Query(15, ge=4, le=24), trials: int = Query(50, ge=5, le=200)):
    """Quality: n containers ke `trials` random inputs, greedy vs optimum.
    Runtime: bade N par greedy algorithms ka time."""
    rows = quality_experiment(n, trials, NODE_CPU, NODE_MEM, seed=n * 1000)
    quality = {}
    for name in GREEDY:
        ratios = [r[name] / r["OPT"] for r in rows]
        quality[name] = {
            "avg_nodes": round(sum(r[name] for r in rows) / len(rows), 2),
            "pct_optimal": round(100 * sum(r[name] == r["OPT"] for r in rows) / len(rows), 1),
            "avg_ratio": round(sum(ratios) / len(ratios), 3),
            "worst_ratio": round(max(ratios), 3),
        }
    # Knapsack DP bade N par bahut slow hai (N = 1000 par ~3 s), isliye runtime
    # chart mein sirf teen greedy algorithms
    fast = {k: GREEDY[k] for k in ["First Fit", "Best Fit", "FFD"]}
    runtime = runtime_experiment([250, 500, 1000, 2000], 1, NODE_CPU, NODE_MEM, algos=fast)
    return {
        "n": n,
        "trials": len(rows),
        "opt_avg_nodes": round(sum(r["OPT"] for r in rows) / len(rows), 2),
        "quality": quality,
        "runtime": runtime,
    }


# ---------------------------------------------------------------
# Web page: static folder ki files browser ko do
# ---------------------------------------------------------------

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def home():
    return FileResponse("static/index.html")
