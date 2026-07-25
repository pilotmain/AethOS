/** Workspace suite — Documents tab API (handoff §8). Draft-only; never auto-publishes. */

import { apiBase, apiFetch } from "@/lib/api";

export type WorkspaceDocFormat = "markdown" | "text" | "csv" | "html";

export type DocumentSummary = {
  id: string;
  title: string;
  format: WorkspaceDocFormat;
  char_count?: number;
  created_at?: number;
  updated_at?: number;
  draft_only?: boolean;
};

export type WorkspaceDocument = DocumentSummary & {
  content: string;
};

export type DocumentListResponse = {
  ok: boolean;
  error?: string;
  document_count?: number;
  documents: DocumentSummary[];
};

const base = () => `${apiBase()}/api/v1/human/workspace/documents`;

export async function listDocuments(limit = 100): Promise<DocumentListResponse> {
  const res = await apiFetch(`${base()}?limit=${limit}`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) return { ok: false, error: `http_${res.status}`, documents: [] };
  return res.json() as Promise<DocumentListResponse>;
}

export async function getDocument(docId: string): Promise<{ ok: boolean; error?: string; document?: WorkspaceDocument }> {
  const res = await apiFetch(`${base()}/${encodeURIComponent(docId)}`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) return { ok: false, error: `http_${res.status}` };
  return res.json();
}

export async function createDocument(input: {
  title: string;
  content?: string;
  format?: WorkspaceDocFormat;
}): Promise<{ ok: boolean; error?: string; document?: DocumentSummary }> {
  const res = await apiFetch(base(), {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) return { ok: false, error: `http_${res.status}` };
  return res.json();
}

export async function updateDocument(
  docId: string,
  input: { title?: string; content?: string; format?: WorkspaceDocFormat },
): Promise<{ ok: boolean; error?: string; document?: DocumentSummary }> {
  const res = await apiFetch(`${base()}/${encodeURIComponent(docId)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) return { ok: false, error: `http_${res.status}` };
  return res.json();
}

export async function deleteDocument(docId: string): Promise<{ ok: boolean; error?: string }> {
  const res = await apiFetch(`${base()}/${encodeURIComponent(docId)}`, { method: "DELETE" });
  if (!res.ok) return { ok: false, error: `http_${res.status}` };
  return res.json();
}
