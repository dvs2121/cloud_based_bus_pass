const API_BASE = "/api";
let state = {
    token: localStorage.getItem("nexroute_token") || null,
    user: JSON.parse(localStorage.getItem("nexroute_user") || "null"),
};
let CITIES = [];

function authHeaders() {
    const h = { "Content-Type": "application/json" };
    if (state.token) h["Authorization"] = `Bearer ${state.token}`;
    return h;
}

document.addEventListener("DOMContentLoaded", async () => {
    document.getElementById("portal-login-form").addEventListener("submit", handlePortalLogin);
    await boot();
});

async function boot() {
    if (!state.token || !state.user || !["admin", "provider"].includes(state.user.role)) {
        showGate();
        return;
    }
    // validate session
    const res = await fetch(`${API_BASE}/auth/me`, { headers: authHeaders() });
    if (!res.ok) { showGate(); return; }
    const me = await res.json();
    state.user = me;

    await loadCitiesInto(["nv-city", "nb-source", "nb-destination"]);

    document.getElementById("gate").classList.add("hidden");
    if (me.role === "admin") {
        document.getElementById("admin-dashboard").classList.remove("hidden");
        initAdminDashboard();
    } else {
        document.getElementById("provider-dashboard").classList.remove("hidden");
        initProviderDashboard();
    }
}

function showGate() {
    document.getElementById("gate").classList.remove("hidden");
    document.getElementById("admin-dashboard").classList.add("hidden");
    document.getElementById("provider-dashboard").classList.add("hidden");
}

async function loadCitiesInto(selectIds) {
    if (CITIES.length === 0) {
        const res = await fetch(`${API_BASE}/cities`);
        const data = await res.json();
        CITIES = data.cities;
    }
    selectIds.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = CITIES.map(c => `<option value="${c}">${c}</option>`).join("");
    });
}

async function handlePortalLogin(e) {
    e.preventDefault();
    const errEl = document.getElementById("portal-login-error");
    errEl.classList.add("hidden");
    try {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                email: document.getElementById("portal-email").value,
                password: document.getElementById("portal-password").value,
            }),
        });
        const data = await res.json();
        if (!res.ok) { errEl.textContent = data.detail; errEl.classList.remove("hidden"); return; }
        if (!["admin", "provider"].includes(data.user.role)) {
            errEl.textContent = "This account isn't a provider or admin account.";
            errEl.classList.remove("hidden");
            return;
        }
        state.token = data.token;
        state.user = data.user;
        localStorage.setItem("nexroute_token", data.token);
        localStorage.setItem("nexroute_user", JSON.stringify(data.user));
        boot();
    } catch { errEl.textContent = "Network error. Please try again."; errEl.classList.remove("hidden"); }
}

// ============================================================ ADMIN
async function initAdminDashboard() {
    await refreshAdminStats();
    await refreshPendingVehicles();
    await refreshAllVehicles();
    document.getElementById("new-bus-form").addEventListener("submit", handleNewBus);
}

async function refreshAdminStats() {
    const res = await fetch(`${API_BASE}/admin/stats`, { headers: authHeaders() });
    const s = await res.json();
    document.getElementById("admin-stats").innerHTML = `
        ${statCard(s.total_users, "Travellers")}
        ${statCard(s.total_providers, "Providers")}
        ${statCard(s.total_buses, "Bus Routes")}
        ${statCard(s.total_bus_tickets, "Tickets Sold")}
        ${statCard(s.total_hire_bookings, "Hire Bookings")}
        ${statCard(s.pending_vehicles, "Pending Vehicles")}
    `;
}
function statCard(num, label) { return `<div class="stat-card"><div class="num">${num}</div><div class="lbl">${label}</div></div>`; }

async function refreshPendingVehicles() {
    const res = await fetch(`${API_BASE}/admin/vehicles?status=pending`, { headers: authHeaders() });
    const vehicles = await res.json();
    const body = document.querySelector("#pending-table tbody");
    body.innerHTML = vehicles.length ? "" : `<tr><td colspan="5" style="color:var(--muted)">Nothing pending — all caught up.</td></tr>`;
    vehicles.forEach(v => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${v.emoji} ${v.name}</td>
            <td>${v.type === "mini_bus" ? "Mini Bus" : "Self-Driving Car"}</td>
            <td>${v.base_city}</td>
            <td>₹${Number(v.price_per_km).toFixed(0)}/km</td>
            <td><button class="btn small" style="margin-right:6px;" data-action="approve" data-id="${v.id}">Approve</button><button class="btn small danger" data-action="reject" data-id="${v.id}">Reject</button></td>
        `;
        body.appendChild(tr);
    });
    body.querySelectorAll("button[data-action]").forEach(btn => {
        btn.addEventListener("click", async () => {
            await fetch(`${API_BASE}/admin/vehicles/${btn.dataset.id}/${btn.dataset.action}`, { method: "POST", headers: authHeaders() });
            await refreshAdminStats();
            await refreshPendingVehicles();
            await refreshAllVehicles();
        });
    });
}

async function refreshAllVehicles() {
    const res = await fetch(`${API_BASE}/admin/vehicles`, { headers: authHeaders() });
    const vehicles = await res.json();
    const body = document.querySelector("#all-vehicles-table tbody");
    body.innerHTML = "";
    vehicles.forEach(v => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${v.emoji} ${v.name}</td>
            <td>${v.type === "mini_bus" ? "Mini Bus" : "Self-Driving Car"}</td>
            <td>${v.base_city}</td>
            <td><span class="status-pill ${v.status}">${v.status}</span></td>
        `;
        body.appendChild(tr);
    });
}

