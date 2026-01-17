import { useParams } from 'react-router-dom';

export default function Results() {
  const { id } = useParams();

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Extraction Results</h1>
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-600">Result ID: {id}</p>
        <p className="text-sm text-gray-400 mt-2">Detailed results will appear here after extraction.</p>
      </div>
    </div>
  );
}
