export default function VendorDashboard() {
  const vendors = [
    { name: "Vendor A", price: "$1200", contact: "vendora@example.com" },
    { name: "Vendor B", price: "$980", contact: "vendorb@example.com" },
    { name: "Vendor C", price: "$1100", contact: "vendorc@example.com" }
  ];

  return (
    <main style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: "16px", padding: "1.5rem" }}>
      <h1>Vendor Dashboard</h1>
      <p>Compare supplier quotes and contacts.</p>

      <table style={{ width: "100%", borderCollapse: "collapse", marginTop: "1rem" }}>
        <thead>
          <tr>
            <th style={{ border: "1px solid #ccc", padding: "0.75rem", textAlign: "left" }}>Vendor</th>
            <th style={{ border: "1px solid #ccc", padding: "0.75rem", textAlign: "left" }}>Price</th>
            <th style={{ border: "1px solid #ccc", padding: "0.75rem", textAlign: "left" }}>Contact</th>
          </tr>
        </thead>
        <tbody>
          {vendors.map((vendor) => (
            <tr key={vendor.name}>
              <td style={{ border: "1px solid #ccc", padding: "0.75rem" }}>{vendor.name}</td>
              <td style={{ border: "1px solid #ccc", padding: "0.75rem" }}>{vendor.price}</td>
              <td style={{ border: "1px solid #ccc", padding: "0.75rem" }}>{vendor.contact}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
