import Link from "next/link";

import { Button } from "@/components/ui/button";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
} from "@/components/ui/breadcrumb";

type DashboardPageProps = {
  params: Promise<{ workspace: string }>;
};

const quickLinks = [
  {
    title: "Collections",
    description: "Organize knowledge bases and retrieval-ready corpora.",
    href: "collections",
  },
  {
    title: "Files",
    description: "Upload and parse documents into your collections.",
    href: "files",
  },
  {
    title: "Toolchains",
    description: "Build and version workflow graphs for your apps.",
    href: "toolchains",
  },
  {
    title: "Runs",
    description: "Monitor live runs and replay historical sessions.",
    href: "runs",
  },
];

export default async function Page({ params }: DashboardPageProps) {
  const { workspace } = await params;
  return (
    <div className="space-y-8">
      <div>
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink href={`/w/${workspace}`}>Workspace</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbItem>
              <BreadcrumbPage>Dashboard</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
        <h1 className="text-2xl font-semibold">Workspace dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Overview of activity, usage, recent runs, and collections.
        </p>
      </div>

      <section className="grid gap-4 md:grid-cols-2">
        {quickLinks.map((link) => (
          <div
            key={link.title}
            className="rounded-lg border border-border bg-card/40 p-5"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-base font-semibold">{link.title}</h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  {link.description}
                </p>
              </div>
              <Button asChild size="sm" variant="outline">
                <Link href={`/w/${workspace}/${link.href}`}>Open</Link>
              </Button>
            </div>
          </div>
        ))}
      </section>

      <section className="rounded-lg border border-dashed border-border p-6 text-sm text-muted-foreground">
        Workspace analytics, live run summaries, and usage insights will appear
        here once the data plumbing is connected.
      </section>
    </div>
  );
}
