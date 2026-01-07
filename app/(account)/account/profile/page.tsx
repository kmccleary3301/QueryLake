export default function Page() {
  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Profile</h1>
        <p className="text-sm text-muted-foreground">Manage your user profile and personal details.</p>
      </div>
      <div className="rounded-lg border border-dashed border-border p-6 text-sm text-muted-foreground">
        Update display name, email, and profile preferences here.
      </div>
    </div>
  );
}
