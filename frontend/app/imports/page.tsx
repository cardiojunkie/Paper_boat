import { ImportUpload } from "../../components/import-upload";

export default function ImportsPage() {
  return (
    <main className="page">
      <h1>Import products</h1>
      <p className="muted">Accepted file type: .xlsx. Each row must include a SKU column.</p>
      <ImportUpload />
    </main>
  );
}
