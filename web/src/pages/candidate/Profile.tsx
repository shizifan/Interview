import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCandidateStore } from '@/stores/candidateStore';

const genderOptions = [
  { value: 1, label: '男' },
  { value: 2, label: '女' },
];

const educationOptions = ['小学', '初中', '高中/中专', '大专', '本科', '硕士及以上'];

export default function Profile() {
  const { candidate, updateProfile } = useCandidateStore();
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  const [form, setForm] = useState({
    name: '',
    gender: 1,
    age: '',
    education: '',
    work_experience: '',
    address: '',
  });

  useEffect(() => {
    if (!candidate) {
      navigate('/');
      return;
    }
    setForm({
      name: candidate.name || '',
      gender: candidate.gender || 1,
      age: candidate.age ? String(candidate.age) : '',
      education: candidate.education || '',
      work_experience: String(candidate.work_experience || ''),
      address: candidate.address || '',
    });
  }, [candidate, navigate]);

  const handleSave = async () => {
    if (!form.name.trim()) {
      setMsg('请输入姓名');
      return;
    }
    setSaving(true);
    setMsg('');
    try {
      await updateProfile({
        name: form.name.trim(),
        gender: form.gender,
        age: form.age ? Number(form.age) : undefined,
        education: form.education || undefined,
        work_experience: form.work_experience ? Number(form.work_experience) : undefined,
        address: form.address || undefined,
      });
      setMsg('保存成功');
    } catch (e) {
      setMsg(e instanceof Error ? e.message : '保存失败');
    } finally {
      setSaving(false);
    }
  };

  if (!candidate) return null;

  return (
    <div className="space-y-4 pb-20">
      <h2 className="text-xl font-bold text-gray-800">个人信息</h2>

      <div className="bg-white rounded-xl p-4 shadow-sm space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-600 mb-1">姓名 *</label>
          <input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-base focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="请输入真实姓名"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-600 mb-1">性别</label>
          <div className="flex gap-3">
            {genderOptions.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setForm({ ...form, gender: opt.value })}
                className={`flex-1 py-2 rounded-lg border text-center transition-colors ${
                  form.gender === opt.value
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-600 mb-1">年龄</label>
          <input
            type="number"
            value={form.age}
            onChange={(e) => setForm({ ...form, age: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-base focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="请输入年龄"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-600 mb-1">学历</label>
          <select
            value={form.education}
            onChange={(e) => setForm({ ...form, education: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-base focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">请选择</option>
            {educationOptions.map((opt) => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-600 mb-1">驾驶经验（年）</label>
          <input
            type="number"
            value={form.work_experience}
            onChange={(e) => setForm({ ...form, work_experience: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-base focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="请输入年数"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-600 mb-1">家庭住址</label>
          <input
            value={form.address}
            onChange={(e) => setForm({ ...form, address: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-base focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="请输入住址"
          />
        </div>
      </div>

      {msg && (
        <p className={`text-sm text-center ${msg.includes('成功') ? 'text-green-600' : 'text-red-500'}`}>{msg}</p>
      )}

      <button
        onClick={handleSave}
        disabled={saving}
        className="w-full py-3 bg-blue-600 text-white text-lg font-medium rounded-xl hover:bg-blue-700 disabled:opacity-50 transition-colors"
      >
        {saving ? '保存中...' : '保存'}
      </button>
    </div>
  );
}
