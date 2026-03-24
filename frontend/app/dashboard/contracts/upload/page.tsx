"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { Upload, File, X, Loader } from "lucide-react";
import toast from "react-hot-toast";
import { apiClient } from "@/services/api";

export default function UploadContractPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [metadata, setMetadata] = useState({
    counterparty_name: "",
    contract_type: "Service Agreement",
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (selectedFile.type !== "application/pdf") {
        toast.error("Please upload a PDF file");
        return;
      }
      if (selectedFile.size > 50 * 1024 * 1024) {
        toast.error("File size must be less than 50MB");
        return;
      }
      setFile(selectedFile);
      setErrors({});
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) {
      if (droppedFile.type !== "application/pdf") {
        toast.error("Please upload a PDF file");
        return;
      }
      if (droppedFile.size > 50 * 1024 * 1024) {
        toast.error("File size must be less than 50MB");
        return;
      }
      setFile(droppedFile);
      setErrors({});
    }
  };

  const handleMetadataChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    const { name, value } = e.target;
    setMetadata((prev) => ({
      ...prev,
      [name]: value,
    }));
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    if (!file) newErrors.file = "Please select a file";
    if (!metadata.counterparty_name.trim())
      newErrors.counterparty_name = "Counterparty name is required";
    if (!metadata.contract_type)
      newErrors.contract_type = "Contract type is required";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLoading(true);
    try {
      await apiClient.uploadContract(file!, metadata);
      toast.success("Contract uploaded successfully!");
      router.push("/dashboard/contracts");
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900">Upload Contract</h1>
        <p className="text-slate-600 mt-1">
          Upload a PDF document for AI-powered analysis
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* File Upload */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-3">
            Contract File *
          </label>

          {!file ? (
            <div
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition ${
                errors.file
                  ? "border-red-400 bg-red-50"
                  : "border-slate-300 hover:border-blue-400 hover:bg-blue-50"
              }`}
            >
              <Upload className="w-12 h-12 text-slate-400 mx-auto mb-3" />
              <p className="text-sm font-medium text-slate-900">
                Drag and drop your PDF here or click to browse
              </p>
              <p className="text-xs text-slate-500 mt-1">
                Maximum file size: 50MB
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                className="hidden"
              />
            </div>
          ) : (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <File className="w-6 h-6 text-blue-600" />
                <div>
                  <p className="font-medium text-slate-900">{file.name}</p>
                  <p className="text-xs text-slate-600">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setFile(null)}
                className="p-1 hover:bg-blue-100 rounded transition"
              >
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>
          )}
          {errors.file && (
            <p className="text-red-500 text-xs mt-2">{errors.file}</p>
          )}
        </div>

        {/* Counterparty Name */}
        <div>
          <label
            htmlFor="counterparty_name"
            className="block text-sm font-medium text-slate-700 mb-2"
          >
            Counterparty Name *
          </label>
          <input
            type="text"
            id="counterparty_name"
            name="counterparty_name"
            value={metadata.counterparty_name}
            onChange={handleMetadataChange}
            placeholder="e.g., Acme Corp"
            className={`w-full px-4 py-2 border rounded-lg outline-none transition ${
              errors.counterparty_name
                ? "border-red-500 focus:ring-red-500"
                : "border-slate-300 focus:ring-blue-500"
            } focus:ring-2 focus:border-transparent`}
          />
          {errors.counterparty_name && (
            <p className="text-red-500 text-xs mt-1">
              {errors.counterparty_name}
            </p>
          )}
        </div>

        {/* Contract Type */}
        <div>
          <label
            htmlFor="contract_type"
            className="block text-sm font-medium text-slate-700 mb-2"
          >
            Contract Type *
          </label>
          <select
            id="contract_type"
            name="contract_type"
            value={metadata.contract_type}
            onChange={handleMetadataChange}
            className={`w-full px-4 py-2 border rounded-lg outline-none transition ${
              errors.contract_type
                ? "border-red-500 focus:ring-red-500"
                : "border-slate-300 focus:ring-blue-500"
            } focus:ring-2 focus:border-transparent`}
          >
            <option value="Service Agreement">Service Agreement</option>
            <option value="NDA">Non-Disclosure Agreement</option>
            <option value="Employment">Employment Agreement</option>
            <option value="License">License Agreement</option>
            <option value="Purchase">Purchase Agreement</option>
            <option value="Lease">Lease Agreement</option>
            <option value="Other">Other</option>
          </select>
          {errors.contract_type && (
            <p className="text-red-500 text-xs mt-1">{errors.contract_type}</p>
          )}
        </div>

        {/* Submit Buttons */}
        <div className="flex gap-4 pt-6">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium py-2 rounded-lg transition flex items-center justify-center gap-2"
          >
            {loading && <Loader className="w-4 h-4 animate-spin" />}
            {loading ? "Uploading..." : "Upload & Analyze"}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-900 font-medium py-2 rounded-lg transition"
          >
            Cancel
          </button>
        </div>
      </form>

      {/* Info Box */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">What happens next?</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>
            ✓ Our AI will extract text from your contract using advanced OCR
          </li>
          <li>
            ✓ Legal analysis will identify key clauses and potential risks
          </li>
          <li>
            ✓ You'll receive a detailed risk assessment and recommendations
          </li>
          <li>
            ✓ All analysis is based on Indian legal statutes and best practices
          </li>
        </ul>
      </div>
    </div>
  );
}
