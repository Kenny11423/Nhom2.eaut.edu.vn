const state = {
  bridge: null,
  currentUser: null,
  selectedTrip: null,
  selectedSeat: null,
  tickets: [],
  schedules: [],
};

function parseResponse(raw) {
  return JSON.parse(raw);
}

function currency(value) {
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(value || 0);
}

function bindNavigation() {
  document.querySelectorAll(".nav-btn").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".nav-btn").forEach((item) => item.classList.remove("active"));
      document.querySelectorAll(".panel").forEach((panel) => panel.classList.remove("active"));
      button.classList.add("active");
      document.getElementById(button.dataset.panel).classList.add("active");
    });
  });
}

function renderDashboard(dashboard) {
  document.getElementById("stat-sold").textContent = dashboard.tickets_sold ?? 0;
  document.getElementById("stat-revenue").textContent = currency(dashboard.revenue);
  document.getElementById("stat-trips").textContent = dashboard.active_trips ?? 0;
  document.getElementById("stat-occupancy").textContent = `${dashboard.occupancy_rate ?? 0}%`;
}

function renderTrips(trips) {
  const container = document.getElementById("trip-list");
  if (!trips.length) {
    container.innerHTML = '<div class="list-item">Khong co chuyen tau phu hop.</div>';
    return;
  }

  container.innerHTML = trips.map((trip) => `
    <article class="list-item">
      <strong>${trip.trip_code} | ${trip.train_code}</strong>
      <div>${trip.origin_name} -> ${trip.destination_name}</div>
      <div>Ngay ${trip.departure_date} | ${trip.departure_time} - ${trip.arrival_time}</div>
      <div>Con trong: ${trip.available_seats} | Gia tu: ${currency(trip.base_price)}</div>
      <div class="ticket-actions">
        <button onclick="selectTrip(${trip.id})">Chon chuyen</button>
      </div>
    </article>
  `).join("");

  window.tripStore = trips;
}

async function selectTrip(tripId) {
  const trip = (window.tripStore || []).find((item) => item.id === tripId);
  state.selectedTrip = trip;
  state.selectedSeat = null;
  document.getElementById("selected-trip").textContent =
    `${trip.trip_code} | ${trip.origin_name} -> ${trip.destination_name} | ${trip.departure_date}`;

  const response = parseResponse(await state.bridge.getTripSeats(JSON.stringify({ trip_id: tripId })));
  renderSeats(response.data.seats);
}

function renderSeats(seats) {
  const container = document.getElementById("seat-map");
  container.innerHTML = seats.map((seat) => `
    <button
      class="seat ${seat.status}"
      ${seat.status === "booked" ? "disabled" : ""}
      onclick="chooseSeat(${seat.id})"
      data-seat-id="${seat.id}"
      data-seat-status="${seat.status}">
      <strong>${seat.carriage_code}-${seat.seat_code}</strong>
      <div>${seat.seat_type}</div>
      <div>${currency(seat.seat_price)}</div>
    </button>
  `).join("");

  window.seatStore = seats;
}

function chooseSeat(seatId) {
  state.selectedSeat = (window.seatStore || []).find((seat) => seat.id === seatId);
  document.querySelectorAll(".seat.available").forEach((seat) => seat.classList.remove("selected"));
  const target = document.querySelector(`[data-seat-id="${seatId}"]`);
  if (target) {
    target.classList.add("selected");
  }
}

function renderTickets(tickets) {
  state.tickets = tickets;
  const container = document.getElementById("ticket-list");
  if (!tickets.length) {
    container.innerHTML = '<div class="list-item">Chua co du lieu ve.</div>';
    return;
  }

  container.innerHTML = tickets.map((ticket) => `
    <article class="list-item">
      <strong>${ticket.ticket_code} | ${ticket.full_name}</strong>
      <div>${ticket.origin_name} -> ${ticket.destination_name} | ${ticket.train_code}</div>
      <div>Cho: ${ticket.carriage_code}-${ticket.seat_code} | Gia: ${currency(ticket.price)}</div>
      <div>Trang thai: ${ticket.status}</div>
      ${ticket.status !== "cancelled" ? `
        <div class="ticket-actions">
          <button onclick="cancelTicket('${ticket.ticket_code}')">Huy ve</button>
        </div>
      ` : ""}
    </article>
  `).join("");
}

function renderSchedules(schedules) {
  state.schedules = schedules;
  const container = document.getElementById("schedule-list");
  container.innerHTML = schedules.map((item) => `
    <article class="list-item">
      <strong>${item.trip_code} | ${item.train_code}</strong>
      <div>${item.origin_name} -> ${item.destination_name}</div>
      <div>${item.departure_date} | ${item.departure_time} - ${item.arrival_time}</div>
      <div>Trang thai: ${item.status}</div>
    </article>
  `).join("");
}

async function cancelTicket(ticketCode) {
  const response = parseResponse(await state.bridge.cancelTicket(JSON.stringify({ ticket_code: ticketCode })));
  renderDashboard(response.data.dashboard);
  renderTickets(response.data.tickets);
}

async function bootstrapData() {
  const response = parseResponse(await state.bridge.bootstrap());
  renderDashboard(response.data.dashboard);
  renderSchedules(response.data.schedules);
  renderTickets(response.data.tickets);
}

function setupEvents() {
  bindNavigation();

  document.getElementById("login-btn").addEventListener("click", async () => {
    const payload = {
      username: document.getElementById("username").value,
      password: document.getElementById("password").value,
    };
    const response = parseResponse(await state.bridge.login(JSON.stringify(payload)));
    document.getElementById("login-message").textContent = response.message;
    if (!response.ok) {
      return;
    }

    state.currentUser = response.data.user;
    document.getElementById("user-badge").textContent =
      `${state.currentUser.full_name} (${state.currentUser.role})`;
    document.getElementById("login-screen").classList.remove("active");
    document.getElementById("main-screen").classList.add("active");
    renderDashboard(response.data.dashboard);
    await bootstrapData();
  });

  document.getElementById("search-btn").addEventListener("click", async () => {
    const payload = {
      origin: document.getElementById("origin").value,
      destination: document.getElementById("destination").value,
      travel_date: document.getElementById("travel-date").value,
    };
    const response = parseResponse(await state.bridge.searchTrips(JSON.stringify(payload)));
    renderTrips(response.data.trips || []);
  });

  document.getElementById("booking-btn").addEventListener("click", async () => {
    if (!state.selectedTrip || !state.selectedSeat) {
      document.getElementById("booking-message").textContent = "Can chon chuyen tau va cho ngoi.";
      return;
    }

    const payload = {
      trip_id: state.selectedTrip.id,
      seat_id: state.selectedSeat.id,
      full_name: document.getElementById("full-name").value,
      id_number: document.getElementById("id-number").value,
      phone: document.getElementById("phone").value,
    };

    const response = parseResponse(await state.bridge.createBooking(JSON.stringify(payload)));
    document.getElementById("booking-message").textContent = response.message;
    if (!response.ok) {
      return;
    }
    renderDashboard(response.data.dashboard);
    renderTickets(response.data.tickets);
    await selectTrip(state.selectedTrip.id);
  });

  document.getElementById("ticket-search-btn").addEventListener("click", async () => {
    const query = document.getElementById("ticket-query").value;
    const response = parseResponse(await state.bridge.searchTickets(JSON.stringify({ query })));
    renderTickets(response.data.tickets || []);
  });
}

new QWebChannel(qt.webChannelTransport, (channel) => {
  state.bridge = channel.objects.bridge;
  setupEvents();
});
