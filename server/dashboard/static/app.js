let state = null;

const $ = (id) => document.getElementById(id);

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function toast(message) {
  const node = $("toast");
  node.textContent = message;
  node.style.display = "block";
  clearTimeout(window.toastTimer);
  window.toastTimer = setTimeout(() => (node.style.display = "none"), 3800);
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

function snapGroups() {
  const visibleClients = new Set((state?.clients || []).map((client) => client.id));
  return (state?.snapcast?.server?.groups || []).filter(
    (group) => (group.clients || []).some((client) => visibleClients.has(client.id)) || group.name
  );
}

function allGroups() {
  return [...snapGroups(), ...(state?.dashboard_groups || []).map((group) => ({ ...group, virtual: true, clients: [] }))];
}

function streams() {
  return state?.snapcast?.server?.streams || [];
}

function renderServices() {
  const services = state?.services || {};
  $("service-status").innerHTML = Object.entries(services)
    .map(([name, ok]) => `<span class="pill"><span class="dot ${ok ? "ok" : "fail"}"></span>${esc(name)}</span>`)
    .join("");
}

function deviceCard(client, compact = false, groupId = null) {
  const metric = latestMetricFor(client.id);
  const ping = metric?.rtt_ms == null ? "-" : `${Math.round(metric.rtt_ms)} ms`;
  const pingClass = metric?.ping_ok ? "ok" : "fail";
  const volume = client.volume || {};
  const muted = Boolean(volume.muted);
  return `<article class="device-card ${compact ? "is-compact" : ""}" data-client-id="${esc(client.id)}">
    <div class="device-card-head">
      <button class="drag-handle" draggable="true" data-drag-client="${esc(client.id)}" aria-label="${esc(client.name)} verslepen" title="Verslepen">
        <span></span><span></span><span></span><span></span><span></span><span></span>
      </button>
      <input class="name-input" value="${esc(client.name)}" data-name="${esc(client.id)}" aria-label="Device naam">
      <span class="pill"><span class="dot ${client.connected ? "ok" : "fail"}"></span>${client.connected ? "online" : "offline"}</span>
    </div>
    <div class="device-meta">
      <span>${esc(client.ip || "-")}</span>
      <span>${esc(client.group_name || client.group_id || "-")}</span>
      <span>${esc(client.stream_id || "-")}</span>
    </div>
    <div class="device-controls">
      <label class="slider-row">
        <span>Volume</span>
        <input type="range" min="0" max="100" value="${volume.percent ?? 100}" data-volume="${esc(client.id)}">
        <output>${volume.percent ?? 100}%</output>
      </label>
      <button data-mute="${esc(client.id)}">${muted ? "Unmute" : "Mute"}</button>
      <label class="latency-row">
        <span>Latency</span>
        <input type="number" min="0" max="8000" step="100" value="${client.latency ?? 0}" data-latency="${esc(client.id)}">
      </label>
      ${groupId ? `<button data-remove-client="${esc(client.id)}" data-remove-group="${esc(groupId)}">Uit groep halen</button>` : ""}
    </div>
    <div class="device-footer">
      <span class="pill"><span class="dot ${pingClass}"></span>${ping}</span>
      <span class="sub">${esc(client.id)}</span>
    </div>
  </article>`;
}

function bindDeviceActions(root = document) {
  root.querySelectorAll("[data-drag-client]").forEach((handle) => {
    handle.addEventListener("dragstart", (event) => {
      event.dataTransfer.setData("text/plain", handle.dataset.dragClient);
      event.dataTransfer.effectAllowed = "move";
      const card = handle.closest("[data-client-id]");
      card.classList.add("is-dragging");
    });
    handle.addEventListener("dragend", () => {
      const card = handle.closest("[data-client-id]");
      card.classList.remove("is-dragging");
    });
  });

  root.querySelectorAll("[data-name]").forEach((input) => {
    input.addEventListener("change", async () => {
      await postAction({ action: "set_client_name", client_id: input.dataset.name, name: input.value });
    });
  });

  root.querySelectorAll("[data-volume]").forEach((input) => {
    input.addEventListener("input", () => {
      input.parentElement.querySelector("output").textContent = `${input.value}%`;
    });
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

  root.querySelectorAll("[data-mute]").forEach((button) => {
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

  root.querySelectorAll("[data-latency]").forEach((input) => {
    input.addEventListener("change", async () => {
      await postAction({ action: "set_client_latency", client_id: input.dataset.latency, latency: Number(input.value) });
    });
  });
}

function renderDevices() {
  $("devices-grid").innerHTML = state.clients.map((client) => deviceCard(client)).join("") || `<p>Geen clients gevonden.</p>`;
  bindDeviceActions($("devices-grid"));
}

function groupBlock(group) {
  const clients = group.virtual
    ? (group.clients || []).map((clientId) => state.clients.find((client) => client.id === clientId)).filter(Boolean)
    : state.clients.filter((client) => client.group_id === group.id);
  const streamOptions = streams()
    .map((stream) => `<option value="${esc(stream.id)}" ${stream.id === group.stream_id ? "selected" : ""}>${esc(stream.id)}</option>`)
    .join("");
  const empty = group.virtual ? "Sleep hier devices naartoe. Een device mag in meerdere dashboard-groepen zitten." : "Geen devices in deze groep.";
  return `<section class="group-block ${group.virtual ? "is-virtual" : ""}" data-drop-group="${esc(group.id)}">
    <div class="group-title">
      <div>
        <input class="group-name" value="${esc(group.name || group.id)}" data-group-name="${esc(group.id)}">
        <div class="sub">${group.virtual ? "Dashboard-groep/preset" : "Actieve Snapcast-groep"}</div>
      </div>
      <div class="group-actions">
        ${
          group.virtual
            ? `<button data-activate-virtual="${esc(group.id)}">Activeer</button><button data-delete-virtual="${esc(group.id)}">Verwijder</button>`
            : `<select data-stream="${esc(group.id)}">${streamOptions}</select>`
        }
      </div>
    </div>
    <div class="dropzone">
      ${clients.map((client) => deviceCard(client, true, group.virtual ? group.id : null)).join("") || `<div class="empty-drop">${empty}</div>`}
    </div>
  </section>`;
}

function renderGroups() {
  const groups = allGroups();
  $("group-hint").textContent = `${groups.length} groepen, ${state.clients.length} clients`;
  $("groups-list").innerHTML = groups.map(groupBlock).join("") || `<p>Geen groepen gevonden.</p>`;
  bindDeviceActions($("groups-list"));

  $("new-group-form").onsubmit = async (event) => {
    event.preventDefault();
    const input = $("new-group-name");
    await postAction({ action: "create_virtual_group", name: input.value || "Nieuwe groep" });
    input.value = "";
  };

  document.querySelectorAll("[data-drop-group]").forEach((zone) => {
    zone.addEventListener("dragover", (event) => {
      event.preventDefault();
      zone.classList.add("is-over");
    });
    zone.addEventListener("dragleave", () => zone.classList.remove("is-over"));
    zone.addEventListener("drop", async (event) => {
      event.preventDefault();
      zone.classList.remove("is-over");
      const clientId = event.dataTransfer.getData("text/plain");
      if (clientId) {
        const groupId = zone.dataset.dropGroup;
        await postAction({
          action: groupId.startsWith("dash-") ? "add_group_client" : "move_client_to_group",
          client_id: clientId,
          group_id: groupId,
        });
      }
    });
  });

  document.querySelectorAll("[data-stream]").forEach((select) => {
    select.addEventListener("change", async () => {
      await postAction({ action: "set_group_stream", group_id: select.dataset.stream, stream_id: select.value });
    });
  });

  document.querySelectorAll("[data-group-name]").forEach((input) => {
    input.addEventListener("change", async () => {
      await postAction({ action: "set_group_name", group_id: input.dataset.groupName, name: input.value });
    });
  });

  document.querySelectorAll("[data-delete-virtual]").forEach((button) => {
    button.addEventListener("click", async () => {
      await postAction({ action: "delete_virtual_group", group_id: button.dataset.deleteVirtual });
    });
  });

  document.querySelectorAll("[data-activate-virtual]").forEach((button) => {
    button.addEventListener("click", async () => {
      await postAction({ action: "activate_virtual_group", group_id: button.dataset.activateVirtual });
    });
  });

  document.querySelectorAll("[data-remove-client]").forEach((button) => {
    button.addEventListener("click", async () => {
      await postAction({
        action: "remove_group_client",
        client_id: button.dataset.removeClient,
        group_id: button.dataset.removeGroup,
      });
    });
  });
}

function renderWifi() {
  $("wifi-device").innerHTML = state.clients
    .map((client) => `<option value="${esc(client.id)}">${esc(client.name)} - ${esc(client.ip || "geen IP")}</option>`)
    .join("");
}

function drawChart(canvas, seriesByClient, maxY) {
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = "#151715";
  ctx.fillRect(0, 0, w, h);
  ctx.strokeStyle = "#343b34";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i += 1) {
    const y = 20 + ((h - 40) * i) / 4;
    ctx.beginPath();
    ctx.moveTo(40, y);
    ctx.lineTo(w - 10, y);
    ctx.stroke();
  }

  const colors = ["#82c66f", "#f0c45a", "#70b7b4", "#f47d65"];
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
  const pingSeries = {};
  const connectSeries = {};
  state.clients.forEach((client) => {
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
  renderWifi();
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
$("wifi-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const client = state.clients.find((item) => item.id === $("wifi-device").value);
  await postAction({
    action: "set_device_wifi",
    client_id: client?.id,
    ip: client?.ip,
    ssid: $("wifi-ssid").value,
    password: $("wifi-password").value,
  });
});

refresh();
setInterval(refresh, 5000);
setInterval(() => {
  if ($("logs").classList.contains("is-active")) renderLogs();
}, 5000);
