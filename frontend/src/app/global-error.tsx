"use client";

/**
 * The last line of defence: shown only when the root layout itself fails, so
 * it brings its own <html> and <body> and leans on nothing else in the app.
 */
export default function GlobalError({ retry }: { error: Error & { digest?: string }; retry: () => void }) {
  return (
    <html lang="en">
      <body
        style={{
          margin: 0,
          minHeight: "100dvh",
          display: "grid",
          placeItems: "center",
          padding: "16px",
          fontFamily: "system-ui, -apple-system, sans-serif",
          background: "#fafafa",
          color: "#18181b",
        }}
      >
        <div style={{ maxWidth: 420, textAlign: "center" }}>
          <h1 style={{ fontSize: 17, fontWeight: 600, margin: 0 }}>Zenkai is having a moment</h1>
          <p style={{ fontSize: 14, lineHeight: 1.6, color: "#52525b", marginTop: 8 }}>
            Its server may be waking up after a quiet spell, which takes up to a minute.
          </p>
          <button
            type="button"
            onClick={() => retry()}
            style={{
              marginTop: 16,
              padding: "9px 18px",
              borderRadius: 10,
              border: 0,
              background: "#18181b",
              color: "#fff",
              fontSize: 14,
              cursor: "pointer",
            }}
          >
            Try again
          </button>
        </div>
      </body>
    </html>
  );
}
