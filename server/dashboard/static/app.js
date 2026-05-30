let state = null;

const $ = (id) => document.getElementById(id);

function toast(message) {
  const node = $("toast");
  node.textContent = message;
  node.style.display = "block";
  clearTimeout(window.toastTimer);
  window.toastTimer = setTimeout(() => (node.style.display = "none"), 2800);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json();
  if (!payload.ok) throw new Error(payload.error || "request failed");
  return payload;
}

function latestMetricFor(clientId) {
  const history = state?.metrics || [];
  for (let i = history.length - 1; i >= 0; i -= 1) {
    const item = history[i].clients.find((client) => client.id === clientId);
    if (item) return item;
  }
  return null;
}

function renderServices() {
  const services = state?.services || {};
  $("service-status").innerHTML = Object.entries(services)
    .map(
      ([name, ok]) =>
        `<span class="pill"><span class="dot ${ok ? "ok" : "fail"}"></span>${name}</span>`
    )
    .join("");
}

function renderDevices() {
  const rows = state.clients
    .map((client) => {
      const metric = latestMetricFor(client.id);
      const ping = metric?.rtt_ms == null ? "-" : `${Math.round(metric.rtt_ms)} ms`;
      const pingClass = metric?.ping_ok ? "ok" : "fail";
      const volume = client.volume || {};
      return `<tr>
        <td>
          <div class="name-main">${client.name}</div>
          <div class="sub">${client.id}</div>
        </td>
        <td>${client.ip || "-"}</td>
        <td>${client.group_name || client.group_id || "-"}</td>
        <td>${client.stream_id || "-"}</td>
        <td><span class="pill"><span class="dot ${pingClass}"></span>${ping}</span></td>
        <td>
          <input type="number" min="0" max="100" value="${volume.percent ?? 100}" data-volume="${client.id}">
          <button data-mute="${client.id}">${volume.muted ? "Unmute" : "Mute"}</button>
        </td>
        <td>
          <input type="number" min="0" max="5000" step="100" value="${client.latency ?? 0}" data-latency="${client.id}">
        </td>
      </tr>`;
    })
    .join("");
  $("devices").innerHTML = rows || `<tr><td colspan="7">Geen clients gevonden.</td></tr>`;

  document.querySelectorAll("[data-volume]").forEach((input) => {
    input.addEventListener("change", async () => {
      const client = state.clients.find((item) => item.id === input.dataset.volume);
      await postAction({
        action: "set_client_volume",
        client_id: client.id,
        percent: Number(input.value),
        muted: Boolean(client.volume?.muted),
      });
    });
  });

  document.querySelectorAll("[data-mute]").forEach((button) => {
    button.addEventListener("click", async () => {
      const client = state.clients.find((item) => item.id === button.dataset.mute);
      await postAction({
        action: "set_client_volume",
        client_id: client.id,
        percent: client.volume?.percent ?? 100,
        muted: !client.volume?.muted,
      });
    });
  });

  document.querySelectorAll("[data-latency]").forEach((input) => {
    input.addEventListener("change", async () => {
      await postAction({
        action: "set_client_latency",
        client_id: input.dataset.latency,
        latency: Number(input.value),
      });
    });
  });
}

