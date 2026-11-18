// Densify - app.js
// Page ka saara kaam: containers ki list sambhalna, backend ko fetch se
// request bhejna, aur result ko cards, Chart.js chart aur node list mein dikhana.

// ---------------------------------------------------------------
// 1. State: page ka data yahan rehta hai
// ---------------------------------------------------------------
let containers = [];          // [{name, cpu, mem, group}, ...]
let lastResult = null;        // /api/schedule ka pichhla jawab
let charts = {};              // Chart.js ke chart objects (naya banane se pehle purana hatana)

const ALGOS = ["First Fit", "Best Fit", "FFD", "Knapsack DP", "Optimal"];
const GREEDY = ["First Fit", "Best Fit", "FFD", "Knapsack DP"];
const COLORS = { "First Fit": "#B7C7D8", "Best Fit": "#8EC1EA", "FFD": "#2A6FAE",
                 "Knapsack DP": "#3E9C98", "Optimal": "#1C3550" };

const $ = (id) => document.getElementById(id);

// ---------------------------------------------------------------
// 2. Helpers
// ---------------------------------------------------------------

// fetch + JSON. Error aaye to FastAPI ka message nikal kar throw karo.
async function getJSON(url, options) {
  const res = await fetch(url, options);
  const data = await res.json();
  if (!res.ok) {
    const d = data.detail;
    throw new Error(Array.isArray(d) ? d.map((e) => e.msg).join("; ") : d);
  }
  return data;
}

const cores = (m) => +(m / 1000).toFixed(2);     // 3500 -> 3.5
const gib = (mi) => +(mi / 1024).toFixed(2);     // 6144 -> 6
const pct = (used, cap) => Math.round((100 * used) / cap);

// Button par "working..." dikhana jab tak kaam chal raha ho
async function busy(button, text, work) {
  const old = button.textContent;
  button.disabled = true;
  button.textContent = text;
  try { await work(); } finally { button.disabled = false; button.textContent = old; }
}

