"use client";

import { FormEvent, useState } from "react";

type Booking = {
  id: number;
  customer: string;
  service: string;
  date: string;
  status: string;
};

const starterBookings: Booking[] = [
  { id: 1, customer: "Ava Johnson", service: "Brake inspection", date: "2026-04-17", status: "Confirmed" },
  { id: 2, customer: "Marco Smith", service: "Oil change", date: "2026-04-18", status: "Pending" },
];

export default function BookingPage() {
  const [bookings, setBookings] = useState(starterBookings);
  const [customer, setCustomer] = useState("");
  const [service, setService] = useState("");
  const [date, setDate] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!customer.trim() || !service.trim() || !date) {
      return;
    }

    setBookings((current) => [
      {
        id: Date.now(),
        customer: customer.trim(),
        service: service.trim(),
        date,
        status: "Pending",
      },
      ...current,
    ]);
    setCustomer("");
    setService("");
    setDate("");
  }

  return (
    <main style={{ display: "grid", gap: "1.5rem" }}>
      <section style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: "16px", padding: "1.5rem" }}>
        <h1 style={{ marginTop: 0 }}>Repair Booking Page</h1>
        <p style={{ color: "#4b5563" }}>
          Capture service appointments, keep the shop schedule visible, and review incoming requests in one place.
        </p>

        <form onSubmit={handleSubmit} style={{ display: "grid", gap: "0.75rem", marginTop: "1rem", maxWidth: "560px" }}>
          <input
            value={customer}
            onChange={(event) => setCustomer(event.target.value)}
            type="text"
            placeholder="Customer name"
            style={{ padding: "0.85rem", border: "1px solid #d1d5db", borderRadius: "12px" }}
          />
          <input
            value={service}
            onChange={(event) => setService(event.target.value)}
            type="text"
            placeholder="Requested service"
            style={{ padding: "0.85rem", border: "1px solid #d1d5db", borderRadius: "12px" }}
          />
          <input
            value={date}
            onChange={(event) => setDate(event.target.value)}
            type="date"
            style={{ padding: "0.85rem", border: "1px solid #d1d5db", borderRadius: "12px" }}
          />
          <button
            type="submit"
            style={{ width: "fit-content", padding: "0.85rem 1rem", border: "none", borderRadius: "12px", background: "#111827", color: "white", fontWeight: 600 }}
          >
            Add booking
          </button>
        </form>
      </section>

      <section style={{ display: "grid", gap: "1rem" }}>
        {bookings.map((booking) => (
          <article key={booking.id} style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: "16px", padding: "1rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
              <div>
                <h2 style={{ marginTop: 0, marginBottom: "0.35rem" }}>{booking.customer}</h2>
                <p style={{ margin: 0, color: "#4b5563" }}>{booking.service}</p>
              </div>
              <div style={{ textAlign: "right" }}>
                <p style={{ margin: 0, fontWeight: 600 }}>{booking.date}</p>
                <span style={{ display: "inline-block", marginTop: "0.35rem", padding: "0.3rem 0.6rem", borderRadius: "999px", background: "#e0f2fe", color: "#0c4a6e", fontSize: "0.85rem" }}>
                  {booking.status}
                </span>
              </div>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
