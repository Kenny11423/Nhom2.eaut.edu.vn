const state = {
  bridge: null,
  currentUser: null,
  selectedTrip: null,
  selectedCarriage: null,
  selectedSeat: null,
  trips: [],
  carriages: [],
  seats: [],
  tickets: [],
  schedules: [],
};

function parseResponse(raw) {
  try {
    return JSON.parse(raw);
  } catch (_error) {
    return { ok: false, message: "Lỗi xử lý dữ liệu từ hệ thống." };
  }
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
  document.getElementById("stat-sold").textContent = (dashboard?.tickets_sold ?? 0).toLocaleString();
  document.getElementById("stat-revenue").textContent = currency(dashboard?.revenue);
  document.getElementById("stat-trips").textContent = (dashboard?.active_trips ?? 0).toLocaleString();
  document.getElementById("stat-occupancy").textContent = `${dashboard?.occupancy_rate ?? 0}%`;
}

function renderTrips(trips) {
  state.trips = trips || [];
  const container = document.getElementById("trip-list");
  if (!state.trips.length) {
    container.innerHTML = '<div class="list-item">Không có chuyến phù hợp.</div>';
    return;
  }

  container.innerHTML = state.trips.map((trip) => `
    <article class="list-item">
      <strong>${trip.trip_code} - ${trip.train_code}</strong>
      <div>${trip.origin_name} → ${trip.destination_name}</div>
      <div style="font-size: 13px; color: var(--text-muted);">
        ${trip.departure_date} | ${trip.departure_time} - ${trip.arrival_time}
      </div>
      <div style="margin-top: 8px; display: flex; justify-content: space-between;">
        <span>Còn ${trip.available_seats} ghế</span>
        <span>${currency(trip.base_price)}</span>
      </div>
      <button onclick="selectTrip(${trip.id})" style="margin-top: 12px;">Chọn chuyến</button>
    </article>
  `).join("");
}

async function selectTrip(tripId) {
  state.selectedTrip = state.trips.find((trip) => trip.id === tripId) || null;
  state.selectedCarriage = null;
  state.selectedSeat = null;
  document.getElementById("selected-trip").innerHTML = "";
  document.getElementById("selected-seat").textContent = "Chưa chọn toa/ghế";
  document.getElementById("seat-map").innerHTML = "";

  const response = parseResponse(await state.bridge.getTripCarriages(JSON.stringify({
    trip_id: tripId,
    boarding_station_trip_id: state.selectedTrip.boarding_station_trip_id,
    alighting_station_trip_id: state.selectedTrip.alighting_station_trip_id,
  })));
  if (!response.ok) {
    alert(response.message);
    return;
  }

  const trip = response.data.trip;
  const itinerary = response.data.itinerary || [];
  state.carriages = response.data.carriages || [];

  document.getElementById("selected-trip").innerHTML = `
    <div class="route-box">
      <div style="font-weight: 700;">${trip.trip_code} | ${trip.origin_name} → ${trip.destination_name}</div>
      <div style="font-size: 12px;">${trip.departure_date} | ${trip.departure_time} - ${trip.arrival_time}</div>
      <div style="margin-top: 8px; font-size: 12px;">${itinerary.map((stop) => `${stop.stop_order}. ${stop.station_code}`).join(" • ")}</div>
    </div>
  `;

  renderCarriages(state.carriages);
}

function renderCarriages(carriages) {
  const container = document.getElementById("carriage-list");
  if (!carriages.length) {
    container.innerHTML = '<div class="list-item">Chuyến này chưa có toa.</div>';
    return;
  }

  container.innerHTML = carriages.map((carriage) => `
    <button class="carriage-chip ${state.selectedCarriage?.id === carriage.id ? "active" : ""}" onclick="selectCarriage(${carriage.id})">
      <strong>${carriage.carriage_code}</strong>
      <span>${carriage.seat_type}</span>
      <span>${carriage.available_seats}/${carriage.total_seats} ghế</span>
    </button>
  `).join("");
}

async function selectCarriage(carriageTripId) {
  state.selectedCarriage = state.carriages.find((item) => item.id === carriageTripId) || null;
  state.selectedSeat = null;
  renderCarriages(state.carriages);

  const response = parseResponse(await state.bridge.getCarriageSeats(JSON.stringify({
    carriage_trip_id: carriageTripId,
    boarding_station_trip_id: state.selectedTrip?.boarding_station_trip_id,
    alighting_station_trip_id: state.selectedTrip?.alighting_station_trip_id,
  })));
  if (!response.ok) {
    alert(response.message);
    return;
  }
  state.seats = response.data.seats || [];
  renderSeats(state.seats);
}

function renderSeats(seats) {
  const container = document.getElementById("seat-map");
  if (!seats.length) {
    container.innerHTML = '<div class="hint">Chọn toa để xem danh sách ghế.</div>';
    return;
  }
  container.innerHTML = seats.map((seat) => `
    <button
      class="seat ${seat.status} ${state.selectedSeat?.id === seat.id ? "selected" : ""}"
      ${seat.status === "booked" ? "disabled" : ""}
      onclick="chooseSeat(${seat.id})">
      <strong>${seat.carriage_code}-${seat.seat_code}</strong>
      <div>${seat.seat_type}</div>
      <div>${(seat.seat_price / 1000).toLocaleString()}k</div>
    </button>
  `).join("");
}

