export default function DashboardPage() {
  const cards = [
    { title: "Users", value: "128" },
    { title: "Requests", value: "42" },
    { title: "Modules Built", value: "7" },
    { title: "System Status", value: "Healthy" }
  ];

  return (
    <main style={{ padding: "2rem", fontFamily: "Arial, sans-serif" }}>
      <h1>Dashboard</h1>
      <p>System overview.</p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "1rem", marginTop: "1rem" }}>
        {cards.map((card) => (
          <div key={card.title} style={{ border: "1px solid #ccc", borderRadius: "12px", padding: "1rem" }}>
            <h2 style={{ margin: 0, fontSize: "1rem" }}>{card.title}</h2>
            <p style={{ fontSize: "1.5rem", fontWeight: "bold", marginTop: "0.5rem" }}>{card.value}</p>
          </div>
        ))}
      </div>
    </main>
  );
}
