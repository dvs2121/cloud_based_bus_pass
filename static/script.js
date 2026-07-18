const API_BASE = "/api";

let CITIES = [];
let ROUTES = [];
let state = {
    token: localStorage.getItem("nexroute_token") || null,
    user: JSON.parse(localStorage.getItem("nexroute_user") || "null"),
};
let hire = { type: "mini_bus", trip: "local", selectedVehicle: null, vehicles: [] };

// ---------------------------------------------------------------- helpers
function authHeaders(extra = {}) {
    const h = { "Content-Type": "application/json", ...extra };
    if (state.token) h["Authorization"] = `Bearer ${state.token}`;
    return h;
}

function setSession(token, user) {
    state.token = token;
    state.user = user;
    localStorage.setItem("nexroute_token", token);
    localStorage.setItem("nexroute_user", JSON.stringify(user));
    renderNav();
}

function clearSession() {
    state.token = null;
    state.user = null;
    localStorage.removeItem("nexroute_token");
    localStorage.removeItem("nexroute_user");
    renderNav();
}

function renderNav() {
    const el = document.getElementById("nav-links");
    if (state.user) {
        el.innerHTML = `
            <a href="/admin" class="nav-btn ghost">Provider / Admin Portal →</a>
            <div class="user-chip">👤 ${state.user.name.split(" ")[0]} <span class="role-tag">${state.user.role}</span></div>
            <button class="nav-btn" id="btn-logout">Log Out</button>
        `;
        document.getElementById("btn-logout").onclick = async () => {
            await fetch(`${API_BASE}/auth/logout`, { method: "POST", headers: authHeaders() });
            clearSession();
            loadMyBookings();
        };
    } else {
        el.innerHTML = `
            <a href="/admin" class="nav-btn ghost">Provider / Admin Portal →</a>
            <button class="nav-btn" id="btn-login">Log In</button>
            <button class="nav-btn primary" id="btn-register">Register</button>
        `;
        document.getElementById("btn-login").onclick = () => openAuthModal("login");
        document.getElementById("btn-register").onclick = () => openAuthModal("register");
    }
}

// ---------------------------------------------------------------- init
document.addEventListener("DOMContentLoaded", async () => {
    const today = new Date().toISOString().split("T")[0];
    document.getElementById("travel-date").setAttribute("min", today);
    document.getElementById("hire-start").setAttribute("min", today);
    document.getElementById("hire-end").setAttribute("min", today);

    renderNav();
    await loadCities();
    setupTabs();
    setupAuthModal();
    setupDevModal();
    setupBusFlow();
    setupHireFlow();
    loadMyBookings();
});

async function loadCities() {
    try {
        const res = await fetch(`${API_BASE}/cities`);
        const data = await res.json();
        CITIES = data.cities;
        ROUTES = data.routes;

        const opts = c => `<option value="${c}">${c}</option>`;
        for (const id of ["source", "destination", "hire-pickup", "hire-drop"]) {
            document.getElementById(id).innerHTML += CITIES.map(opts).join("");
        }

        const track = document.getElementById("ticker-track");
        const items = ROUTES.slice(0, 14).map(r => `<span><b>${r.source}</b> → ${r.destination}</span>`);
        track.innerHTML = items.concat(items).join("");
    } catch (e) {
        console.error("Failed to load cities", e);
    }
}

// ---------------------------------------------------------------- tabs
function setupTabs() {
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
            btn.classList.add("active");
            document.getElementById(btn.dataset.tab).classList.add("active");
        });
    });
}

// ---------------------------------------------------------------- auth modal
function openAuthModal(tab) {
    document.getElementById("auth-modal").classList.remove("hidden");
    switchAuthTab(tab);
}

function switchAuthTab(tab) {
    document.querySelectorAll("[data-authtab]").forEach(b => b.classList.toggle("active", b.dataset.authtab === tab));
    document.getElementById("login-form").classList.toggle("hidden", tab !== "login");
    document.getElementById("register-form").classList.toggle("hidden", tab !== "register");
}