function renderGroups() {
  const groups = state.snapcast.server.groups || [];
  const streams = state.snapcast.server.streams || [];
  $("group-hint").textContent = `${groups.length} groepen, ${state.clients.length} clients`;

  $("groups-list").innerHTML = groups
    .map((group) => {
      const assigned = new Set((group.clients || []).map((client) => client.id));
      const checks = state.clients
        .map(
          (client) => `<label>
            <input type="checkbox" value="${client.id}" data-group-client="${group.id}" ${
            assigned.has(client.id) ? "checked" : ""
          }>
            <span>${client.name} <span class="sub">${client.ip || client.id}</span></span>
          </label>`
        )
        .join("");
      const streamOptions = streams
        .map(
          (stream) =>
            `<option value="${stream.id}" ${stream.id === group.stream_id ? "selected" : ""}>${stream.id}</option>`
        )
        .join("");
      return `<div class="group-block">
        <div class="group-title">
          <div>
            <div class="name-main">${group.name || group.id}</div>
            <div class="sub">${group.id}</div>
          </div>
          <div>
            <select data-stream="${group.id}">${streamOptions}</select>
            <button data-apply-group="${group.id}">Toepassen</button>
          </div>
        </div>
        <div class="client-checks">${checks}</div>
      </div>`;
    })
    .join("");

  document.querySelectorAll("[data-stream]").forEach((select) => {
    select.addEventListener("change", async () => {
      await postAction({ action: "set_group_stream", group_id: select.dataset.stream, stream_id: select.value });
    });
  });

  document.querySelectorAll("[data-apply-group]").forEach((button) => {
    button.addEventListener("click", async () => {
      const groupId = button.dataset.applyGroup;
      const clients = [...document.querySelectorAll(`[data-group-client="${groupId}"]:checked`)].map(
        (input) => input.value
      );
      await postAction({ action: "set_group_clients", group_id: groupId, clients });
    });
  });
}

function drawChart(canvas, seriesByClient, maxY) {
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = "#15191d";
  ctx.fillRect(0, 0, w, h);
  ctx.strokeStyle = "#343d45";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i += 1) {
    const y = 20 + ((h - 40) * i) / 4;
    ctx.beginPath();
    ctx.moveTo(40, y);
    ctx.lineTo(w - 10, y);
    ctx.stroke();
  }

  const colors = ["#6db5ff", "#54d17a", "#ffd36a", "#ff6f70"];
  Object.entries(seriesByClient).forEach(([name, points], index) => {
    ctx.strokeStyle = colors[index % colors.length];
    ctx.fillStyle = colors[index % colors.length];
    ctx.lineWidth = 2;
    ctx.beginPath();
    points.forEach((point, pointIndex) => {
      const x = 40 + ((w - 55) * pointIndex) / Math.max(1, points.length - 1);
      const y = h - 20 - ((h - 45) * Math.min(maxY, point.value || 0)) / maxY;
      if (pointIndex === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
    ctx.fillText(name, 46, 18 + index * 16);
  });
}

function renderQuality() {
  const history = state.metrics || [];
  const clients = state.clients;
  const pingSeries = {};
  const connectSeries = {};
  clients.forEach((client) => {
    pingSeries[client.name] = history.map((item) => {
      const found = item.clients.find((entry) => entry.id === client.id);
      return { value: found?.rtt_ms ?? 0 };
    });
    connectSeries[client.name] = history.map((item) => {
      const found = item.clients.find((entry) => entry.id === client.id);
      return { value: found?.connected && found?.ping_ok ? 1 : 0 };
    });
  });
  drawChart($("ping-chart"), pingSeries, 500);
  drawChart($("connect-chart"), connectSeries, 1);
}

async function renderLogs() {
  try {
    const log = await api(`/api/logs?name=${encodeURIComponent($("log-select").value)}`);
    $("log-output").textContent = log.text || "Nog geen logregels.";
  } catch (error) {
    $("log-output").textContent = error.message;
  }
}

async function postAction(payload) {
  try {
    await api("/api/snapcast", { method: "POST", body: JSON.stringify(payload) });
    toast("Opgeslagen");
    await refresh();
  } catch (error) {
    toast(error.message);
  }
}

function render() {
  renderServices();
  renderDevices();
  renderGroups();
  renderQuality();
}

async function refresh() {
  try {
    state = await api("/api/status");
    render();
  } catch (error) {
    toast(error.message);
  }
}

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab, .panel").forEach((node) => node.classList.remove("is-active"));
    tab.classList.add("is-active");
    $(tab.dataset.tab).classList.add("is-active");
    if (tab.dataset.tab === "logs") renderLogs();
  });
});

$("refresh").addEventListener("click", refresh);
$("log-select").addEventListener("change", renderLogs);

refresh();
setInterval(refresh, 5000);
setInterval(() => {
  if ($("logs").classList.contains("is-active")) renderLogs();
}, 5000);
