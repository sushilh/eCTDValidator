import { useState } from "react";
import axios from "axios";
import './PdfValidatorStyles.css';

export default function PdfValidatorUI() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
    setResult(null);
    setError(null);
    setProgress(0);
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a PDF file.");
      return;
    }

    setLoading(true);
    setError(null);
    setProgress(10);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post("http://127.0.0.1:8000/validate", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setProgress(percentCompleted);
        }
      });
      setResult(response.data);
      setProgress(100);
    } catch (err) {
      setError("Failed to validate PDF. Please try again.");
      setProgress(0);
    }

    setLoading(false);
  };

  return (
    <div className="flex flex-col items-center p-8 bg-gradient-to-r from-blue-50 to-gray-100 min-h-screen">
      <h1 className="text-4xl font-extrabold text-gray-800 mb-6 drop-shadow-md">📄 PDF Validator</h1>
      <div className="bg-white shadow-xl rounded-2xl p-8 w-full max-w-lg border border-gray-200">
        <label className="block text-lg font-semibold text-gray-700 mb-4">Upload Your PDF:</label>
        <div className="flex items-center space-x-2">
          <input
            type="file"
            accept="application/pdf"
            onChange={handleFileChange}
            className="w-full border border-gray-300 p-3 rounded-lg bg-white text-gray-700 cursor-pointer shadow-sm hover:border-blue-400 focus:border-blue-500"
          />
        </div>
        <button
          onClick={handleUpload}
          className="w-full px-6 py-3 mt-4 bg-gradient-to-r from-blue-500 to-blue-700 text-white font-bold rounded-lg shadow-md hover:from-blue-600 hover:to-blue-800 transition-transform transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={loading}
        >
          {loading ? "Validating..." : "Upload & Validate"}
        </button>
        {loading && (
          <div className="w-full bg-gray-300 rounded-full h-3 mt-4 overflow-hidden shadow-inner">
            <div className="bg-blue-600 h-3 rounded-full transition-all ease-in-out" style={{ width: `${progress}%` }}></div>
          </div>
        )}
      </div>

      {error && <p className="text-red-600 mt-4 font-bold text-lg">❌ {error}</p>}

      {result && (
        <div className="mt-6 bg-white shadow-xl rounded-lg p-6 w-full max-w-lg text-left border border-gray-300">
          <h2 className="text-xl font-semibold text-gray-800 mb-3">✅ Validation Result</h2>
          <pre className="text-sm text-gray-700 whitespace-pre-wrap bg-gray-100 p-4 rounded border border-gray-400 overflow-auto max-h-64 shadow-inner">
            {JSON.stringify(result, null, 2)}
          </pre>
          {result.ectdValid !== undefined && (
            <p className={`mt-2 text-lg font-semibold ${result.ectdValid ? 'text-green-600' : 'text-red-600'}`}>
              {result.ectdValid ? "✅ eCTD Compliance Check Passed" : "❌ eCTD Compliance Check Failed"}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
