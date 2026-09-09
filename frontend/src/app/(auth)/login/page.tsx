"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/lib/store";

export default function LoginPage() {
  const router = useRouter();
  const { setUser, setTokens } = useAuthStore();
  const [email, setEmail] = useState("ivannextlevel@yahoo.com");
  const [password, setPassword] = useState("DevPass123!");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [debug, setDebug] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setDebug("Submitting...");
    setLoading(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      setDebug(`Fetching ${apiUrl}/api/v1/auth/login ...`);

      const res = await fetch(`${apiUrl}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();
      setDebug(`Response: ${res.status} - keys: ${Object.keys(data).join(", ")}`);

      if (!res.ok) {
        setError(data?.error?.message || data?.detail || `Login failed (${res.status})`);
        setLoading(false);
        return;
      }

      const { tokens, user } = data;
      setDebug(`Login OK! User: ${user?.email}, Token: ${tokens?.access_token?.slice(0, 20)}...`);
      setTokens(tokens.access_token, tokens.refresh_token);
      setUser(user);

      // Small delay to let state persist before navigating
      setTimeout(() => {
        window.location.href = "/dashboard";
      }, 500);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(`Network error: ${msg}`);
      setDebug(`Catch: ${msg}`);
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: "0 auto", padding: 24 }}>
      <h1 style={{ fontSize: 24, fontWeight: "bold", marginBottom: 8 }}>Sign In</h1>
      <p style={{ color: "#666", marginBottom: 24 }}>Sign in to your SelfPublisherForge account</p>

      {error && (
        <div style={{ background: "#fee", border: "1px solid #c00", padding: 12, borderRadius: 6, marginBottom: 16, color: "#c00" }}>
          {error}
        </div>
      )}

      {debug && (
        <div style={{ background: "#eef", border: "1px solid #00c", padding: 8, borderRadius: 6, marginBottom: 16, fontSize: 12, color: "#006" }}>
          {debug}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: "block", marginBottom: 4, fontWeight: 500 }}>Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{ width: "100%", padding: 8, border: "1px solid #ccc", borderRadius: 6, fontSize: 14 }}
          />
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={{ display: "block", marginBottom: 4, fontWeight: 500 }}>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{ width: "100%", padding: 8, border: "1px solid #ccc", borderRadius: 6, fontSize: 14 }}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          style={{
            width: "100%",
            padding: 12,
            background: loading ? "#999" : "#2563eb",
            color: "white",
            border: "none",
            borderRadius: 6,
            fontSize: 16,
            fontWeight: 600,
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "Signing in..." : "Sign In"}
        </button>
      </form>

      <p style={{ marginTop: 16, textAlign: "center", color: "#666" }}>
        Don&apos;t have an account?{" "}
        <Link href="/register" style={{ color: "#2563eb" }}>
          Create one
        </Link>
      </p>
    </div>
  );
}
