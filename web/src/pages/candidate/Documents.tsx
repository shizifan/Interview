import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCandidateStore } from '@/stores/candidateStore';
import { confirmOcr } from '@/api/candidate';
import type { Document } from '@/types';

const docTypes = [
  { type: 1, label: '身份证', icon: '🪪' },
  { type: 2, label: '驾驶证', icon: '🚗' },
  { type: 3, label: '从业资格证', icon: '📜' },
  { type: 4, label: '体检报告', icon: '🏥' },
];

const ocrFieldLabels: Record<string, string> = {
  name: '姓名',
  id_number: '身份证号',
  gender: '性别',
  birth_date: '出生日期',
  address: '住址',
  license_number: '驾驶证号',
  license_type: '准驾类型',
  issue_date: '初次领证日期',
  valid_until: '有效期至',
  cert_number: '资格证号',
  cert_type: '证书类型',
  result: '体检结论',
};

function parseOcr(ocrResult: string | Record<string, string> | null): Record<string, string> {
  if (!ocrResult) return {};
  if (typeof ocrResult === 'string') {
    try {
      return JSON.parse(ocrResult);
    } catch {
      return {};
    }
  }
  return ocrResult;
}

function OcrPanel({
  doc,
  candidateId,
  onUpdated,
}: {
  doc: Document;
  candidateId: number;
  onUpdated: () => void;
}) {
  const ocrData = parseOcr(doc.ocr_result);
  const [editing, setEditing] = useState(false);
  const [fields, setFields] = useState<Record<string, string>>(ocrData);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setFields(parseOcr(doc.ocr_result));
    setEditing(false);
  }, [doc.ocr_result]);

  if (Object.keys(ocrData).length === 0) return null;

  const handleSave = async () => {
    setSaving(true);
    try {
      await confirmOcr(candidateId, doc.id, fields);
      onUpdated();
      setEditing(false);
    } catch (err) {
      alert(err instanceof Error ? err.message : '保存失败');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mt-3 bg-gray-50 rounded-lg p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-500 font-medium">OCR 识别结果</span>
        {!editing ? (
          <button
            onClick={() => setEditing(true)}
            className="text-xs text-blue-600 hover:text-blue-700"
          >
            修正
          </button>
        ) : (
          <div className="flex gap-2">
            <button
              onClick={() => { setFields(ocrData); setEditing(false); }}
              className="text-xs text-gray-500 hover:text-gray-600"
            >
              取消
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="text-xs text-blue-600 hover:text-blue-700 font-medium"
            >
              {saving ? '保存中...' : '确认保存'}
            </button>
          </div>
        )}
      </div>
      <div className="space-y-1.5">
        {Object.entries(fields).map(([key, val]) => (
          <div key={key} className="flex items-center gap-2 text-sm">
            <span className="text-gray-400 w-24 shrink-0 text-right">
              {ocrFieldLabels[key] || key}：
            </span>
            {editing ? (
              <input
                value={val}
                onChange={(e) => setFields({ ...fields, [key]: e.target.value })}
                className="flex-1 px-2 py-0.5 border border-gray-300 rounded text-gray-800 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
              />
            ) : (
              <span className="text-gray-700">{val}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

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
      <p className="text-sm text-gray-500">请上传以下证件照片，系统将自动识别验证。如识别有误可点击"修正"进行更正。</p>

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

              {/* OCR核对面板 */}
              {doc && (
                <OcrPanel
                  doc={doc}
                  candidateId={candidate.id}
                  onUpdated={loadDocuments}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