function setupAuthModal() {
    document.querySelectorAll("[data-close]").forEach(btn => {
        btn.addEventListener("click", () => document.getElementById(btn.dataset.close).classList.add("hidden"));
    });
    document.querySelectorAll(".modal-overlay").forEach(overlay => {
        overlay.addEventListener("click", e => { if (e.target === overlay) overlay.classList.add("hidden"); });
    });
    document.querySelectorAll("[data-authtab]").forEach(b => b.addEventListener("click", () => switchAuthTab(b.dataset.authtab)));

    document.getElementById("mine-login-btn")?.addEventListener("click", () => openAuthModal("login"));

    document.getElementById("login-form").addEventListener("submit", async e => {
        e.preventDefault();
        const errEl = document.getElementById("login-error");
        errEl.classList.add("hidden");
        try {
            const res = await fetch(`${API_BASE}/auth/login`, {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    email: document.getElementById("login-email").value,
                    password: document.getElementById("login-password").value,
                }),
            });
            const data = await res.json();
            if (!res.ok) { errEl.textContent = data.detail; errEl.classList.remove("hidden"); return; }
            setSession(data.token, data.user);
            document.getElementById("auth-modal").classList.add("hidden");
            loadMyBookings();
        } catch { errEl.textContent = "Network error. Please try again."; errEl.classList.remove("hidden"); }
    });

    document.getElementById("register-form").addEventListener("submit", async e => {
        e.preventDefault();
        const errEl = document.getElementById("register-error");
        errEl.classList.add("hidden");
        try {
            const res = await fetch(`${API_BASE}/auth/register`, {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    name: document.getElementById("reg-name").value,
                    email: document.getElementById("reg-email").value,
                    phone: document.getElementById("reg-phone").value,
                    password: document.getElementById("reg-password").value,
                    role: document.getElementById("reg-role").value,
                }),
            });
            const data = await res.json();
            if (!res.ok) { errEl.textContent = data.detail; errEl.classList.remove("hidden"); return; }
            setSession(data.token, data.user);
            document.getElementById("auth-modal").classList.add("hidden");
            loadMyBookings();
            if (data.user.role === "provider") {
                alert("Provider account created! Head to the Provider / Admin Portal to list your vehicles.");
            }
        } catch { errEl.textContent = "Network error. Please try again."; errEl.classList.remove("hidden"); }
    });
}

// ---------------------------------------------------------------- developer modal
function setupDevModal() {
    document.getElementById("dev-fab").addEventListener("click", () => {
        document.getElementById("dev-modal").classList.remove("hidden");
    });
}

// ---------------------------------------------------------------- bus search & booking
function setupBusFlow() {
    document.getElementById("search-form").addEventListener("submit", handleSearch);
    document.getElementById("booking-form").addEventListener("submit", handleBooking);
}

async function handleSearch(event) {
    event.preventDefault();
    const source = document.getElementById("source").value;
    const destination = document.getElementById("destination").value;
    const date = document.getElementById("travel-date").value;
    const timePeriod = document.getElementById("travel-time").value;

    if (source === destination) { alert("Source and destination can't be the same city."); return; }

    const params = new URLSearchParams({ source, destination, date });
    if (timePeriod) params.append("time_period", timePeriod);

    document.getElementById("search-section").classList.add("hidden");
    document.getElementById("results-section").classList.remove("hidden");
    document.getElementById("bus-list").innerHTML = '<p class="loading">Searching the network…</p>';

    try {
        const response = await fetch(`${API_BASE}/search?${params}`);
        const buses = await response.json();
        displayResults(buses);
    } catch (error) {
        document.getElementById("bus-list").innerHTML = '<p class="no-results">Error searching buses. Please try again.</p>';
    }
}

function displayResults(buses) {
    const busList = document.getElementById("bus-list");
    busList.innerHTML = "";
    if (!buses || buses.length === 0) {
        busList.innerHTML = '<p class="no-results">No buses found on this corridor for that date. Try nearby dates or check the routes on the Provider / Admin Portal.</p>';
        return;
    }
    buses.forEach(bus => {
        const card = document.createElement("div");
        card.className = "bus-card";
        const timeStr = bus.departure_time.substring(0, 5);
        const lowSeats = bus.available_seats <= 6;
        card.innerHTML = `
            <div>
                <div class="route-info"><span>${bus.source}</span><span class="arrow">→</span><span>${bus.destination}</span></div>
                <div class="operator">${bus.operator_name} · ${bus.bus_type}</div>
            </div>
            <div>${bus.departure_date}</div>
            <div>⏰ ${timeStr}</div>
            <div class="seats ${lowSeats ? "low" : ""}">${bus.available_seats} left</div>
            <div class="price">₹${Number(bus.base_price).toFixed(0)}</div>
        `;
        card.onclick = () => selectBus(bus);
        busList.appendChild(card);
    });
}

