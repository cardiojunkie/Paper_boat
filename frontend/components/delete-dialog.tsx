"use client";

import { Trash2 } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { deleteByFilter, deleteSelected, previewDelete } from "../lib/api";
import type { ProductFilters } from "../lib/types";

export function DeleteControls({
  selectedIds,
  filters,
  onDeleted,
}: {
  selectedIds: string[];
  filters: ProductFilters;
  onDeleted: () => void;
}) {
  const queryClient = useQueryClient();
  const [preview, setPreview] = useState<{ count: number; phrase: string } | null>(null);
  const [confirmation, setConfirmation] = useState("");
  const [message, setMessage] = useState("");
  const selectedDelete = useMutation({
    mutationFn: deleteSelected,
    onSuccess: (data) => {
      setMessage(`Deleted ${data.deleted_count} products`);
      onDeleted();
      queryClient.invalidateQueries({ queryKey: ["products"] });
    },
  });
  const filterPreview = useMutation({
    mutationFn: () => previewDelete(filters),
    onSuccess: (data) => setPreview({ count: data.count, phrase: data.confirmation_phrase }),
  });
  const filterDelete = useMutation({
    mutationFn: () => deleteByFilter(filters, preview?.count ?? 0, confirmation),
    onSuccess: (data) => {
      setMessage(`Deleted ${data.deleted_count} products`);
      setPreview(null);
      setConfirmation("");
      onDeleted();
      queryClient.invalidateQueries({ queryKey: ["products"] });
    },
  });

  return (
    <div className="delete-controls">
      <div className="delete-actions">
        <button
          className="button danger"
          disabled={!selectedIds.length || selectedDelete.isPending}
          onClick={() => window.confirm(`Delete ${selectedIds.length} selected products? This cannot be undone.`) && selectedDelete.mutate(selectedIds)}
        >
          <Trash2 size={16} /> Delete
        </button>
        <button className="text-button danger-text" disabled={filterPreview.isPending} onClick={() => filterPreview.mutate()}>
          Delete by filter
        </button>
      </div>
      {message && <p className="muted action-message" aria-live="polite">{message}</p>}
      {selectedDelete.error && <p className="error">{selectedDelete.error.message}</p>}
      {filterPreview.error && <p className="error">{filterPreview.error.message}</p>}
      {preview && (
        <div className="danger-confirmation">
          <span className="error">Deleting every product matching the active filters: {preview.count}</span>
          <input aria-label="Delete confirmation phrase" className="input" value={confirmation} onChange={(event) => setConfirmation(event.target.value)} placeholder={preview.phrase} />
          <button className="button danger" disabled={confirmation !== preview.phrase || filterDelete.isPending} onClick={() => filterDelete.mutate()}>
            Confirm filter delete
          </button>
        </div>
      )}
      {filterDelete.error && <p className="error">{filterDelete.error.message}</p>}
    </div>
  );
}
