import React, { useState, useEffect } from 'react';
import {
  ArrowLeft, Copy, Check, Printer, Sparkles, ShieldAlert,
  Flame, TrendingUp, AlertCircle, Terminal, HelpCircle, Loader2
} from 'lucide-react';
import { api } from '../services/api';

export default function PMBriefPage({ issueId, onBack }) {
  const [brief, setBrief] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    async function loadBrief() {
      try {
        setLoading(true);
        const data = await api.getIssueBrief(issueId);
        setBrief(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    loadBrief();
  }, [issueId]);

  const handleCopy = () => {
    if (!brief) return;
    const textContent = `
=========================================
${brief.title}
=========================================
SUMMARY:
${brief.summary}

PROBLEM STATEMENT:
${brief.problem_statement}

IMPACT SIGNALS:
- Total Customer Reports: ${brief.impact_signals.total_reviews}
- Negative Sentiment Ratio: ${brief.impact_signals.negative_percentage}
- Dominant Agitation Emotion: ${brief.impact_signals.dominant_emotion}
- Severity Level: ${brief.impact_signals.severity_level} (Score: ${brief.impact_signals.severity_score})
- Severity Rationale: ${brief.impact_signals.severity_rationale}

TEMPORAL TRAJECTORY:
- Trend: ${brief.temporal_trajectory.trend} (${brief.temporal_trajectory.trend_direction})
- Explanation: ${brief.temporal_trajectory.explanation}

VOICE OF CUSTOMER (AUTHENTIC EVIDENCE):
${brief.customer_statements.map(s => `"${s.quote}" — ${s.metadata}`).join('\n')}

INVESTIGATION AREAS:
${brief.investigation_areas.map((a, i) => `${i + 1}. ${a}`).join('\n')}

RECOMMENDED ACTIONS:
${brief.recommended_actions.map((a, i) => `${i + 1}. ${a}`).join('\n')}
=========================================
Generated via Review Intelligence AI MVP
    `.trim();

    navigator.clipboard.writeText(textContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center space-y-4">
        <Loader2 className="w-8 h-8 animate-spin mx-auto text-indigo-400" />
        <p className="text-sm text-slate-400">Synthesizing executive PM brief from structured evidence...</p>
      </div>
    );
  }

  if (error || !brief) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 space-y-4 text-center">
        <p className="text-red-400">Failed to load PM Brief: {error}</p>
        <button onClick={onBack} className="text-xs text-indigo-400 underline">Return</button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      
      {/* Top action bar */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <button
          onClick={onBack}
          className="inline-flex items-center space-x-2 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Issue Analysis</span>
        </button>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleCopy}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition-all"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied Brief' : 'Copy Text'}</span>
          </button>
          <button
            onClick={() => window.print()}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition-all"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print</span>
          </button>
        </div>
      </div>

      {/* Brief Document Container */}
      <article className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-10 space-y-8 shadow-xl">
        
        {/* Document Header */}
        <div className="border-b border-slate-800 pb-6 space-y-3">
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 text-[11px] font-semibold tracking-wide uppercase border border-indigo-500/30">
              Product Intelligence Brief
            </span>
            {brief.is_emerging && (
              <span className="px-2.5 py-0.5 rounded-full bg-rose-500/20 text-rose-300 text-[11px] font-bold tracking-wide uppercase border border-rose-500/30">
                🚨 Emerging Spike Alert
              </span>
            )}
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-100 tracking-tight">
            {brief.title}
          </h1>

          <p className="text-xs text-slate-400">
            Synthesized deterministically from verified customer evidence. Distinguishes raw customer data from engineering recommendations.
          </p>
        </div>

        {/* Section 1: Executive Summary */}
        <section className="space-y-3">
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>1. Executive Summary &amp; Problem Statement</span>
          </h2>
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
            <p className="text-sm font-semibold text-slate-200 leading-relaxed">
              {brief.summary}
            </p>
            <p className="text-xs text-slate-400 leading-relaxed">
              {brief.problem_statement}
            </p>
          </div>
        </section>

        {/* Section 2: Impact Signals */}
        <section className="space-y-3">
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
            <ShieldAlert className="w-3.5 h-3.5 text-orange-400" />
            <span>2. Measurable Impact Signals</span>
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 text-xs">
              <span className="text-slate-500 block">Total Reports</span>
              <span className="text-base font-bold text-slate-200">{brief.impact_signals.total_reviews} reviews</span>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 text-xs">
              <span className="text-slate-500 block">Dissatisfaction</span>
              <span className="text-base font-bold text-rose-400">{brief.impact_signals.negative_percentage}</span>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 text-xs">
              <span className="text-slate-500 block">Severity Level</span>
              <span className="text-base font-bold text-orange-400">{brief.impact_signals.severity_level}</span>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 text-xs">
              <span className="text-slate-500 block">Temporal Trend</span>
              <span className="text-base font-bold text-sky-400">{brief.temporal_trajectory.trend}</span>
            </div>
          </div>
        </section>

        {/* Section 3: Voice of Customer */}
        <section className="space-y-3">
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            3. Voice of Customer — Supporting Evidence Quotes
          </h2>
          <div className="space-y-2.5">
            {brief.customer_statements.map((item, idx) => (
              <div key={idx} className="p-3.5 rounded-xl bg-slate-950/50 border border-slate-800/80 space-y-1.5">
                <blockquote className="text-xs text-slate-200 italic leading-relaxed">
                  "{item.quote}"
                </blockquote>
                <div className="text-[11px] text-slate-500 flex items-center justify-between">
                  <span>{item.metadata}</span>
                  <span className="capitalize text-indigo-400/80 font-medium">Emotion: {item.emotion}</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Section 4: Potential Investigation Areas */}
        <section className="space-y-3">
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
            <Terminal className="w-3.5 h-3.5 text-sky-400" />
            <span>4. Engineering Investigation Hypotheses</span>
          </h2>
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
            {brief.investigation_areas.map((area, idx) => (
              <div key={idx} className="flex items-start space-x-2 text-xs text-slate-300">
                <span className="font-mono text-sky-400 font-bold shrink-0">{idx + 1}.</span>
                <span>{area}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Section 5: Recommended Action Items */}
        <section className="space-y-3">
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
            <AlertCircle className="w-3.5 h-3.5 text-emerald-400" />
            <span>5. Recommended PM Actions</span>
          </h2>
          <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/30 space-y-2">
            {brief.recommended_actions.map((act, idx) => (
              <div key={idx} className="flex items-start space-x-2 text-xs text-emerald-200">
                <span className="font-mono text-emerald-400 font-bold shrink-0">✓</span>
                <span>{act}</span>
              </div>
            ))}
          </div>
        </section>

      </article>

    </div>
  );
}