function chooseSeat(seatId) {
  state.selectedSeat = state.seats.find((seat) => seat.id === seatId) || null;
  if (!state.selectedSeat) {
    return;
  }
  document.getElementById("selected-seat").textContent =
    `Đã chọn ${state.selectedSeat.carriage_code}-${state.selectedSeat.seat_code} | ${state.selectedSeat.seat_type} | ${currency(state.selectedSeat.seat_price)}`;
  renderSeats(state.seats);
}

function renderTickets(tickets) {
  state.tickets = tickets || [];
  const container = document.getElementById("ticket-list");
  if (!state.tickets.length) {
    container.innerHTML = '<div class="list-item">Chưa có vé nào.</div>';
    return;
  }
  container.innerHTML = state.tickets.map((ticket) => `
    <article class="list-item">
      <strong>${ticket.ticket_code} - ${ticket.full_name}</strong>
      <div>${ticket.boarding_name} → ${ticket.alighting_name} | ${ticket.train_code}</div>
      <div style="font-size: 13px;">${ticket.carriage_code}-${ticket.seat_code} | ${currency(ticket.price)}</div>
      <div style="margin-top: 8px; display: flex; justify-content: space-between; align-items: center;">
        <span>${ticket.status === "cancelled" ? "Đã hủy" : "Đã đặt"}</span>
        ${ticket.status !== "cancelled" ? `<button onclick="cancelTicket('${ticket.ticket_code}')" style="background: var(--danger);">Hủy vé</button>` : ""}
      </div>
    </article>
  `).join("");
}

function renderSchedules(schedules) {
  state.schedules = schedules || [];
  const container = document.getElementById("schedule-list");
  if (!state.schedules.length) {
    container.innerHTML = '<div class="list-item">Không có lịch trình.</div>';
    return;
  }
  container.innerHTML = state.schedules.map((item) => `
    <article class="list-item">
      <strong>${item.trip_code} - ${item.train_code}</strong>
      <div>${item.origin_name} → ${item.destination_name}</div>
      <div style="font-size: 13px; color: var(--text-muted);">
        ${item.departure_date} | ${item.departure_time} - ${item.arrival_time}
      </div>
      <div style="margin-top: 8px;">Ga dừng: ${item.stop_count} | Toa: ${item.carriage_count} | Ghế trống: ${item.available_seats}/${item.total_seats}</div>
    </article>
  `).join("");
}

async function cancelTicket(ticketCode) {
  if (!confirm(`Hủy vé ${ticketCode}?`)) return;
  const response = parseResponse(await state.bridge.cancelTicket(JSON.stringify({ ticket_code: ticketCode })));
  if (!response.ok) {
    alert(response.message);
    return;
  }
  renderDashboard(response.data.dashboard);
  renderTickets(response.data.tickets);
}

async function bootstrapData() {
  const response = parseResponse(await state.bridge.bootstrap());
  if (!response.ok) return;
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
    if (!response.ok) {
      document.getElementById("login-message").textContent = response.message;
      return;
    }
    state.currentUser = response.data.user;
    document.getElementById("user-badge").innerHTML = `
      <div style="font-weight: 700;">${state.currentUser.full_name}</div>
      <div style="font-size: 11px; opacity: 0.8;">${state.currentUser.role}</div>
    `;
    document.getElementById("login-screen").classList.remove("active");
    document.getElementById("main-screen").classList.add("active");
    renderDashboard(response.data.dashboard);
    bootstrapData();
  });

  document.getElementById("search-btn").addEventListener("click", async () => {
    const payload = {
      origin: document.getElementById("origin").value,
      destination: document.getElementById("destination").value,
      travel_date: document.getElementById("travel-date").value,
    };
    const response = parseResponse(await state.bridge.searchTrips(JSON.stringify(payload)));
    if (response.ok) {
      renderTrips(response.data.trips);
    }
  });

  document.getElementById("booking-btn").addEventListener("click", async () => {
    if (!state.selectedTrip || !state.selectedSeat) {
      document.getElementById("booking-message").textContent = "Vui lòng chọn chuyến, toa và ghế.";
      return;
    }
    const payload = {
      trip_id: state.selectedTrip.id,
      seat_id: state.selectedSeat.id,
      boarding_station_trip_id: state.selectedTrip.boarding_station_trip_id,
      alighting_station_trip_id: state.selectedTrip.alighting_station_trip_id,
      full_name: document.getElementById("full-name").value,
      id_number: document.getElementById("id-number").value,
      phone: document.getElementById("phone").value,
    };
    const response = parseResponse(await state.bridge.createBooking(JSON.stringify(payload)));
    document.getElementById("booking-message").textContent = response.message;
    if (!response.ok) return;
    renderDashboard(response.data.dashboard);
    renderTickets(response.data.tickets);
    await selectTrip(state.selectedTrip.id);
    document.getElementById("full-name").value = "";
    document.getElementById("id-number").value = "";
    document.getElementById("phone").value = "";
  });

  document.getElementById("ticket-search-btn").addEventListener("click", async () => {
    const query = document.getElementById("ticket-query").value;
    const response = parseResponse(await state.bridge.searchTickets(JSON.stringify({ query })));
    if (response.ok) {
      renderTickets(response.data.tickets);
    }
  });
}

new QWebChannel(qt.webChannelTransport, (channel) => {
  state.bridge = channel.objects.bridge;
  setupEvents();
});