function selectBus(bus) {
    document.getElementById("selected-bus-id").value = bus.id;
    const infoDiv = document.getElementById("selected-bus-info");
    infoDiv.innerHTML = `
        <p><strong>Route:</strong> ${bus.source} → ${bus.destination}</p>
        <p><strong>Operator:</strong> ${bus.operator_name} (${bus.bus_type})</p>
        <p><strong>Departs:</strong> ${bus.departure_date} at ${bus.departure_time.substring(0, 5)}</p>
        <p><strong>Fare:</strong> ₹${Number(bus.base_price).toFixed(0)}</p>
    `;
    if (state.user) {
        document.getElementById("name").value = state.user.name;
        document.getElementById("email").value = state.user.email;
    }
    document.getElementById("results-section").classList.add("hidden");
    document.getElementById("booking-section").classList.remove("hidden");
}

async function handleBooking(event) {
    event.preventDefault();
    const busId = document.getElementById("selected-bus-id").value;
    if (!busId) { alert("No bus selected!"); return; }

    const payload = {
        passenger_name: document.getElementById("name").value,
        passenger_email: document.getElementById("email").value,
        passenger_phone: document.getElementById("phone").value,
        bus_id: parseInt(busId),
    };

    try {
        const response = await fetch(`${API_BASE}/book`, { method: "POST", headers: authHeaders(), body: JSON.stringify(payload) });
        if (!response.ok) { const err = await response.json(); alert(`Booking Failed: ${err.detail}`); return; }
        const ticket = await response.json();
        displayTicket(ticket);
        loadMyBookings();
    } catch { alert("Network error. Please try again."); }
}

function displayTicket(ticket) {
    document.getElementById("booking-section").classList.add("hidden");
    document.getElementById("ticket-section").classList.remove("hidden");
    document.getElementById("res-route").innerHTML = ticket.route.replace("→", '<span class="arrow">→</span>');
    document.getElementById("res-id").textContent = ticket.ticket_id;
    document.getElementById("res-price").textContent = `₹${ticket.price.toFixed(2)}`;
    document.getElementById("res-status").textContent = ticket.status;
}

function resetSearch() {
    document.getElementById("results-section").classList.add("hidden");
    document.getElementById("search-section").classList.remove("hidden");
}

// ---------------------------------------------------------------- vehicle hire
function setupHireFlow() {
    document.querySelectorAll("#vehicle-type-toggle button").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll("#vehicle-type-toggle button").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            hire.type = btn.dataset.type;
            hire.selectedVehicle = null;
            loadVehicles();
        });
    });
    document.querySelectorAll("#trip-type-toggle button").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll("#trip-type-toggle button").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            hire.trip = btn.dataset.trip;
            document.getElementById("hire-drop-group").style.display = hire.trip === "outstation" ? "flex" : "none";
            refreshQuote();
        });
    });
    ["hire-pickup", "hire-drop", "hire-start", "hire-end"].forEach(id => {
        document.getElementById(id).addEventListener("change", refreshQuote);
    });
    document.getElementById("hire-confirm-btn").addEventListener("click", confirmHireBooking);
    loadVehicles();
}

async function loadVehicles() {
    const grid = document.getElementById("vehicle-grid");
    grid.innerHTML = '<p class="loading">Loading fleet…</p>';
    try {
        const res = await fetch(`${API_BASE}/vehicles?type=${hire.type}`);
        hire.vehicles = await res.json();
        if (hire.vehicles.length === 0) {
            grid.innerHTML = '<p class="no-results">No vehicles of this type are listed yet.</p>';
            return;
        }
        grid.innerHTML = "";
        hire.vehicles.forEach(v => {
            const card = document.createElement("div");
            card.className = "vehicle-card";
            card.dataset.id = v.id;
            card.innerHTML = `
                <div class="emoji">${v.emoji}</div>
                <h3>${v.name}</h3>
                <div class="meta">📍 ${v.base_city} · ${v.seats} seats</div>
                <div class="rate">₹${Number(v.price_per_km).toFixed(0)}/km · ₹${Number(v.price_per_day_local).toFixed(0)}/day local</div>
            `;
            card.onclick = () => {
                document.querySelectorAll(".vehicle-card").forEach(c => c.classList.remove("selected"));
                card.classList.add("selected");
                hire.selectedVehicle = v;
                refreshQuote();
            };
            grid.appendChild(card);
        });
    } catch {
        grid.innerHTML = '<p class="no-results">Error loading fleet.</p>';
    }
}

function computeDays() {
    const start = document.getElementById("hire-start").value;
    const end = document.getElementById("hire-end").value;
    if (!start || !end) return 1;
    const diff = (new Date(end) - new Date(start)) / (1000 * 60 * 60 * 24);
    return Math.max(1, Math.round(diff) + 1);
}

