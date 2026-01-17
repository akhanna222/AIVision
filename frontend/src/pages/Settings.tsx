import { useState } from 'react';
import { Save, Key, Bell, Shield } from 'lucide-react';
import toast from 'react-hot-toast';

export default function Settings() {
  const [apiKey, setApiKey] = useState('');

  const handleSave = () => {
    toast.success('Settings saved');
  };

  return (
    <div className="p-6 max-w-2xl">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center mb-4">
            <Key className="w-5 h-5 text-gray-500 mr-2" />
            <h2 className="text-lg font-semibold">API Configuration</h2>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">API Key</label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg"
                placeholder="Enter your API key"
              />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center mb-4">
            <Bell className="w-5 h-5 text-gray-500 mr-2" />
            <h2 className="text-lg font-semibold">Notifications</h2>
          </div>
          <label className="flex items-center">
            <input type="checkbox" className="mr-2" defaultChecked />
            <span className="text-sm">Email notifications for completed extractions</span>
          </label>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center mb-4">
            <Shield className="w-5 h-5 text-gray-500 mr-2" />
            <h2 className="text-lg font-semibold">Security</h2>
          </div>
          <label className="flex items-center">
            <input type="checkbox" className="mr-2" defaultChecked />
            <span className="text-sm">Two-factor authentication</span>
          </label>
        </div>

        <button
          onClick={handleSave}
          className="bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 flex items-center"
        >
          <Save className="w-5 h-5 mr-2" />
          Save Settings
        </button>
      </div>
    </div>
  );
}
