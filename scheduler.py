"""
Densify - scheduler.py

Is file mein do cheezein hain:
  1. Problem ka model: Container (app) aur Node (server)
  2. Greedy placement algorithms: First Fit, Best Fit, First Fit Decreasing
  (Anti-affinity: can_fit() group bhi check karta hai, isliye har algorithm
   apne aap is rule ko maanta hai.)

Units (Kubernetes jaise):
  CPU    -> millicores   (1000m = 1 CPU core)
  Memory -> MiB          (1024 MiB = 1 GiB)
Integers use kar rahe hain taaki float wali rounding galti (0.1 + 0.2) na aaye.
"""

from dataclasses import dataclass, field


# ---------------------------------------------------------------
# 1. Model
# ---------------------------------------------------------------

@dataclass
class Container:
    name: str
    cpu: int          # millicores
    mem: int          # MiB
    group: str = ""   # anti-affinity group: same group wale do containers ek node par nahi


@dataclass
class Node:
    name: str
    cpu_cap: int                      # is node ki total CPU
    mem_cap: int                      # is node ki total memory
    containers: list = field(default_factory=list)
    cpu_used: int = 0
    mem_used: int = 0

    def can_fit(self, c):
        """Kya container c is node mein aa jayega? Dono resources check,
        aur anti-affinity: is node par c ke group ka koi container na ho."""
        if self.cpu_used + c.cpu > self.cpu_cap or self.mem_used + c.mem > self.mem_cap:
            return False
        return not self.has_conflict(c)

    def has_conflict(self, c):
        """Is node par c ke hi group ka koi container pehle se hai?"""
        if not c.group:
            return False
        return any(other.group == c.group for other in self.containers)

    def place(self, c):
        """Container c ko is node par rakh do."""
        self.containers.append(c)
        self.cpu_used += c.cpu
        self.mem_used += c.mem

    def remove_last(self):
        """Aakhri rakha hua container wapas hata do (Branch and Bound mein kaam aayega)."""
        c = self.containers.pop()
        self.cpu_used -= c.cpu
        self.mem_used -= c.mem
        return c

    def slack_after(self, c):
        """c rakhne ke baad kitni khaali jagah bachegi (0 se 2 ke beech).
        CPU aur memory dono ka bacha hua hissa (fraction) jod dete hain."""
        cpu_left = (self.cpu_cap - self.cpu_used - c.cpu) / self.cpu_cap
        mem_left = (self.mem_cap - self.mem_used - c.mem) / self.mem_cap
        return cpu_left + mem_left


def size(c, cpu_cap, mem_cap):
    """Container ka 'size' ek number mein: jo resource zyada maanga hai,
    uska fraction (dominant resource). Jaise 2000m / 4000m = 0.5"""
    return max(c.cpu / cpu_cap, c.mem / mem_cap)


def check_input(containers, cpu_cap, mem_cap):
    """Agar koi container akele hi node se bada hai, to wo kahin fit nahi hoga."""
    for c in containers:
        if c.cpu > cpu_cap or c.mem > mem_cap:
            raise ValueError(f"'{c.name}' ({c.cpu}m CPU, {c.mem} MiB) is bigger than "
                             f"a node, so it can never be placed")


def open_new_node(nodes, cpu_cap, mem_cap):
    """Ek naya khaali node chalu karo aur list mein jod do."""
    node = Node(f"node-{len(nodes) + 1}", cpu_cap, mem_cap)
    nodes.append(node)
    return node


# ---------------------------------------------------------------
# 2. Greedy algorithms
# ---------------------------------------------------------------

def first_fit(containers, cpu_cap, mem_cap):
    """Har container ko PEHLE node par rakho jismein wo fit ho jaye.
    Kahin fit na ho to naya node kholo.
    Time: O(n * m)   (n = containers, m = nodes)"""
    check_input(containers, cpu_cap, mem_cap)
    nodes = []
    for c in containers:
        target = None
        for node in nodes:
            if node.can_fit(c):
                target = node
                break                     # pehla mil gaya, aage mat dekho
        if target is None:
            target = open_new_node(nodes, cpu_cap, mem_cap)
        target.place(c)
    return nodes


def best_fit(containers, cpu_cap, mem_cap):
    """Har container ko us node par rakho jahan rakhne ke baad
    SABSE KAM jagah bache (sabse 'tight' fit).
    Time: O(n * m)"""
    check_input(containers, cpu_cap, mem_cap)
    nodes = []
    for c in containers:
        target = None
        best_slack = None
        for node in nodes:                # saare nodes dekhne padenge
            if node.can_fit(c):
                s = node.slack_after(c)
                if best_slack is None or s < best_slack:
                    best_slack = s
                    target = node
        if target is None:
            target = open_new_node(nodes, cpu_cap, mem_cap)
        target.place(c)
    return nodes


def merge_sort(items, key):
    """Divide and conquer: list ko aadha-aadha todo, dono sort karo, phir jodo.
    Yahan DESCENDING order (bada pehle). Time: O(n log n)"""
    if len(items) <= 1:
        return items[:]
    mid = len(items) // 2
    left = merge_sort(items[:mid], key)
    right = merge_sort(items[mid:], key)

    merged = []
    i = j = 0
    while i < len(left) and j < len(right):
        if key(left[i]) >= key(right[j]):     # bada wala pehle
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])                    # jo bacha, seedha jod do
    merged.extend(right[j:])
    return merged


def first_fit_decreasing(containers, cpu_cap, mem_cap):
    """Pehle containers ko size ke hisaab se bade se chhote sort karo,
    phir First Fit chalao. Bade pehle jaate hain, chhote baad mein gaps bharte hain.
    Time: O(n log n) sort + O(n * m) placement"""
    ordered = merge_sort(containers, key=lambda c: size(c, cpu_cap, mem_cap))
    return first_fit(ordered, cpu_cap, mem_cap)
