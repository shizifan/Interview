import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCandidateStore } from '@/stores/candidateStore';

const docTypes = [
  { type: 1, label: '身份证', icon: '🪪' },
  { type: 2, label: '驾驶证', icon: '🚗' },
  { type: 3, label: '从业资格证', icon: '📜' },
  { type: 4, label: '体检报告', icon: '🏥' },
];

export default function Documents() {
  const { candidate, documents, loadDocuments, uploadDocument } = useCandidateStore();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [selectedType, setSelectedType] = useState<number | null>(null);

  useEffect(() => {
    if (!candidate) {
      navigate('/');
      return;
    }
    loadDocuments();
  }, [candidate, navigate, loadDocuments]);

  const handleUpload = (docType: number) => {
    setSelectedType(docType);
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || selectedType === null) return;
    setUploading(true);
    try {
      await uploadDocument(file, selectedType);
    } catch (err) {
      alert(err instanceof Error ? err.message : '上传失败');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const getDocByType = (type: number) => documents.find((d) => d.type === type);

  if (!candidate) return null;

  return (
    <div className="space-y-4 pb-20">
      <h2 className="text-xl font-bold text-gray-800">材料上传</h2>
      <p className="text-sm text-gray-500">请上传以下证件照片，系统将自动识别验证</p>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFileChange}
      />

      <div className="space-y-3">
        {docTypes.map(({ type, label, icon }) => {
          const doc = getDocByType(type);
          const hasDoc = !!doc;
          return (
            <div key={type} className="bg-white rounded-xl p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{icon}</span>
                  <div>
                    <div className="font-medium text-gray-800">{label}</div>
                    {hasDoc ? (
                      <div className="text-xs text-green-600 mt-0.5">
                        已上传 · 评分: {doc.score}分
                      </div>
                    ) : (
                      <div className="text-xs text-gray-400 mt-0.5">未上传</div>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => handleUpload(type)}
                  disabled={uploading}
                  className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    hasDoc
                      ? 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  {uploading && selectedType === type ? '上传中...' : hasDoc ? '重新上传' : '上传'}
                </button>
              </div>

              {/* OCR结果 */}
              {doc?.ocr_result && (
                <div className="mt-3 bg-gray-50 rounded-lg p-3">
                  <div className="text-xs text-gray-500 mb-1">识别结果</div>
                  <div className="grid grid-cols-2 gap-1">
                    {Object.entries(doc.ocr_result).map(([key, val]) => (
                      <div key={key} className="text-xs">
                        <span className="text-gray-400">{key}：</span>
                        <span className="text-gray-700">{val}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
