import { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Clock, FileText } from 'lucide-react';
import { api } from '../services/api';

export default function Analytics() {
  const [data, setData] = useState({
    total_extractions: 0,
    success_rate: 0,
    avg_processing_time: 0,
    extractions_today: 0
  });

  useEffect(() => {
    api.getAnalytics().then(setData).catch(() => {});
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Analytics</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <FileText className="w-8 h-8 text-blue-500 mb-2" />
          <p className="text-sm text-gray-500">Total Extractions</p>
          <p className="text-2xl font-bold">{data.total_extractions}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <TrendingUp className="w-8 h-8 text-green-500 mb-2" />
          <p className="text-sm text-gray-500">Success Rate</p>
          <p className="text-2xl font-bold">{data.success_rate}%</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <Clock className="w-8 h-8 text-yellow-500 mb-2" />
          <p className="text-sm text-gray-500">Avg Processing Time</p>
          <p className="text-2xl font-bold">{data.avg_processing_time.toFixed(2)}s</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <BarChart3 className="w-8 h-8 text-purple-500 mb-2" />
          <p className="text-sm text-gray-500">Today</p>
          <p className="text-2xl font-bold">{data.extractions_today}</p>
        </div>
      </div>
    </div>
  );
}
