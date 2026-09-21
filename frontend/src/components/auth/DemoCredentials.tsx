/**
 * The seeded demo login, shown only outside production.
 *
 * It exists so anyone running this locally can see a populated account without
 * signing up first. Printing credentials on a real sign-in page would be a
 * liability, so the block does not render when NODE_ENV is production.
 */
export function DemoCredentials() {
  if (process.env.NODE_ENV === "production") return null;

  return (
    <div className="mt-7 rounded-[10px] border border-dashed border-border bg-bg-subtle p-3.5">
      <p className="text-[11px] font-semibold uppercase tracking-[0.07em] text-faint">
        Demo account
      </p>
      <p className="mt-1.5 text-[12.5px] leading-relaxed text-muted">
        Signs you in as a seeded student with saved items and preferences already set.
      </p>
      <dl className="mt-2 font-mono text-[12px] text-text">
        <div className="flex gap-2">
          <dt className="text-faint">email</dt>
          <dd>student@zenkai.dev</dd>
        </div>
        <div className="flex gap-2">
          <dt className="text-faint">pass</dt>
          <dd>zenkai-demo-2026</dd>
        </div>
      </dl>
      <p className="mt-2 text-[11px] text-faint">
        Shown in development only. A reviewer account exists at reviewer@zenkai.dev with the
        password zenkai-review-2026.
      </p>
    </div>
  );
}
