import { useState } from 'react';
import { Upload, Loader2, CheckCircle } from 'lucide-react';
import { api } from '../services/api';
import toast from 'react-hot-toast';

export default function BatchExtract() {
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<Array<{ name: string; status: string }>>([]);

  const handleBatchExtract = async () => {
    if (files.length === 0) return;
    setLoading(true);
    const newResults: Array<{ name: string; status: string }> = [];

    for (const file of files) {
      try {
        await api.extract(file);
        newResults.push({ name: file.name, status: 'success' });
      } catch {
        newResults.push({ name: file.name, status: 'failed' });
      }
    }

    setResults(newResults);
    setLoading(false);
    toast.success(`Processed ${files.length} files`);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Batch Extract</h1>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <input
          type="file"
          accept=".pdf,.png,.jpg,.jpeg"
          multiple
          onChange={(e) => setFiles(Array.from(e.target.files || []))}
          className="mb-4"
        />

        <p className="text-sm text-gray-500 mb-4">{files.length} file(s) selected</p>

        <button
          onClick={handleBatchExtract}
          disabled={files.length === 0 || loading}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center"
        >
          {loading ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <Upload className="w-5 h-5 mr-2" />}
          {loading ? 'Processing...' : 'Extract All'}
        </button>
      </div>

      {results.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Results</h2>
          <ul className="space-y-2">
            {results.map((r, i) => (
              <li key={i} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <span>{r.name}</span>
                <CheckCircle className={`w-5 h-5 ${r.status === 'success' ? 'text-green-500' : 'text-red-500'}`} />
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
