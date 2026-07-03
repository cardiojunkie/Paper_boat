"use client";

import { Upload } from "lucide-react";
import { useMutation } from "@tanstack/react-query";

import { uploadImport } from "../lib/api";

export function ImportUpload({ onImported }: { onImported?: () => void }) {
  const mutation = useMutation({ mutationFn: uploadImport, onSuccess: () => onImported?.() });
  const result = mutation.data;

  return (
    <div className="grid">
      <div className="panel">
        <div className="row">
          <label className="button primary">
            <Upload size={16} /> Upload .xls/.xlsx
            <input
              hidden
              type="file"
              accept=".xls,.xlsx"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) mutation.mutate(file);
              }}
            />
          </label>
          {mutation.isPending && <span className="muted">Uploading and processing...</span>}
          {mutation.error && <span className="error">{mutation.error.message}</span>}
        </div>
      </div>
      {result && (
        <div className="panel">
          <h2>Import summary</h2>
          <p>
            {result.status}: {result.inserted_rows} inserted, {result.updated_rows} updated, {result.failed_rows} failed from{" "}
            {result.total_rows} rows.
          </p>
          {result.error_summary && <p className="error">{result.error_summary}</p>}
          {!!result.errors.length && (
            <>
              <h3>Row errors</h3>
              <table>
                <thead>
                  <tr>
                    <th>Row</th>
                    <th>SKU</th>
                    <th>Code</th>
                    <th>Message</th>
                    <th>Header</th>
                  </tr>
                </thead>
                <tbody>
                  {result.errors.map((error, index) => (
                    <tr key={`${error.row_number}-${index}`}>
                      <td>{error.row_number}</td>
                      <td>{error.sku}</td>
                      <td>{error.error_code}</td>
                      <td>{error.message}</td>
                      <td>{error.field_header}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <button className="button" onClick={() => navigator.clipboard.writeText(JSON.stringify(result.errors, null, 2))}>
                Copy error report
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