// ---------------------------------------------------------------
// 3. Containers ki table
// ---------------------------------------------------------------
function renderTable() {
  const tbody = $("container-tbody");
  tbody.innerHTML = "";
  containers.forEach((c, i) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${i + 1}</td><td></td><td></td><td></td><td></td>
                    <td><button class="del" data-i="${i}" title="Remove">&times;</button></td>`;
    // Inputs DOM se banate hain (value seedha set), taaki naam mein HTML ho to bhi safe rahe
    ["name", "cpu", "mem", "group"].forEach((field, k) => {
      const input = document.createElement("input");
      input.value = c[field] || "";
      if (field === "cpu" || field === "mem") { input.type = "number"; input.min = 1; }
      if (field === "group") input.placeholder = "none";
      input.dataset.i = i;
      input.dataset.field = field;
      tr.children[k + 1].appendChild(input);
    });
    tbody.appendChild(tr);
  });
  $("empty-msg").style.display = containers.length ? "none" : "block";
  $("count-info").textContent = containers.length ? `${containers.length} containers` : "";
}

// Table mein kuch type hua: state update karo
$("container-tbody").addEventListener("input", (e) => {
  const { i, field } = e.target.dataset;
  if (i === undefined) return;
  const isNumber = field === "cpu" || field === "mem";
  containers[i][field] = isNumber ? Number(e.target.value) : e.target.value;
});

// Delete button
$("container-tbody").addEventListener("click", (e) => {
  if (!e.target.classList.contains("del")) return;
  containers.splice(Number(e.target.dataset.i), 1);
  renderTable();
});

function setData(data) {
  $("node-cpu").value = data.node_cpu;
  $("node-mem").value = data.node_mem;
  containers = data.containers;
  renderTable();
  $("error").textContent = "";
}

$("btn-sample").addEventListener("click", async () => {
  setData(await getJSON("/api/sample"));
});

$("btn-replicas").addEventListener("click", async () => {
  setData(await getJSON("/api/sample?which=replicas"));
});

$("btn-random").addEventListener("click", async () => {
  const n = Number($("random-n").value) || 20;
  const seed = Math.floor(Math.random() * 100000);       // har click par naya data
  const replicas = $("random-replicas").checked;
  try { setData(await getJSON(`/api/random?n=${n}&seed=${seed}&replicas=${replicas}`)); }
  catch (err) { $("error").textContent = err.message; }
});

$("btn-add").addEventListener("click", () => {
  containers.push({ name: `app-${containers.length + 1}`, cpu: 500, mem: 512, group: "" });
  renderTable();
});

$("btn-clear").addEventListener("click", () => {
  containers = [];
  renderTable();
  $("result-panel").classList.add("hidden");
});

// ---------------------------------------------------------------
// 4. Scheduler chalana: POST /api/schedule
// ---------------------------------------------------------------
$("btn-run").addEventListener("click", () => busy($("btn-run"), "Running...", async () => {
  $("error").textContent = "";
  if (containers.length === 0) {
    $("error").textContent = "Add at least one container first.";
    return;
  }
  const body = {
    node_cpu: Number($("node-cpu").value),
    node_mem: Number($("node-mem").value),
    containers: containers,
  };
  try {
    lastResult = await getJSON("/api/schedule", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    renderResults();
  } catch (err) {
    $("error").textContent = "Error: " + err.message;
  }
}));

// ---------------------------------------------------------------
// 5. Result dikhana
// ---------------------------------------------------------------
function renderResults() {
  const { results, lower_bound } = lastResult;
  const best = results["Optimal"].count;

  // (a) Summary cards
  let html = "";
  for (const name of ALGOS) {
    const r = results[name];
    let sub = `${r.time_ms} ms`;
    if (name === "Optimal") sub += r.proven ? ` · ${r.explored} explored` : " · time limit hit";
    const label = results["Optimal"].proven ? "optimal" : "best found";
    const badge = r.count === best ? `<span class="badge">${label}</span>` : `<span class="badge" style="visibility:hidden">-</span>`;
    html += `<div class="card" style="--algo:${COLORS[name]}">
               <p class="label">${name === "Optimal" ? "Optimal (Branch & Bound)" : name}</p>
               <p class="value">${r.count}</p>
               <p class="sub">nodes · ${sub}</p>${badge}</div>`;
  }
  html += `<div class="card lb"><p class="label">Lower bound</p><p class="value">${lower_bound}</p>
           <p class="sub">no answer can use fewer nodes</p></div>`;
  $("summary").innerHTML = html;

  // (b) Kitne nodes bache
  const ff = results["First Fit"].count;
  const saved = ff - best;
  $("saving").innerHTML = saved > 0
    ? `Best placement saves <b>${saved} node${saved > 1 ? "s" : ""}</b> compared to First Fit (${Math.round((100 * saved) / ff)}% fewer servers).`
    : "First Fit is already optimal for this input.";
  if (!results["Optimal"].proven) {
    $("saving").innerHTML += " <span class='hint'>(Exact search stopped at the 3 s limit, so “Optimal” is the best found.)</span>";
  }

  // (b2) Anti-affinity ki jaankari (sirf jab groups hon)
  const aa = lastResult.anti_affinity;
  if (aa.groups > 0) {
    $("aa-info").innerHTML = `<b>Anti-affinity:</b> ${aa.groups} groups → conflict graph with ${aa.edges} edges. ` +
      `Welsh–Powell colouring needs <b>${aa.colours} colours</b>, so at least ${aa.colours} nodes are needed. ` +
      `Every algorithm keeps replicas of the same group on different nodes.`;
    $("aa-info").classList.remove("hidden");
  } else {
    $("aa-info").classList.add("hidden");
  }

  // (c) Algorithm tabs
  $("algo-tabs").innerHTML = ALGOS.map((a) => `<button data-algo="${a}">${a}</button>`).join("");
  showAlgo("FFD");
  $("result-panel").classList.remove("hidden");
}

$("algo-tabs").addEventListener("click", (e) => {
  if (e.target.dataset.algo) showAlgo(e.target.dataset.algo);
});

// Ek algorithm ke nodes: chart + node cards
function showAlgo(name) {
  document.querySelectorAll("#algo-tabs button").forEach((b) =>
    b.classList.toggle("active", b.dataset.algo === name));

  const { node_cpu, node_mem } = lastResult;
  const nodes = lastResult.results[name].nodes;

  // Chart.js: har node ke liye CPU% aur Memory% ke bars
  if (charts.node) charts.node.destroy();
  charts.node = new Chart($("node-chart"), {
    type: "bar",
    data: {
      labels: nodes.map((n) => n.name),
      datasets: [
        { label: "CPU used %", data: nodes.map((n) => pct(n.cpu_used, node_cpu)), backgroundColor: "#2A6FAE" },
        { label: "Memory used %", data: nodes.map((n) => pct(n.mem_used, node_mem)), backgroundColor: "#8EC1EA" },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: { y: { min: 0, max: 100, title: { display: true, text: "% of node used" } } },
      plugins: { title: { display: true, text: `${name}: ${nodes.length} nodes` } },
    },
  });

  // Node cards
  $("node-list").innerHTML = nodes.map((n) => `
    <div class="node">
      <h3>${n.name}</h3>
      <div class="meter"><span>CPU ${cores(n.cpu_used)} / ${cores(node_cpu)} cores</span><span>${pct(n.cpu_used, node_cpu)}%</span></div>
      <div class="bar"><span class="cpu" style="width:${pct(n.cpu_used, node_cpu)}%"></span></div>
      <div class="meter"><span>Memory ${gib(n.mem_used)} / ${gib(node_mem)} GiB</span><span>${pct(n.mem_used, node_mem)}%</span></div>
      <div class="bar"><span class="mem" style="width:${pct(n.mem_used, node_mem)}%"></span></div>
      <div class="chips">${n.containers.map((c) => `<span class="chip">${escapeHTML(c.name)}${c.group ? `<small>${escapeHTML(c.group)}</small>` : ""}</span>`).join("")}</div>
    </div>`).join("");
}

function escapeHTML(s) {
  return String(s).replace(/[&<>"']/g, (ch) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
}

// ---------------------------------------------------------------
// 6. Experiment: GET /api/experiment
// ---------------------------------------------------------------
$("btn-exp").addEventListener("click", () => busy($("btn-exp"), "Running... (few seconds)", async () => {
  $("exp-error").textContent = "";
  const n = Number($("exp-n").value);
  const trials = Number($("exp-trials").value);
  let data;
  try { data = await getJSON(`/api/experiment?n=${n}&trials=${trials}`); }
  catch (err) { $("exp-error").textContent = "Error: " + err.message; return; }

  const greedy = GREEDY;
  const fast = ["First Fit", "Best Fit", "FFD"];     // runtime chart: Knapsack DP bahut slow hai

  // (a) Kitne % inputs par optimal answer mila
  if (charts.quality) charts.quality.destroy();
  charts.quality = new Chart($("quality-chart"), {
    type: "bar",
    data: {
      labels: greedy,
      datasets: [{ label: "% of inputs solved optimally", data: greedy.map((a) => data.quality[a].pct_optimal),
                   backgroundColor: greedy.map((a) => COLORS[a]) }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: { y: { min: 0, max: 100 } },
      plugins: { legend: { display: false },
                 title: { display: true, text: `Solved optimally (N = ${data.n}, ${data.trials} random inputs)` } },
    },
  });

  // (b) N badhne par time
  if (charts.runtime) charts.runtime.destroy();
  charts.runtime = new Chart($("runtime-chart"), {
    type: "line",
    data: {
      labels: data.runtime.map((r) => r.n),
      datasets: fast.map((a) => ({ label: a, data: data.runtime.map((r) => +r.time_ms[a].toFixed(2)),
                                     borderColor: COLORS[a], backgroundColor: COLORS[a] })),
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: { x: { title: { display: true, text: "Number of containers (N)" } },
                y: { title: { display: true, text: "Time (ms)" } } },
      plugins: { title: { display: true, text: "Runtime vs N (expected O(n²))" } },
    },
  });

  // (c) Table
  let rows = `<tr><th>Algorithm</th><th>Avg nodes</th><th>Solved optimally</th><th>Avg ratio to optimal</th><th>Worst ratio</th></tr>`;
  for (const a of greedy) {
    const q = data.quality[a];
    rows += `<tr><td>${a}</td><td>${q.avg_nodes}</td><td>${q.pct_optimal}%</td><td>${q.avg_ratio}</td><td>${q.worst_ratio}</td></tr>`;
  }
  rows += `<tr><td>Optimal (B&amp;B)</td><td>${data.opt_avg_nodes}</td><td>100%</td><td>1.000</td><td>1.000</td></tr>`;
  $("exp-table").innerHTML = rows;
  $("exp-result").classList.remove("hidden");
}));

// Page khulte hi khaali table dikhao
renderTable();
