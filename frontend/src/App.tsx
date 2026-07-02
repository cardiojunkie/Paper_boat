import { Loader2, Search } from 'lucide-react';
import { FormEvent, useState } from 'react';
import ResultsCard, { MatchResponse } from './components/ResultsCard';

export default function App() {
  const [name, setName] = useState('');
  const [brand, setBrand] = useState('');
  const [competitorTarget, setCompetitorTarget] = useState('Amazon');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<MatchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('http://localhost:8000/api/evaluate-match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product: { name, brand },
          competitor_target: competitorTarget,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to evaluate product match.');
      }

      const data: MatchResponse = await response.json();
      setResult(data);
    } catch (submitError) {
      setError((submitError as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-100 p-6">
      <div className="mx-auto max-w-3xl rounded-2xl bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-bold text-slate-900">Search-Based Product Matching</h1>
        <p className="mt-1 text-sm text-slate-500">Entity Resolution Dashboard</p>

        <form className="mt-6 grid gap-4" onSubmit={handleSubmit}>
          <input
            required
            className="rounded-lg border border-slate-300 p-3"
            placeholder="Product Name"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
          <input
            required
            className="rounded-lg border border-slate-300 p-3"
            placeholder="Brand"
            value={brand}
            onChange={(event) => setBrand(event.target.value)}
          />
          <select
            className="rounded-lg border border-slate-300 p-3"
            value={competitorTarget}
            onChange={(event) => setCompetitorTarget(event.target.value)}
          >
            <option>Amazon</option>
            <option>Noon</option>
            <option>Sharaf DG</option>
          </select>
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-3 text-white disabled:opacity-70"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
            {loading ? 'Finding Match...' : 'Find Match'}
          </button>
        </form>

        {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}
        {result ? <ResultsCard data={result} /> : null}
      </div>
    </main>
  );
}
