import { CheckCircle2 } from 'lucide-react';

export type MatchResponse = {
  search_url: string;
  scraped_results: string[];
  llm_evaluation: {
    exact_match_found: boolean;
    matched_competitor_title: string;
    price: number;
    confidence_score: number;
    reasoning: string;
  };
};

type Props = {
  data: MatchResponse;
};

export default function ResultsCard({ data }: Props) {
  const confidencePercent = `${Math.round(data.llm_evaluation.confidence_score * 100)}%`;

  return (
    <div className="mt-6 rounded-xl bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center gap-2 text-emerald-600">
        <CheckCircle2 className="h-5 w-5" />
        <h2 className="text-lg font-semibold">LLM Match Evaluation</h2>
      </div>
      <p className="text-sm text-slate-500">Search URL: {data.search_url}</p>
      <p className="mt-3 font-medium">Matched Title: {data.llm_evaluation.matched_competitor_title}</p>
      <p className="mt-1 text-slate-700">Price: AED {data.llm_evaluation.price}</p>
      <p className="mt-1 text-slate-700">Confidence: {confidencePercent}</p>
      <p className="mt-3 text-slate-700">Reasoning: {data.llm_evaluation.reasoning}</p>
    </div>
  );
}