async function handleNewBus(e) {
    e.preventDefault();
    const payload = {
        operator_name: document.getElementById("nb-operator").value || "RailYatra Express",
        bus_type: document.getElementById("nb-bustype").value,
        source: document.getElementById("nb-source").value,
        destination: document.getElementById("nb-destination").value,
        departure_date: document.getElementById("nb-date").value,
        departure_time: document.getElementById("nb-time").value,
        base_price: parseFloat(document.getElementById("nb-price").value),
        total_seats: parseInt(document.getElementById("nb-seats").value),
    };
    if (payload.source === payload.destination) { alert("Source and destination can't be the same."); return; }
    const res = await fetch(`${API_BASE}/admin/buses`, { method: "POST", headers: authHeaders(), body: JSON.stringify(payload) });
    const data = await res.json();
    const successEl = document.getElementById("nb-success");
    if (!res.ok) { alert(data.detail); return; }
    successEl.textContent = `Route published: ${data.source} → ${data.destination} on ${data.departure_date}`;
    successEl.classList.remove("hidden");
    await refreshAdminStats();
}

// ============================================================ PROVIDER
async function initProviderDashboard() {
    document.querySelectorAll("#nv-type-toggle button").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll("#nv-type-toggle button").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            document.getElementById("nv-driver-group").style.display = btn.dataset.type === "self_driving_car" ? "none" : "flex";
            if (btn.dataset.type === "self_driving_car") document.getElementById("nv-driver").value = 0;
        });
    });
    document.getElementById("new-vehicle-form").addEventListener("submit", handleNewVehicle);
    await refreshMyVehicles();
    await refreshMyBookings();
}

async function handleNewVehicle(e) {
    e.preventDefault();
    const type = document.querySelector("#nv-type-toggle button.active").dataset.type;
    const payload = {
        type,
        name: document.getElementById("nv-name").value,
        base_city: document.getElementById("nv-city").value,
        seats: parseInt(document.getElementById("nv-seats").value),
        price_per_km: parseFloat(document.getElementById("nv-perkm").value),
        price_per_day_local: parseFloat(document.getElementById("nv-perday").value),
        driver_allowance_per_day: parseFloat(document.getElementById("nv-driver").value || 0),
        description: document.getElementById("nv-desc").value,
        emoji: type === "mini_bus" ? "🚐" : "🚗",
    };
    const res = await fetch(`${API_BASE}/provider/vehicles`, { method: "POST", headers: authHeaders(), body: JSON.stringify(payload) });
    const data = await res.json();
    if (!res.ok) { alert(data.detail); return; }
    const successEl = document.getElementById("nv-success");
    successEl.textContent = `"${data.name}" submitted — pending admin approval before it appears to travellers.`;
    successEl.classList.remove("hidden");
    document.getElementById("new-vehicle-form").reset();
    await refreshMyVehicles();
}

async function refreshMyVehicles() {
    const res = await fetch(`${API_BASE}/provider/vehicles/mine`, { headers: authHeaders() });
    const vehicles = await res.json();
    const body = document.querySelector("#my-vehicles-table tbody");
    body.innerHTML = vehicles.length ? "" : `<tr><td colspan="4" style="color:var(--muted)">You haven't listed any vehicles yet.</td></tr>`;
    vehicles.forEach(v => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${v.emoji} ${v.name}</td>
            <td>${v.type === "mini_bus" ? "Mini Bus" : "Self-Driving Car"}</td>
            <td>${v.base_city}</td>
            <td><span class="status-pill ${v.status}">${v.status}</span></td>
        `;
        body.appendChild(tr);
    });
}

async function refreshMyBookings() {
    const res = await fetch(`${API_BASE}/provider/bookings`, { headers: authHeaders() });
    const bookings = await res.json();
    const body = document.querySelector("#my-bookings-table tbody");
    body.innerHTML = bookings.length ? "" : `<tr><td colspan="4" style="color:var(--muted)">No bookings yet.</td></tr>`;
    bookings.forEach(b => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${b.pickup_city}${b.drop_city ? " → " + b.drop_city : " (local)"}</td>
            <td>${b.trip_type}</td>
            <td>${b.start_date} → ${b.end_date}</td>
            <td>₹${Number(b.total_price).toFixed(0)}</td>
        `;
        body.appendChild(tr);
    });
}