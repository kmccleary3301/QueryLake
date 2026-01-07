"use client";

import Link from "next/link";
import { useState } from "react";
import { useParams } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
} from "@/components/ui/breadcrumb";

export default function Page() {
  const params = useParams<{ workspace: string }>()!;
  const [query, setQuery] = useState("");
  const [promptPreset, setPromptPreset] = useState("");
  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink href={`/w/${params.workspace}`}>Workspace</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbItem>
              <BreadcrumbPage>Playground</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
        <h1 className="text-2xl font-semibold">Playground</h1>
        <p className="text-sm text-muted-foreground">
          Quick experiments with retrieval and model calls.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-card/40 p-5">
          <h2 className="text-base font-semibold">LLM playground</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Use the legacy LLM playground UI while we wire the new workspace
            version.
          </p>
          <div className="mt-4">
            <Button asChild size="sm" variant="outline">
              <Link href="/platform/playground/llm">Open legacy playground</Link>
            </Button>
          </div>
        </div>
        <div className="rounded-lg border border-border bg-card/40 p-5">
          <h2 className="text-base font-semibold">Retrieval tests</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Run retrieval queries against workspace collections (coming soon).
          </p>
          <div className="mt-4">
            <Button size="sm" variant="outline" disabled>
              Configure retrieval
            </Button>
          </div>
        </div>
        <div className="rounded-lg border border-border bg-card/40 p-5">
          <h2 className="text-base font-semibold">Prompt presets</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Save reusable prompt templates and test them across models.
          </p>
          <div className="mt-4">
            <Button size="sm" variant="outline" disabled>
              Create preset
            </Button>
          </div>
        </div>
        <div className="rounded-lg border border-border bg-card/40 p-5">
          <h2 className="text-base font-semibold">RAG evaluations</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Benchmark retrieval + generation quality with curated test sets.
          </p>
          <div className="mt-4">
            <Button size="sm" variant="outline" disabled>
              Start evaluation
            </Button>
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-dashed border-border p-6 text-sm text-muted-foreground">
        We will add toolchain dry-runs, custom eval suites, and retrieval
        dashboards here once the new platform flows are wired.
      </div>

      <div className="rounded-lg border border-border p-5 space-y-4">
        <div className="text-base font-semibold">Retrieval quick test (stub)</div>
        <div className="text-sm text-muted-foreground">
          This is a placeholder for workspace retrieval evaluation. We will wire
          real collection selectors and results once the backend endpoints are ready.
        </div>
        <Input
          placeholder="Enter a test query"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <Button size="sm" variant="outline" disabled>
          Run retrieval
        </Button>
      </div>

      <div className="rounded-lg border border-border p-5 space-y-4">
        <div className="text-base font-semibold">Prompt presets (stub)</div>
        <Textarea
          className="min-h-[120px]"
          placeholder="Describe a prompt preset to save..."
          value={promptPreset}
          onChange={(event) => setPromptPreset(event.target.value)}
        />
        <Button size="sm" variant="outline" disabled>
          Save preset
        </Button>
        <div className="text-xs text-muted-foreground">
          Preset storage and syncing will be added in the next iteration.
        </div>
      </div>
    </div>
  );
}
