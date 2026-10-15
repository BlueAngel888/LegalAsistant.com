'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X } from 'lucide-react';
import { DocumentType } from '@/lib/types';
import { useI18n } from './I18nProvider';

interface DocumentUploadProps {
  onUploadSuccess: (documentId: string, fileName: string) => void;
  onUploadError: (error: string) => void;
}

export function DocumentUpload({ onUploadSuccess, onUploadError }: DocumentUploadProps) {
  const { t } = useI18n();
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [documentType, setDocumentType] = useState<DocumentType>(DocumentType.CONTRACT);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setFiles((prev) => [...prev, ...acceptedFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
  });

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      onUploadError(t.upload.selectAtLeastOne);
      return;
    }

    setUploading(true);

    try {
      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('documentType', documentType);

        const response = await fetch('/api/documents', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.error || t.upload.uploadFailed);
        }

        const data = await response.json();

        if (!data.success) {
          throw new Error(data.error || t.upload.uploadFailed);
        }

        onUploadSuccess(data.documentId, file.name);
      }

      setFiles([]);
    } catch (error) {
      onUploadError(error instanceof Error ? error.message : t.upload.uploadFailed);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Document Type Selection */}
      <div>
        <label className="form-label">{t.upload.documentType}</label>
        <select
          value={documentType}
          onChange={(e) => setDocumentType(e.target.value as DocumentType)}
          className="form-input"
          disabled={uploading}
        >
          {Object.values(DocumentType).map((value) => (
            <option key={value} value={value}>
              {t.documentTypes[value]}
            </option>
          ))}
        </select>
      </div>

      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition ${
          isDragActive
            ? 'border-cyan-400 bg-cyan-400/10'
            : 'border-white/10 hover:border-gray-400 bg-white/5'
        } ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <input {...getInputProps()} disabled={uploading} />
        <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
        <p className="text-lg font-medium text-white mb-2">
          {isDragActive ? t.upload.dropHere : t.upload.dragDrop}
        </p>
        <p className="text-sm text-slate-300">
          {t.upload.orClick}
        </p>
      </div>

      {/* Files List */}
      {files.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-white">{t.upload.selectedFiles}</h3>
          <div className="space-y-2">
            {files.map((file, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 bg-white/10 rounded-md"
              >
                <div className="flex items-center gap-3">
                  <File className="w-5 h-5 text-slate-300" />
                  <div>
                    <p className="text-sm font-medium text-white">{file.name}</p>
                    <p className="text-xs text-slate-400">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => removeFile(idx)}
                  disabled={uploading}
                  className="p-1 text-slate-300 hover:text-red-600 disabled:opacity-50"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Upload Button */}
      <button
        onClick={handleUpload}
        disabled={files.length === 0 || uploading}
        className="w-full btn btn-primary btn-large disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {uploading ? t.upload.uploading : t.upload.uploadButton.replace('{count}', String(files.length))}
      </button>
    </div>
  );
}
