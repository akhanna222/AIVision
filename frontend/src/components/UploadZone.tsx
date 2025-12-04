/**
 * Upload Zone Component with Drag & Drop
 */

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, AlertCircle } from 'lucide-react';
import { cn } from '@/utils/cn';

interface UploadZoneProps {
  onFilesSelected: (files: File[]) => void;
  maxFiles?: number;
  maxSize?: number; // in MB
  accept?: string[];
}

export function UploadZone({
  onFilesSelected,
  maxFiles = 10,
  maxSize = 50,
  accept = ['pdf', 'jpg', 'jpeg', 'png', 'tiff', 'heic'],
}: UploadZoneProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string>('');

  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: any[]) => {
      setError('');

      // Check for rejected files
      if (rejectedFiles.length > 0) {
        const reasons = rejectedFiles.map((f) => f.errors.map((e: any) => e.message).join(', '));
        setError(`Some files were rejected: ${reasons.join('; ')}`);
        return;
      }

      // Check file size
      const oversized = acceptedFiles.filter((f) => f.size > maxSize * 1024 * 1024);
      if (oversized.length > 0) {
        setError(`Files too large (max ${maxSize}MB): ${oversized.map((f) => f.name).join(', ')}`);
        return;
      }

      // Check total files
      if (files.length + acceptedFiles.length > maxFiles) {
        setError(`Maximum ${maxFiles} files allowed`);
        return;
      }

      const newFiles = [...files, ...acceptedFiles];
      setFiles(newFiles);
      onFilesSelected(newFiles);
    },
    [files, maxFiles, maxSize, onFilesSelected]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: accept.reduce(
      (acc, ext) => ({
        ...acc,
        [`application/${ext}`]: [`.${ext}`],
        [`image/${ext}`]: [`.${ext}`],
      }),
      {}
    ),
    maxFiles,
  });

  const removeFile = (index: number) => {
    const newFiles = files.filter((_, i) => i !== index);
    setFiles(newFiles);
    onFilesSelected(newFiles);
  };

  const clearAll = () => {
    setFiles([]);
    onFilesSelected([]);
    setError('');
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="w-full">
      {/* Drop Zone */}
      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all',
          isDragActive
            ? 'border-primary-500 bg-primary-50'
            : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
        )}
      >
        <input {...getInputProps()} />
        <Upload className={cn(
          'mx-auto h-12 w-12 mb-4',
          isDragActive ? 'text-primary-500' : 'text-gray-400'
        )} />
        {isDragActive ? (
          <p className="text-lg font-medium text-primary-600">Drop files here...</p>
        ) : (
          <>
            <p className="text-lg font-medium text-gray-700 mb-2">
              Drag & drop files here, or click to browse
            </p>
            <p className="text-sm text-gray-500">
              Supported: {accept.join(', ')} (Max {maxSize}MB per file, up to {maxFiles} files)
            </p>
          </>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md flex items-start gap-2">
          <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Selected Files List */}
      {files.length > 0 && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-gray-700">
              Selected Files ({files.length})
            </h3>
            <button
              onClick={clearAll}
              className="text-sm text-red-600 hover:text-red-700 font-medium"
            >
              Clear All
            </button>
          </div>

          <div className="space-y-2">
            {files.map((file, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <File className="h-5 w-5 text-gray-400 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-700 truncate">
                      {file.name}
                    </p>
                    <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                  </div>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  className="p-1 hover:bg-gray-100 rounded-full transition-colors"
                  title="Remove file"
                >
                  <X className="h-4 w-4 text-gray-500" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
