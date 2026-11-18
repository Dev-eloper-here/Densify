"""
Densify - constraints.py

Anti-affinity (graph colouring, Welsh-Powell)
   Ek service ke replicas (jaise web-1, web-2, web-3) ek hi node par nahi hone
   chahiye, warna wo node gira to poori service band. Inhe ek "group" dete hain.
   Conflict graph: har container ek vertex, same group ke do containers ke beech edge.
   Graph colouring: jude hue (conflicting) containers ko alag rang. Ek rang ke
   containers ek node share kar sakte hain. Jitne rang lage, kam se kam utne nodes.
   Placement khud scheduler.py ka can_fit() sambhalta hai (same group = conflict).
"""

from scheduler import merge_sort


# ---------------------------------------------------------------
# Conflict graph + Welsh-Powell colouring
# ---------------------------------------------------------------

def conflict_graph(containers):
    """Adjacency list: graph[i] = un containers ke index jinse i ka conflict hai."""
    graph = {i: set() for i in range(len(containers))}
    members = {}
    for i, c in enumerate(containers):
        if c.group:
            members.setdefault(c.group, []).append(i)
    for group in members.values():
        for a in group:
            for b in group:
                if a != b:
                    graph[a].add(b)
    return graph


def welsh_powell(graph):
    """Greedy graph colouring (Welsh-Powell):
      1. Vertices ko degree (kitne edges) ke hisaab se bade se chhote sort karo
      2. Pehle bina rang wale vertex ko naya rang do
      3. Usi rang ko list ke har us vertex ko do jiska koi padosi us rang ka nahi
      4. Jab tak sab rang na jaayein, repeat
    Returns: (colour dict {vertex: rang number}, kitne rang lage)
    Time: O(V^2 + E)"""
    order = merge_sort(list(graph), key=lambda v: len(graph[v]))   # zyada degree pehle
    colour = {}
    k = 0
    for v in order:
        if v in colour:
            continue
        colour[v] = k
        for u in order:
            if u not in colour and all(colour.get(w) != k for w in graph[u]):
                colour[u] = k
        k += 1
    return colour, k


def is_proper_colouring(graph, colour):
    """Har edge ke dono siron ka rang alag hai?"""
    return all(colour[a] != colour[b] for a in graph for b in graph[a])
