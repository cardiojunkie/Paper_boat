"use client";

import { KeyRound, Save, X } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { getOpenRouterSettings, updateOpenRouterApiKey } from "../lib/api";

export function OpenRouterSettings() {
  const queryClient = useQueryClient();
  const [apiKey, setApiKey] = useState("");
  const [message, setMessage] = useState("");
  const query = useQuery({ queryKey: ["openrouter-settings"], queryFn: getOpenRouterSettings });
  const mutation = useMutation({
    mutationFn: updateOpenRouterApiKey,
    onSuccess: (data) => {
      queryClient.setQueryData(["openrouter-settings"], data);
      setApiKey("");
      setMessage(data.configured ? "Saved." : "Cleared.");
    },
  });

  const save = (event: FormEvent) => {
    event.preventDefault();
    mutation.mutate(apiKey);
  };

  return (
    <form className="panel" onSubmit={save}>
      <div className="row between">
        <h2>OpenRouter</h2>
        <span className="status-pill">{query.data?.configured ? "Key configured" : "No key"}</span>
      </div>
      <div className="field-block">
        <input
          className="input"
          type="password"
          value={apiKey}
          placeholder="API key"
          onChange={(event) => {
            setApiKey(event.target.value);
            setMessage("");
          }}
        />
      </div>
      <div className="row">
        <button className="button primary" disabled={!apiKey.trim() || mutation.isPending}>
          <Save size={16} /> Save
        </button>
        <button className="button" type="button" disabled={mutation.isPending} onClick={() => mutation.mutate("")}>
          <X size={16} /> Clear
        </button>
        {query.data?.model && (
          <span className="muted">
            <KeyRound size={14} /> {query.data.model}
          </span>
        )}
      </div>
      {message && <p className="muted">{message}</p>}
      {query.error && <p className="error">{query.error.message}</p>}
      {mutation.error && <p className="error">{mutation.error.message}</p>}
    </form>
  );
}
