const API_BASE = "/api"; 

document.addEventListener("DOMContentLoaded", () => {
    // Set minimum date to today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById("travel-date").setAttribute("min", today);
    
    document.getElementById("search-form").addEventListener("submit", handleSearch);
    document.getElementById("booking-form").addEventListener("submit", handleBooking);
});

async function handleSearch(event) {
    event.preventDefault();
    
    const source = document.getElementById("source").value;
    const destination = document.getElementById("destination").value;
    const date = document.getElementById("travel-date").value;
    const timePeriod = document.getElementById("travel-time").value;

    // Build query parameters
    const params = new URLSearchParams({
        source: source,
        destination: destination,
        date: date
    });
    
    if (timePeriod) {
        params.append("time_period", timePeriod);
    }

    try {
        const response = await fetch(`${API_BASE}/search?${params}`);
        const buses = await response.json();
        
        displayResults(buses);
        
        // Show results section, hide search section
        document.getElementById("search-section").classList.add("hidden");
        document.getElementById("results-section").classList.remove("hidden");
    } catch (error) {
        alert("Error searching buses. Please try again.");
        console.error(error);
    }
}

function displayResults(buses) {
    const busList = document.getElementById("bus-list");
    busList.innerHTML = '';

    if (buses.length === 0) {
        busList.innerHTML = '<p class="no-results">No buses found for your criteria. Try different dates or cities.</p>';
        return;
    }

    buses.forEach(bus => {
        const card = document.createElement("div");
        card.className = "bus-card";
        card.dataset.id = bus.id;
        
        const timeStr = bus.departure_time.substring(0, 5);

        card.innerHTML = `
            <div class="card-left">
                <div class="route-info">
                    <span class="city">${bus.source}</span> 
                    <span class="arrow">→</span> 
                    <span class="city">${bus.destination}</span>
                </div>
                <div class="schedule-info">
                    <span>📅 ${bus.departure_date}</span>
                    <span>⏰ ${timeStr}</span>
                </div>
            </div>
            <div class="card-right">
                <strong>$${bus.base_price}</strong>
                <span class="seats">${bus.available_seats} seats left</span>
            </div>
        `;
        
        card.onclick = () => selectBus(bus);
        busList.appendChild(card);
    });
}

function selectBus(bus) {
    // Store selected bus data
    document.getElementById("selected-bus-id").value = bus.id;
    
    // Display selected bus info
    const infoDiv = document.getElementById("selected-bus-info");
    infoDiv.innerHTML = `
        <p><strong>Selected Route:</strong> ${bus.source} → ${bus.destination}</p>
        <p><strong>Date:</strong> ${bus.departure_date} at ${bus.departure_time.substring(0, 5)}</p>
        <p><strong>Price:</strong> $${bus.base_price}</p>
    `;
    
    // Show booking form, hide results
    document.getElementById("results-section").classList.add("hidden");
    document.getElementById("booking-section").classList.remove("hidden");
}

async function handleBooking(event) {
    event.preventDefault();
    
    const busId = document.getElementById("selected-bus-id").value;
    if (!busId) {
        alert("No bus selected!");
        return;
    }

    const payload = {
        user_name: document.getElementById("name").value,
        user_email: document.getElementById("email").value,
        user_phone: document.getElementById("phone").value,
        bus_id: parseInt(busId)
    };

    try {
        const response = await fetch(`${API_BASE}/book`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const err = await response.json();
            alert(`Booking Failed: ${err.detail}`);
            return;
        }

        const ticket = await response.json();
        displayTicket(ticket);
    } catch (error) {
        alert("Network error. Please try again.");
    }
}

function displayTicket(ticket) {
    document.getElementById("booking-section").classList.add("hidden");
    document.getElementById("ticket-section").classList.remove("hidden");

    document.getElementById("res-id").textContent = ticket.ticket_id;
    document.getElementById("res-route").textContent = ticket.route;
    document.getElementById("res-price").textContent = ticket.price.toFixed(2);
    document.getElementById("res-status").textContent = ticket.status;
}

function resetSearch() {
    document.getElementById("results-section").classList.add("hidden");
    document.getElementById("search-section").classList.remove("hidden");
}