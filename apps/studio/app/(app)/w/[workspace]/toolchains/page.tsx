"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useParams } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import RuntimeModeBanner from "@/components/toolchains/runtime-mode-banner";
import { useContextAction } from "@/app/context-provider";
import { toolchainCategory } from "@/types/globalTypes";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
} from "@/components/ui/breadcrumb";

export default function Page() {
  const params = useParams<{ workspace: string }>()!;
  const { userData, authReviewed, loginValid } = useContextAction();
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");

  const categories: toolchainCategory[] = useMemo(() => {
    return userData?.available_toolchains ?? [];
  }, [userData?.available_toolchains]);

  const categoryOptions = useMemo(() => {
    const options = categories.map((category) => category.category).sort();
    return ["all", ...options];
  }, [categories]);

  const filteredCategories = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    return categories
      .filter(
        (category) => categoryFilter === "all" || category.category === categoryFilter
      )
      .map((category) => ({
        ...category,
        entries: category.entries.filter((toolchain) => {
          if (!query) return true;
          return (
            toolchain.title.toLowerCase().includes(query) ||
            toolchain.id.toLowerCase().includes(query) ||
            toolchain.category.toLowerCase().includes(query)
          );
        }),
      }))
      .filter((category) => category.entries.length > 0);
  }, [categories, categoryFilter, searchQuery]);

  return (
    <div className="space-y-6">
      <RuntimeModeBanner />

      <header className="ql-page-header">
        <div>
          <div className="ql-page-kicker">Workflow catalog</div>
          <Breadcrumb className="mt-2">
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbLink href={`/w/${params.workspace}`}>Workspace</BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbItem>
                <BreadcrumbPage>Toolchains</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
          <h1 className="ql-page-title">Toolchains</h1>
          <p className="ql-page-copy">
            Workflow definitions, reusable execution graphs, and interaction surfaces for the current workspace.
          </p>
        </div>
        <div className="ql-toolbar-strip">
          <Button asChild size="sm" variant="outline">
            <Link href={`/w/${params.workspace}/runs/new`}>New run</Link>
          </Button>
          <Button asChild size="sm">
            <Link href="/nodes/node_editor">Create toolchain (legacy builder)</Link>
          </Button>
        </div>
      </header>

      {!authReviewed ? (
        <div className="ql-panel space-y-3 p-5">
          <Skeleton className="h-4 w-40" />
          <Skeleton className="h-4 w-64" />
          <Skeleton className="h-4 w-52" />
        </div>
      ) : !loginValid || !userData ? (
        <div className="ql-panel p-6 text-sm text-muted-foreground">
          Sign in to view your toolchains.
        </div>
      ) : categories.length === 0 ? (
        <div className="ql-panel p-6 text-sm text-muted-foreground">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Empty catalog</div>
          <div className="mt-2">No toolchains found yet. Create your first workflow definition to get started.</div>
          <div className="mt-4">
            <Button asChild size="sm" variant="outline">
              <Link href="/nodes/node_editor">Create toolchain (legacy builder)</Link>
            </Button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="ql-toolbar-strip flex-wrap">
            <Input
              className="w-[280px]"
              placeholder="Search toolchains..."
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
            />
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-[240px]">
                <SelectValue placeholder="Filter by category" />
              </SelectTrigger>
              <SelectContent>
                {categoryOptions.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option === "all" ? "All categories" : option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                setSearchQuery("");
                setCategoryFilter("all");
              }}
            >
              Clear filters
            </Button>
          </div>

          {filteredCategories.length === 0 ? (
            <div className="ql-panel p-6 text-sm text-muted-foreground">
              No toolchains match your filters.
            </div>
          ) : (
            filteredCategories.map((category) => (
              <section key={category.category} className="ql-panel p-5">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/70 pb-4">
                  <div>
                    <div className="ql-page-kicker">Category</div>
                    <h2 className="mt-2 text-base font-semibold text-foreground">{category.category}</h2>
                  </div>
                  <div className="rounded-full border border-border/70 bg-background/55 px-3 py-1 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                    {category.entries.length} toolchains
                  </div>
                </div>

                <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                  {category.entries.map((toolchain) => (
                    <div key={toolchain.id} className="ql-panel-inset p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <div className="text-sm font-semibold text-foreground">{toolchain.title}</div>
                          <div className="mt-1 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                            {toolchain.id}
                          </div>
                        </div>
                        <div className="rounded-full border border-border/70 bg-background/55 px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
                          {toolchain.category}
                        </div>
                      </div>
                      <div className="mt-4 flex flex-wrap gap-2">
                        <Button asChild size="sm" variant="outline">
                          <Link href={`/w/${params.workspace}/runs/new?toolchain=${toolchain.id}`}>Run</Link>
                        </Button>
                        <Button asChild size="sm" variant="outline">
                          <Link href={`/w/${params.workspace}/toolchains/${toolchain.id}`}>Open</Link>
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            ))
          )}
        </div>
      )}
    </div>
  );
}
