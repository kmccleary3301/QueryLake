"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import Link from "next/link";
import FileDropzone from "@/components/ui/file-dropzone";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useContextAction } from "@/app/context-provider";
import {
  fetch_collection_document_type,
  fetchCollection,
  fetchCollectionDocuments,
} from "@/hooks/querylakeAPI";
import uploadFiles from "@/hooks/upload-files";

type CollectionSummary = {
  title: string;
  description: string;
  type: "user" | "organization" | "global";
  owner: string;
  public: boolean;
  document_count: number;
};

export default function CollectionPage() {
  const params = useParams<{ workspace: string; collectionId: string }>()!;
  const { userData, authReviewed, loginValid } = useContextAction();
  const [collection, setCollection] = useState<CollectionSummary | null>(null);
  const [documents, setDocuments] = useState<fetch_collection_document_type[]>(
    []
  );
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState<
    { name: string; progress: number }[]
  >([]);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const dropzoneRef = useRef<HTMLDivElement | null>(null);

  const refreshDocuments = useCallback(() => {
    if (!userData?.auth) return;
    fetchCollectionDocuments({
      auth: userData.auth,
      collection_id: params.collectionId,
      onFinish: (result) => {
        setDocuments(result ?? []);
      },
    });
  }, [params.collectionId, userData?.auth]);

  useEffect(() => {
    if (!authReviewed || !loginValid || !userData?.auth) {
      setLoading(false);
      return;
    }
    setLoading(true);
    fetchCollection({
      auth: userData.auth,
      collection_id: params.collectionId,
      onFinish: (result) => {
        if (result) {
          setCollection(result as CollectionSummary);
        }
        setLoading(false);
      },
    });
    refreshDocuments();
  }, [authReviewed, loginValid, userData?.auth, params.collectionId, refreshDocuments]);

  useEffect(() => {
    if (!userData?.auth) return;
    if (!documents.some((doc) => !doc.finished_processing)) return;
    const interval = setInterval(() => {
      refreshDocuments();
      fetchCollection({
        auth: userData.auth,
        collection_id: params.collectionId,
        onFinish: (result) => {
          if (result) {
            setCollection(result as CollectionSummary);
          }
        },
      });
    }, 8000);
    return () => clearInterval(interval);
  }, [documents, userData?.auth, params.collectionId, refreshDocuments]);

  const startUpload = async (files: File[]) => {
    if (!userData?.auth || files.length === 0) return;
    setUploadError(null);
    setUploading(files.map((file) => ({ name: file.name, progress: 0 })));

    const responses = await uploadFiles({
      files,
      url: "/upload/",
      parameters: {
        auth: userData.auth,
        collection_hash_id: params.collectionId,
      },
      on_upload_progress: (progress, index) => {
        setUploading((prev) =>
          prev.map((entry, idx) =>
            idx === index ? { ...entry, progress } : entry
          )
        );
      },
      on_response: (response) => {
        if ((response as { success?: boolean }).success === false) {
          setUploadError("One or more files failed to upload.");
        }
      },
    });

    setUploading([]);
    refreshDocuments();
    fetchCollection({
      auth: userData.auth,
      collection_id: params.collectionId,
      onFinish: (result) => {
        if (result) {
          setCollection(result as CollectionSummary);
        }
      },
    });
    const failures = responses.filter(
      (response) => (response as { success?: boolean }).success === false
    );
    if (failures.length > 0) {
      toast(`Uploaded with ${failures.length} failure(s).`);
    } else {
      toast("Upload complete.");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbLink href={`/w/${params.workspace}/collections`}>
                  Collections
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbPage>{params.collectionId}</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
          <h1 className="text-2xl font-semibold">
            {collection?.title ?? `Collection: ${params.collectionId}`}
          </h1>
          <p className="text-sm text-muted-foreground">
            Workspace {params.workspace}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline">
            <Link href={`/w/${params.workspace}/collections`}>
              Back to collections
            </Link>
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              dropzoneRef.current?.scrollIntoView({ behavior: "smooth" });
            }}
          >
            Upload documents
          </Button>
          <Button asChild variant="outline">
            <Link href={`/w/${params.workspace}/files`}>
              Open in Files
            </Link>
          </Button>
          <Button variant="outline" disabled>
            Edit settings
          </Button>
        </div>
      </div>

      <div ref={dropzoneRef} className="rounded-lg border border-border p-4">
        <div className="text-sm font-medium">Upload documents</div>
        <p className="mt-1 text-xs text-muted-foreground">
          Drop files here to ingest them into this collection.
        </p>
        <div className="mt-4">
          <FileDropzone
            multiple
            onFile={(files) => {
              startUpload(files);
            }}
          />
        </div>
        {uploadError ? (
          <div className="mt-3 text-xs text-destructive">{uploadError}</div>
        ) : null}
        {uploading.length > 0 && (
          <div className="mt-4 space-y-2 text-xs text-muted-foreground">
            {uploading.map((entry) => (
              <div key={entry.name} className="flex items-center justify-between">
                <span>{entry.name}</span>
                <span>{entry.progress}%</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {loading ? (
        <div className="rounded-lg border border-border p-5 space-y-3">
          <Skeleton className="h-5 w-44" />
          <Skeleton className="h-4 w-64" />
          <Skeleton className="h-4 w-52" />
          <Skeleton className="h-4 w-36" />
        </div>
      ) : !collection ? (
        <div className="rounded-lg border border-dashed border-border p-6 text-sm text-muted-foreground">
          Collection not found or unavailable.
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
          <div className="rounded-lg border border-border p-5 space-y-3 text-sm">
            <div className="font-semibold">Overview</div>
            <div className="text-muted-foreground">
              {collection.description || "No description provided."}
            </div>
            <div className="grid gap-2 text-xs text-muted-foreground">
              <div className="flex justify-between">
                <span>Type</span>
                <span className="font-medium text-foreground">
                  {collection.type}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Owner</span>
                <span className="font-medium text-foreground">
                  {collection.owner}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Documents</span>
                <span className="font-medium text-foreground">
                  {collection.document_count}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Visibility</span>
                <span className="font-medium text-foreground">
                  {collection.public ? "Public" : "Private"}
                </span>
              </div>
            </div>
          </div>
          <div className="rounded-lg border border-border p-5 text-sm">
            <div className="font-semibold">Next steps</div>
            <ul className="mt-3 space-y-2 text-muted-foreground">
              <li>Upload files to populate this collection.</li>
              <li>Review parsing status and metadata.</li>
              <li>Run retrieval queries once indexed.</li>
            </ul>
          </div>
        </div>
      )}

      <div className="rounded-lg border border-border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Document</TableHead>
              <TableHead>Size</TableHead>
              <TableHead>Length</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {documents.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="py-6 text-center text-sm text-muted-foreground">
                  No documents available.
                </TableCell>
              </TableRow>
            ) : (
              documents.map((doc) => (
                <TableRow key={doc.hash_id}>
                  <TableCell className="font-medium">{doc.title}</TableCell>
                  <TableCell>{doc.size}</TableCell>
                  <TableCell>{doc.length}</TableCell>
                  <TableCell>
                    {doc.finished_processing ? "Ready" : "Processing"}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
