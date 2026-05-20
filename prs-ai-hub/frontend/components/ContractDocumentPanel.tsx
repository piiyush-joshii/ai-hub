"use client";

import { useRef, useState } from "react";
import { parseDocument } from "@/lib/api";

type Props = {
  title?: string;
  filename: string;
  text: string;
  onChange: (filename: string, text: string) => void;
  readOnly?: boolean;
  emptyHint?: string;
};

export function ContractDocumentPanel({
  title = "Contract document",
  filename,
  text,
  onChange,
  readOnly = false,
  emptyHint = "Upload a contract (PDF, DOCX, or TXT) or load a sample fixture.",
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [editing, setEditing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(true);

  async function handleFile(file: File) {
    setUploadError(null);
    setUploading(true);
    try {
      const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
      if (ext === "txt") {
        const fileText = await file.text();
        onChange(file.name, fileText);
      } else if (["pdf", "docx", "doc"].includes(ext)) {
        const { filename: name, text: parsed } = await parseDocument(file);
        onChange(name, parsed);
      } else {
        setUploadError("Use PDF, DOCX, or TXT.");
        return;
      }
      setEditing(false);
      setExpanded(true);
    } catch (e: unknown) {
      setUploadError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold">{title}</h2>
          {text ? (
            <p className="mt-1 text-xs text-slate-500">
              <span className="font-data">{filename}</span>
              {" · "}
              {text.length.toLocaleString()} characters
            </p>
          ) : (
            <p className="mt-1 text-sm text-slate-500">{emptyHint}</p>
          )}
        </div>
        {!readOnly && (
          <div className="flex flex-wrap gap-2">
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.docx,.doc,.txt,application/pdf"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleFile(f);
              }}
            />
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              disabled={uploading}
              className="rounded-lg border border-brand-300 bg-brand-50 px-3 py-1.5 text-sm font-medium text-brand-800 hover:bg-brand-100 disabled:opacity-50"
            >
              {uploading ? "Parsing…" : "Replace file"}
            </button>
            {text && (
              <button
                type="button"
                onClick={() => setEditing((v) => !v)}
                className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
              >
                {editing ? "Preview" : "Edit text"}
              </button>
            )}
            <button
              type="button"
              onClick={() => setExpanded((v) => !v)}
              className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
            >
              {expanded ? "Collapse" : "Expand"}
            </button>
          </div>
        )}
      </div>

      {uploadError && (
        <p className="mt-3 text-sm text-red-600" role="alert">
          {uploadError}
        </p>
      )}

      {text && expanded && (
        <div className="mt-4">
          {editing && !readOnly ? (
            <textarea
              className="font-data h-96 w-full resize-y rounded-lg border border-slate-300 bg-slate-50 p-3 text-xs leading-relaxed text-slate-800"
              value={text}
              onChange={(e) => onChange(filename, e.target.value)}
              spellCheck={false}
            />
          ) : (
            <pre className="font-data max-h-96 overflow-auto whitespace-pre-wrap rounded-lg border border-slate-200 bg-slate-50 p-4 text-xs leading-relaxed text-slate-800">
              {text}
            </pre>
          )}
        </div>
      )}
    </section>
  );
}
