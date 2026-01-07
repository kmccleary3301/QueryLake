export default function Page() {
  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Preferences</h1>
        <p className="text-sm text-muted-foreground">Customize appearance, keyboard shortcuts, and workspace defaults.</p>
      </div>
      <div className="rounded-lg border border-dashed border-border p-6 text-sm text-muted-foreground">
        This page is part of the new QueryLake workspace experience. We are wiring data sources, actions, and UI flows next.
      </div>
    </div>
  );
}