async function refreshQuote() {
    const box = document.getElementById("quote-box");
    const confirmBtn = document.getElementById("hire-confirm-btn");
    if (!hire.selectedVehicle) { box.classList.add("hidden"); confirmBtn.classList.add("hidden"); return; }

    const pickup = document.getElementById("hire-pickup").value;
    const drop = document.getElementById("hire-drop").value;
    if (!pickup || (hire.trip === "outstation" && !drop)) { box.classList.add("hidden"); confirmBtn.classList.add("hidden"); return; }

    const days = computeDays();
    try {
        const res = await fetch(`${API_BASE}/vehicles/quote`, {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ vehicle_id: hire.selectedVehicle.id, trip_type: hire.trip, pickup_city: pickup, drop_city: drop || null, days }),
        });
        if (!res.ok) { box.classList.add("hidden"); confirmBtn.classList.add("hidden"); return; }
        const q = await res.json();
        box.classList.remove("hidden");
        confirmBtn.classList.remove("hidden");
        box.innerHTML = `
            <div class="row"><span>Vehicle</span><span>${q.vehicle.emoji} ${q.vehicle.name}</span></div>
            ${hire.trip === "outstation" ? `<div class="row"><span>Distance (round trip)</span><span>${q.billed_km} km</span></div>` : `<div class="row"><span>Package</span><span>80 km / 8 hr per day</span></div>`}
            <div class="row"><span>Base fare (${days} day${days > 1 ? "s" : ""})</span><span>₹${q.base_fare.toFixed(0)}</span></div>
            <div class="row"><span>Driver charges</span><span>₹${q.driver_charges.toFixed(0)}</span></div>
            <div class="row"><span>GST (5%)</span><span>₹${q.gst.toFixed(0)}</span></div>
            <div class="row total"><span>Total</span><span>₹${q.total_price.toFixed(0)}</span></div>
        `;
    } catch { box.classList.add("hidden"); confirmBtn.classList.add("hidden"); }
}

async function confirmHireBooking() {
    if (!state.user) { openAuthModal("login"); return; }
    const pickup = document.getElementById("hire-pickup").value;
    const drop = document.getElementById("hire-drop").value;
    const start = document.getElementById("hire-start").value || new Date().toISOString().split("T")[0];
    const end = document.getElementById("hire-end").value || start;

    try {
        const res = await fetch(`${API_BASE}/vehicle-bookings`, {
            method: "POST", headers: authHeaders(),
            body: JSON.stringify({
                vehicle_id: hire.selectedVehicle.id, trip_type: hire.trip,
                pickup_city: pickup, drop_city: drop || null, start_date: start, end_date: end,
            }),
        });
        const data = await res.json();
        if (!res.ok) { alert(`Booking failed: ${data.detail}`); return; }
        document.getElementById("hire-ticket-section").classList.remove("hidden");
        document.getElementById("hire-ticket-body").innerHTML = `
            <p><strong>Booking ID:</strong> ${data.booking_id}</p>
            <p><strong>Vehicle:</strong> ${data.vehicle}</p>
            <p><strong>Route:</strong> ${data.route}</p>
            <p><strong>Total Paid:</strong> ₹${data.total_price.toFixed(0)}</p>
            <p><strong>Status:</strong> <span class="badge">${data.status}</span></p>
        `;
        loadMyBookings();
    } catch { alert("Network error. Please try again."); }
}

// ---------------------------------------------------------------- my bookings
async function loadMyBookings() {
    const locked = document.getElementById("mine-locked");
    const content = document.getElementById("mine-content");
    const hireContent = document.getElementById("mine-hire-content");
    if (!state.token) { locked.classList.remove("hidden"); content.classList.add("hidden"); hireContent.classList.add("hidden"); return; }

    locked.classList.add("hidden");
    content.classList.remove("hidden");
    hireContent.classList.remove("hidden");

    try {
        const hireRes = await fetch(`${API_BASE}/vehicle-bookings/mine`, { headers: authHeaders() });
        const hireBookings = hireRes.ok ? await hireRes.json() : [];
        document.getElementById("mine-hire").innerHTML = hireBookings.length
            ? hireBookings.map(b => `<div class="selected-bus-info"><p>${b.pickup_city}${b.drop_city ? " → " + b.drop_city : " (local)"} · ₹${Number(b.total_price).toFixed(0)} · <span class="badge">${b.status}</span></p></div>`).join("")
            : '<p style="color:var(--muted)">No hire bookings yet.</p>';

        document.getElementById("mine-tickets").innerHTML = '<p style="color:var(--muted)">Bus ticket history is shown right after booking — save your Ticket ID for future reference.</p>';
    } catch { /* silent */ }
}