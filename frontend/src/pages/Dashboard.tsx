import { useState, useEffect } from 'react';
import { BarChart3, FileText, Clock, TrendingUp } from 'lucide-react';
import { api } from '../services/api';

export default function Dashboard() {
  const [stats, setStats] = useState({ extractions: 0, templates: 0, avgTime: 0, successRate: 0 });

  useEffect(() => {
    api.getAnalytics().then(data => {
      setStats({
        extractions: data.total_extractions || 0,
        templates: data.total_templates || 0,
        avgTime: data.avg_processing_time || 0,
        successRate: data.success_rate || 0
      });
    }).catch(() => {});
  }, []);

  const cards = [
    { title: 'Total Extractions', value: stats.extractions, icon: FileText, color: 'blue' },
    { title: 'Templates', value: stats.templates, icon: BarChart3, color: 'green' },
    { title: 'Avg Time (s)', value: stats.avgTime.toFixed(2), icon: Clock, color: 'yellow' },
    { title: 'Success Rate', value: `${stats.successRate}%`, icon: TrendingUp, color: 'purple' },
  ];

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {cards.map((card) => (
          <div key={card.title} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">{card.title}</p>
                <p className="text-2xl font-bold mt-1">{card.value}</p>
              </div>
              <card.icon className={`w-10 h-10 text-${card.color}-500`} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
