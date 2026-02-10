"use client";

import { useState, useCallback } from "react";
import { useImportRoyalties, type RoyaltyImportRequest } from "../hooks";

const PLATFORMS = [
  { value: "kdp", label: "Amazon KDP" },
  { value: "ingram_spark", label: "IngramSpark" },
  { value: "draft2digital", label: "Draft2Digital" },
] as const;

export function RoyaltyImporter() {
  const [platform, setPlatform] = useState<RoyaltyImportRequest["platform"]>("kdp");
  const [fileName, setFileName] = useState<string>("");
  const [fileContent, setFileContent] = useState<string>("");
  const [dragActive, setDragActive] = useState(false);

  const importRoyalties = useImportRoyalties();

  const handleFileRead = useCallback((file: File) => {
    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = (event) => {
      const result = event.target?.result as string;
      // Extract base64 from data URL
      const base64 = result.includes(",") ? result.split(",")[1] : result;
      setFileContent(base64);
    };
    reader.readAsDataURL(file);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);
      const file = e.dataTransfer.files[0];
      if (file && file.name.endsWith(".csv")) {
        handleFileRead(file);
      }
    },
    [handleFileRead]
  );

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileRead(file);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!fileContent) return;

    importRoyalties.mutate({
      platform,
      file_content: fileContent,
      file_name: fileName,
    });
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Import Royalties</h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="platform-select" className="block text-sm font-medium text-gray-700 mb-1">
            Platform
          </label>
          <select
            id="platform-select"
            value={platform}
            onChange={(e) => setPlatform(e.target.value as RoyaltyImportRequest["platform"])}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {PLATFORMS.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
        </div>

        <div
          className={`border-2 border-dashed rounded-md p-6 text-center transition-colors ${
            dragActive
              ? "border-blue-500 bg-blue-50"
              : "border-gray-300 hover:border-gray-400"
          }`}
          onDragOver={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
        >
          {fileName ? (
            <div>
              <p className="text-sm text-gray-900 font-medium">{fileName}</p>
              <button
                type="button"
                onClick={() => {
                  setFileName("");
                  setFileContent("");
                }}
                className="mt-2 text-sm text-red-600 hover:text-red-800"
              >
                Remove
              </button>
            </div>
          ) : (
            <div>
              <p className="text-sm text-gray-600">
                Drag and drop a CSV file here, or{" "}
                <label htmlFor="file-upload" className="text-blue-600 hover:text-blue-800 cursor-pointer">
                  browse
                </label>
              </p>
              <input
                id="file-upload"
                type="file"
                accept=".csv"
                onChange={handleFileInput}
                className="hidden"
              />
              <p className="mt-1 text-xs text-gray-500">CSV files only</p>
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={importRoyalties.isPending || !fileContent}
          className="w-full px-4 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {importRoyalties.isPending ? "Importing..." : "Import Royalties"}
        </button>

        {importRoyalties.isSuccess && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-md">
            <p className="text-sm text-green-800">
              Imported {importRoyalties.data.records_imported} records
              {importRoyalties.data.records_skipped > 0 &&
                ` (${importRoyalties.data.records_skipped} skipped)`}
            </p>
            {importRoyalties.data.errors.length > 0 && (
              <ul className="mt-2 text-xs text-yellow-700 list-disc list-inside">
                {importRoyalties.data.errors.map((err, i) => (
                  <li key={i}>{err}</li>
                ))}
              </ul>
            )}
          </div>
        )}

        {importRoyalties.isError && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-800">
              Import failed: {importRoyalties.error.message}
            </p>
          </div>
        )}
      </form>
    </div>
  );
}
