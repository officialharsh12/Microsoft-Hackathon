import React, { useState } from 'react';
import { Upload, FileSpreadsheet, ArrowRight, CheckCircle2, AlertCircle, Loader2, Sparkles, RefreshCw } from 'lucide-react';
import { api } from '../services/api';

export default function UploadPage({ onAnalysisComplete }) {
  const [file, setFile] = useState(null);
  const [uploadData, setUploadData] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStep, setAnalysisStep] = useState(0);
  const [error, setError] = useState(null);

  // Column mapping state
  const [textCol, setTextCol] = useState('');
  const [dateCol, setDateCol] = useState('');
  const [ratingCol, setRatingCol] = useState('');
  const [idCol, setIdCol] = useState('');

  const pipelineSteps = [
    'Validating CSV & scrubbing PII...',
    'Running DistilBERT SST-2 Sentiment Inference...',
    'Running RoBERTa GoEmotions Emotion Profiling...',
    'Generating 384-d MiniLM Sentence Embeddings...',
    'Clustering review vectors & discovering themes...',
    'Computing explainable severity scores & trend trajectories...',
    'Persisting product issues & evidence chain...'
  ];

  const handleFileChange = async (selectedFile) => {
    if (!selectedFile) return;
    setFile(selectedFile);
    setError(null);
    setIsUploading(true);

    try {
      const data = await api.uploadCSV(selectedFile);
      setUploadData(data);
      setTextCol(data.detected_text_column || data.columns[0] || '');
      setDateCol(data.detected_date_column || '');
      setRatingCol(data.detected_rating_column || '');
      setIdCol(data.detected_id_column || '');
    } catch (err) {
      setError(err.message);
    } finally {
      setIsUploading(false);
    }
  };

  const handleUseDemo = async () => {
    setError(null);
    setIsUploading(true);
    try {
      // Create synthetic File from backend demo data by fetching it or passing blob
      const demoRes = await fetch('/api/reviews/upload', {
        method: 'POST',
        body: (() => {
          const form = new FormData();
          // We can fetch demo_reviews.csv from public or request upload
          return form;
        })()
      }).catch(() => null);

      // Fetch demo CSV content
      const demoCsvText = await fetch('/data/demo_reviews.csv')
        .then(r => r.text())
        .catch(async () => {
          // Fallback fetch from raw endpoint or simulate demo file
          return "review_id,review_text,rating,date,app_version,platform\nDEMO-001,\"Payment failed on checkout. Card was debited.\",1,2026-03-01,2.4.1,iOS";
        });

      const demoBlob = new Blob([demoCsvText], { type: 'text/csv' });
      const demoFile = new File([demoBlob], 'demo_reviews.csv', { type: 'text/csv' });
      await handleFileChange(demoFile);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsUploading(false);
    }
  };

  const handleStartAnalysis = async () => {
    if (!uploadData || !textCol) {
      setError('Please select a valid review text column.');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setAnalysisStep(0);

    // Animate pipeline status for UX
    const interval = setInterval(() => {
      setAnalysisStep(prev => (prev < pipelineSteps.length - 1 ? prev + 1 : prev));
    }, 2800);

    try {
      const payload = {
        dataset_id: uploadData.dataset_id,
        text_column: textCol,
        date_column: dateCol || null,
        rating_column: ratingCol || null,
        id_column: idCol || null,
      };

      const result = await api.analyzeDataset(payload);
      clearInterval(interval);
      if (onAnalysisComplete) {
        onAnalysisComplete(uploadData.dataset_id);
      }
    } catch (err) {
      clearInterval(interval);
      setError(err.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-10 space-y-8">
      {/* Page Title */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Automated AI Review Pipeline</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-100 tracking-tight">
          Ingest & Analyze Customer Reviews
        </h1>
        <p className="text-slate-400 max-w-2xl mx-auto text-sm sm:text-base">
          Upload any CSV containing raw customer reviews. Our multi-model ML pipeline classifies sentiment, detects emotions, groups semantic clusters, and pinpoints high-severity product issues.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-500/30 text-red-200 flex items-start space-x-3 text-sm animate-in fade-in">
          <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">Pipeline Error: </span>
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Upload Box */}
      {!uploadData && (
        <div className="p-8 sm:p-12 border-2 border-dashed border-slate-700 hover:border-indigo-500/60 rounded-2xl bg-slate-900/40 hover:bg-slate-900/60 transition-all text-center space-y-6">
          <div className="w-16 h-16 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center mx-auto text-indigo-400">
            {isUploading ? <Loader2 className="w-8 h-8 animate-spin" /> : <Upload className="w-8 h-8" />}
          </div>

          <div className="space-y-2">
            <h3 className="text-lg font-bold text-slate-200">
              Drag & Drop your CSV file here, or browse
            </h3>
            <p className="text-xs text-slate-400">
              Supports CSV with review text, optional date, star ratings, and metadata
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <label className="cursor-pointer px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-all shadow-lg shadow-indigo-600/20">
              Browse CSV File
              <input
                type="file"
                accept=".csv"
                className="hidden"
                onChange={(e) => handleFileChange(e.target.files[0])}
                disabled={isUploading}
              />
            </label>

            <span className="text-xs text-slate-500 font-medium">OR</span>

            <button
              onClick={async () => {
                setIsUploading(true);
                try {
                  const res = await fetch('/api/reviews/upload-demo', {
                    method: 'POST',
                    headers: {
                      'Authorization': `Bearer ${localStorage.getItem('feedbackpulse_token')}`
                    }
                  });
                  if (!res.ok) throw new Error('Failed to load demo dataset');
                  const d = await res.json();
                  setUploadData(d);
                  setTextCol(d.detected_text_column || 'review_text');
                  setDateCol(d.detected_date_column || 'date');
                  setRatingCol(d.detected_rating_column || 'rating');
                  setIdCol(d.detected_id_column || 'review_id');
                } catch (err) {
                  setError(err.message);
                } finally {
                  setIsUploading(false);
                }
              }}
              disabled={isUploading}
              className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-medium text-sm transition-all flex items-center space-x-2"
            >
              <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
              <span>Load All 100 Demo Reviews</span>
            </button>
          </div>
        </div>
      )}

      {/* Column Mapping & Preview Section */}
      {uploadData && !isAnalyzing && (
        <div className="space-y-6 bg-slate-900/60 border border-slate-800 rounded-2xl p-6 sm:p-8">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-6 border-b border-slate-800 gap-4">
            <div>
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <h2 className="text-lg font-bold text-slate-100">
                  Uploaded: <span className="font-mono text-indigo-300">{uploadData.filename}</span>
                </h2>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Detected <span className="font-semibold text-slate-200">{uploadData.total_rows} rows</span> and {uploadData.columns.length} columns. Verify column selections below:
              </p>
            </div>

            <button
              onClick={() => { setUploadData(null); setFile(null); }}
              className="text-xs text-slate-400 hover:text-slate-200 px-3 py-1.5 rounded-lg border border-slate-700/60 hover:bg-slate-800"
            >
              Choose different file
            </button>
          </div>

          {/* Column Selectors */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            
            {/* Text Column (Required) */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
                <span>Review Text Column <span className="text-rose-400">*</span></span>
              </label>
              <select
                value={textCol}
                onChange={(e) => setTextCol(e.target.value)}
                className="w-full bg-slate-950 border border-indigo-500/50 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {uploadData.columns.map((col) => (
                  <option key={col} value={col}>{col}</option>
                ))}
              </select>
              <p className="text-[11px] text-indigo-400">Target text for AI models</p>
            </div>

            {/* Date Column (Optional) */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">
                Date Column (Optional)
              </label>
              <select
                value={dateCol}
                onChange={(e) => setDateCol(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">-- None (No Dates) --</option>
                {uploadData.columns.map((col) => (
                  <option key={col} value={col}>{col}</option>
                ))}
              </select>
              <p className="text-[11px] text-slate-500">Enables temporal trend detection</p>
            </div>

            {/* Rating Column (Optional) */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">
                Rating / Stars (Optional)
              </label>
              <select
                value={ratingCol}
                onChange={(e) => setRatingCol(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">-- None (No Rating) --</option>
                {uploadData.columns.map((col) => (
                  <option key={col} value={col}>{col}</option>
                ))}
              </select>
              <p className="text-[11px] text-slate-500">Numerical rating (1 to 5)</p>
            </div>

            {/* ID Column (Optional) */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">
                Review ID Column (Optional)
              </label>
              <select
                value={idCol}
                onChange={(e) => setIdCol(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">-- Auto-generate IDs --</option>
                {uploadData.columns.map((col) => (
                  <option key={col} value={col}>{col}</option>
                ))}
              </select>
              <p className="text-[11px] text-slate-500">Preserves original identifiers</p>
            </div>

          </div>

          {/* Sample Rows Preview Table */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Data Preview (First 5 Rows)
            </h4>
            <div className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="min-w-full divide-y divide-slate-800 text-left text-xs">
                <thead className="bg-slate-950/80 text-slate-400 font-semibold">
                  <tr>
                    {uploadData.columns.map((col) => (
                      <th key={col} className="px-3 py-2.5 truncate max-w-[200px]">
                        {col}
                        {col === textCol && <span className="ml-1 text-[10px] text-indigo-400 font-normal">(Text)</span>}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 bg-slate-900/30 text-slate-300">
                  {uploadData.sample_rows.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/40">
                      {uploadData.columns.map((col) => (
                        <td key={col} className="px-3 py-2 truncate max-w-[220px]">
                          {String(row[col] ?? '')}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Action Button */}
          <div className="flex justify-end pt-4">
            <button
              onClick={handleStartAnalysis}
              className="flex items-center space-x-2 px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-sky-500 hover:from-indigo-500 hover:to-sky-400 text-white font-semibold text-sm transition-all shadow-lg shadow-indigo-500/25"
            >
              <span>Start AI Review Analysis</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Analysis Progress Overlay */}
      {isAnalyzing && (
        <div className="p-8 sm:p-12 border border-slate-800 rounded-2xl bg-slate-900/80 text-center space-y-6 animate-in fade-in">
          <div className="relative w-20 h-20 mx-auto">
            <div className="absolute inset-0 rounded-full border-4 border-indigo-500/20 animate-ping"></div>
            <div className="w-20 h-20 rounded-full bg-indigo-600/20 border-2 border-indigo-500 flex items-center justify-center text-indigo-400">
              <Loader2 className="w-10 h-10 animate-spin" />
            </div>
          </div>

          <div className="space-y-2 max-w-md mx-auto">
            <h3 className="text-xl font-bold text-slate-100">
              Processing Review Intelligence Pipeline
            </h3>
            <p className="text-sm text-indigo-300 font-medium">
              {pipelineSteps[analysisStep]}
            </p>
            <p className="text-xs text-slate-500">
              Executing batched inference with DistilBERT, RoBERTa GoEmotions, and MiniLM sentence embeddings.
            </p>
          </div>

          {/* Pipeline mini-stepper */}
          <div className="flex justify-center items-center space-x-2 pt-4">
            {pipelineSteps.map((_, i) => (
              <div
                key={i}
                className={`h-1.5 rounded-full transition-all duration-300 ${
                  i === analysisStep
                    ? 'w-8 bg-indigo-500'
                    : i < analysisStep
                    ? 'w-3 bg-emerald-500'
                    : 'w-3 bg-slate-800'
                }`}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
