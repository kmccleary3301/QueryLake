import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function Page() {
  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">System status</h1>
        <p className="text-sm text-muted-foreground">
          Health and connectivity checks for the QueryLake backend.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-card/40 p-5">
          <h2 className="text-base font-semibold">Backend health</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Validate that the API gateway and model services are reachable.
          </p>
          <div className="mt-4 flex gap-2">
            <Button asChild size="sm" variant="outline">
              <Link href="http://localhost:8000/healthz">Healthz</Link>
            </Button>
            <Button asChild size="sm" variant="outline">
              <Link href="http://localhost:8000/readyz">Readyz</Link>
            </Button>
          </div>
        </div>
        <div className="rounded-lg border border-border bg-card/40 p-5">
          <h2 className="text-base font-semibold">Diagnostics</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Collect version info, runtime config, and telemetry snapshots.
          </p>
          <div className="mt-4">
            <Button size="sm" variant="outline">
              Copy diagnostics (stub)
            </Button>
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-dashed border-border p-6 text-sm text-muted-foreground">
        We will wire live health probes, version metadata, and diagnostics here
        once we finalize API status endpoints.
      </div>
    </div>
  );
}
