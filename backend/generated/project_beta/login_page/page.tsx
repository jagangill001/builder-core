export default function LoginPage() {
  return (
    <main style={{ padding: "2rem", fontFamily: "Arial, sans-serif" }}>
      <h1>Login Page</h1>
      <p>Sign in to access the dashboard.</p>

      <form style={{ display: "grid", gap: "1rem", maxWidth: "400px", marginTop: "1rem" }}>
        <input type="email" placeholder="Email address" style={{ padding: "0.75rem" }} />
        <input type="password" placeholder="Password" style={{ padding: "0.75rem" }} />
        <button type="submit" style={{ padding: "0.75rem", background: "black", color: "white", border: "none" }}>
          Login
        </button>
      </form>
    </main>
  );
}
