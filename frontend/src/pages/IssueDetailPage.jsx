import React, { useState, useEffect } from 'react';
import {
  ArrowLeft, FileText, TrendingUp, AlertTriangle, ShieldAlert,
  ThumbsDown, Sparkles, Star, Calendar, Smartphone, Loader2, CheckCircle2,
  Brain, Activity, ThumbsUp, HelpCircle
} from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';
import { api } from '../services/api';

export default function IssueDetailPage({ issueId, onBack, onOpenBrief }) {
  const [issue, setIssue] = useState(null);
  const [evidenceData, setEvidenceData] = useState(null);
  const [intelligence, setIntelligence] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [feedbackStatus, setFeedbackStatus] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [issueDetail, evidence, intel] = await Promise.all([
          api.getIssue(issueId),
          api.getIssueEvidence(issueId, 25),
          api.getIssueIntelligence(issueId),
        ]);
        setIssue(issueDetail);
        setEvidenceData(evidence);
        setIntelligence(intel);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [issueId]);

  const handleRLFeedback = async (reward) => {
    if (!intelligence?.rl_recommendation?.action) return;
    try {
      setFeedbackStatus('loading');
      await api.submitRLFeedback(
        issueId,
        issue.dataset_id,
        intelligence.rl_recommendation.action,
        reward
      );
      setFeedbackStatus('success');
      setTimeout(() => setFeedbackStatus(null), 3000);
    } catch (err) {
      console.error(err);
      setFeedbackStatus('error');
    }
  };

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-20 text-center space-y-4">
        <Loader2 className="w-8 h-8 animate-spin mx-auto text-indigo-400" />
        <p className="text-sm text-slate-400">Retrieving issue diagnostics, AI intelligence, and supporting evidence...</p>
      </div>
    );
  }

  if (error || !issue) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 space-y-4 text-center">
        <p className="text-red-400">Failed to load issue details: {error}</p>
        <button onClick={onBack} className="text-xs text-indigo-400 underline">Return to Dashboard</button>
      </div>
    );
  }

  const rationale = evidenceData?.detection_rationale || {};
  const evidenceReviews = evidenceData?.evidence_reviews || [];

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Top Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <button
          onClick={onBack}
          className="inline-flex items-center space-x-2 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </button>

        <button
          onClick={() => onOpenBrief(issue.id)}
          className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-sky-500 hover:from-indigo-500 hover:to-sky-400 text-white font-semibold text-xs transition-all shadow-md shadow-indigo-500/20"
        >
          <FileText className="w-3.5 h-3.5" />
          <span>Generate Executive PM Brief</span>
        </button>
      </div>

      {/* Issue Header Card */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-5">
        <div className="flex flex-wrap items-center gap-2">
          {issue.is_emerging && (
            <span className="text-xs font-bold px-2.5 py-1 rounded-md bg-rose-500/20 text-rose-300 border border-rose-500/40">
              🚨 EMERGING RADAR SPIKE
            </span>
          )}
          <span className={`text-xs font-bold px-2.5 py-1 rounded-md border ${
            issue.severity === 'CRITICAL' ? 'bg-red-500/20 text-red-300 border-red-500/30' :
            issue.severity === 'HIGH' ? 'bg-orange-500/20 text-orange-300 border-orange-500/30' :
            'bg-amber-500/20 text-amber-300 border-amber-500/30'
          }`}>
            {issue.severity} SEVERITY (Score: {issue.severity_score})
          </span>
          <span className="text-xs font-medium px-2.5 py-1 rounded-md bg-slate-800 text-slate-300">
            Trend: {issue.trend}
          </span>
        </div>

        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-100 tracking-tight">
            {issue.theme}
          </h1>
          <p className="text-sm text-slate-400 mt-2">
            {issue.severity_reason}
          </p>
        </div>

        {/* Metric Badges */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
          <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 text-xs">
            <span className="text-slate-500 block">Related Reviews</span>
            <span className="text-base font-bold text-slate-200">{issue.review_count}</span>
          </div>
          <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 text-xs">
            <span className="text-slate-500 block">Negative Ratio</span>
            <span className="text-base font-bold text-rose-400">{issue.negative_percentage}%</span>
          </div>
          <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 text-xs">
            <span className="text-slate-500 block">Dominant Emotion</span>
            <span className="text-base font-bold text-indigo-300 capitalize">{issue.dominant_emotion}</span>
          </div>
          <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 text-xs">
            <span className="text-slate-500 block">Trajectory</span>
            <span className="text-base font-bold text-sky-400 capitalize">{issue.trend_direction}</span>
          </div>
        </div>
      </div>

      {/* Intelligence Layer (RL + LLM) */}
      {intelligence && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* LLM Reasoning */}
          <div className="lg:col-span-2 bg-indigo-950/20 border border-indigo-500/30 rounded-2xl p-6 space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-indigo-500/20">
              <div className="flex items-center space-x-2 text-indigo-300 font-bold text-lg">
                <Brain className="w-5 h-5 text-indigo-400" />
                <h2>AI Executive Summary</h2>
              </div>
              <span className="text-[10px] uppercase tracking-wider text-indigo-400/70 border border-indigo-500/30 px-2 py-1 rounded bg-indigo-500/10">
                Generated by {intelligence.llm_model}
              </span>
            </div>

            <div className="space-y-4 text-sm text-slate-300">
              <p className="leading-relaxed">{intelligence.executive_summary}</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                  <span className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Root Cause Hypothesis</span>
                  <p className="text-indigo-200 font-medium">{intelligence.root_cause_hypothesis}</p>
                </div>
                <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                  <span className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Why This Matters</span>
                  <p className="text-amber-200/90 font-medium">{intelligence.why_it_matters}</p>
                </div>
              </div>

              {intelligence.key_insights && intelligence.key_insights.length > 0 && (
                <div className="pt-2">
                  <span className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Key Data Insights</span>
                  <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {intelligence.key_insights.map((insight, idx) => (
                      <li key={idx} className="flex items-start space-x-2 text-xs">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                        <span className="text-slate-400">{insight}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          {/* RL Recommendation */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-6 flex flex-col">
            <div className="flex items-center space-x-2 text-violet-300 font-bold text-lg pb-4 border-b border-slate-800">
              <Activity className="w-5 h-5 text-violet-400" />
              <h2>RL Agent Strategy</h2>
            </div>
            
            <div className="flex-1 space-y-4">
              <div className="text-center p-4 bg-violet-500/10 border border-violet-500/20 rounded-xl">
                <span className="block text-[10px] font-bold text-violet-400 uppercase tracking-wider mb-1">Recommended Action</span>
                <span className="block text-lg font-extrabold text-violet-200">{intelligence.rl_recommendation.label}</span>
                <span className="text-xs text-violet-300/70 mt-1 block">Confidence: {(intelligence.rl_recommendation.confidence * 100).toFixed(0)}%</span>
              </div>
              
              <p className="text-xs text-slate-400 leading-relaxed text-center">
                {intelligence.rl_recommendation.description}
              </p>

              {/* Action specific scores */}
              <div className="space-y-2 mt-4 pt-4 border-t border-slate-800">
                <span className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2">Q-Value Transparency</span>
                {intelligence.rl_recommendation.all_scores.slice(0, 3).map((score, i) => (
                  <div key={score.action} className="flex items-center justify-between text-xs">
                    <span className="text-slate-400 truncate pr-2">{score.label}</span>
                    <span className="text-slate-500 font-mono">{score.score.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* RL Feedback mechanism */}
            <div className="pt-4 border-t border-slate-800">
              <span className="block text-xs text-center text-slate-400 mb-2">Is this recommendation helpful?</span>
              <div className="flex justify-center gap-2">
                <button
                  onClick={() => handleRLFeedback(1.0)}
                  disabled={feedbackStatus !== null}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 text-xs font-medium rounded-lg border border-emerald-500/20 transition-colors disabled:opacity-50"
                >
                  <ThumbsUp className="w-3.5 h-3.5" />
                  Yes
                </button>
                <button
                  onClick={() => handleRLFeedback(-1.0)}
                  disabled={feedbackStatus !== null}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 text-xs font-medium rounded-lg border border-rose-500/20 transition-colors disabled:opacity-50"
                >
                  <ThumbsDown className="w-3.5 h-3.5" />
                  No
                </button>
              </div>
              {feedbackStatus === 'success' && <p className="text-[10px] text-emerald-400 text-center mt-2">Agent policy updated!</p>}
              {feedbackStatus === 'error' && <p className="text-[10px] text-rose-400 text-center mt-2">Failed to submit feedback.</p>}
            </div>
          </div>
        </div>
      )}

      {/* ML Pipeline Fallback (Only if Intelligence API fails or doesn't return full insights) */}
      {!intelligence && (
        <div className="bg-indigo-950/20 border border-indigo-500/30 rounded-2xl p-6 space-y-4">
          <div className="flex items-center space-x-2 text-indigo-300 font-bold text-base">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            <h2>Why This Issue Was Detected (ML Pipeline)</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="space-y-1 p-3 bg-slate-900/60 rounded-xl border border-slate-800">
              <span className="font-semibold text-slate-300 block">Volume &amp; Semantic Cluster</span>
              <p className="text-slate-400">{rationale.review_volume || `${issue.review_count} customer reports cluster together.`}</p>
            </div>
            <div className="space-y-1 p-3 bg-slate-900/60 rounded-xl border border-slate-800">
              <span className="font-semibold text-slate-300 block">Sentiment &amp; Dissatisfaction</span>
              <p className="text-slate-400">{rationale.sentiment_signal || `${issue.negative_percentage}% expressed negative sentiment.`}</p>
            </div>
            <div className="space-y-1 p-3 bg-slate-900/60 rounded-xl border border-slate-800">
              <span className="font-semibold text-slate-300 block">Customer Emotional Agitation</span>
              <p className="text-slate-400">{rationale.emotional_resonance || `Dominant emotion is ${issue.dominant_emotion}.`}</p>
            </div>
            <div className="space-y-1 p-3 bg-slate-900/60 rounded-xl border border-slate-800">
              <span className="font-semibold text-slate-300 block">Severity &amp; Risk Rationale</span>
              <p className="text-slate-400">{rationale.severity_level || issue.severity_reason}</p>
            </div>
          </div>
        </div>
      )}

      {/* Timeline Chart if available */}
      {issue.timeline && issue.timeline.length > 1 && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-3">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            Issue Occurrence Frequency Over Time
          </h3>
          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={issue.timeline} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <defs>
                  <linearGradient id="issueColor" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#818cf8" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#818cf8" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 10 }} />
                <YAxis tick={{ fill: '#64748b', fontSize: 10 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }} />
                <Area type="monotone" dataKey="count" stroke="#818cf8" strokeWidth={2} fillOpacity={1} fill="url(#issueColor)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Supporting Evidence Chain */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              Customer Evidence Chain
              {intelligence?.evidence_review_ids && (
                <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Grounded
                </span>
              )}
            </h2>
            <p className="text-xs text-slate-400">
              Showing top reviews ranked by relevance. Highlighted reviews were used directly by the LLM reasoning layer.
            </p>
          </div>
        </div>

        <div className="space-y-3">
          {evidenceReviews.map((rev, idx) => {
            const isLLMReferenced = intelligence?.evidence_review_ids?.includes(rev.id || rev.review_id);
            return (
              <div
                key={rev.id || idx}
                className={`border rounded-xl p-4 sm:p-5 space-y-3 transition-colors ${
                  isLLMReferenced
                    ? 'bg-indigo-950/20 border-indigo-500/40 shadow-[0_0_15px_rgba(99,102,241,0.05)]'
                    : 'bg-slate-900/70 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-indigo-400 font-semibold">{rev.original_id || `REV-${idx+1}`}</span>
                    {isLLMReferenced && (
                      <span className="flex items-center gap-1 text-[10px] font-bold text-indigo-300 bg-indigo-500/10 px-1.5 py-0.5 rounded">
                        <Brain className="w-3 h-3" /> AI Context
                      </span>
                    )}
                    {rev.rating && (
                      <span className="flex items-center text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20 font-semibold">
                        <Star className="w-3 h-3 fill-current mr-1" />
                        {rev.rating}
                      </span>
                    )}
                    {rev.date && (
                      <span className="text-slate-500 flex items-center">
                        <Calendar className="w-3 h-3 mr-1" />
                        {rev.date}
                      </span>
                    )}
                    {rev.platform && (
                      <span className="text-slate-500 flex items-center">
                        <Smartphone className="w-3 h-3 mr-1" />
                        {rev.platform} {rev.app_version ? `v${rev.app_version}` : ''}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-0.5 rounded font-semibold text-[11px] ${
                      rev.sentiment === 'POSITIVE' ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                    }`}>
                      {rev.sentiment} ({Math.round((rev.sentiment_score || 0.9) * 100)}%)
                    </span>
                    {rev.emotion && (
                      <span className="px-2 py-0.5 rounded bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 capitalize text-[11px]">
                        {rev.emotion}
                      </span>
                    )}
                  </div>
                </div>

                <blockquote className={`text-sm border-l-2 pl-3 italic ${
                  isLLMReferenced ? 'text-slate-100 border-indigo-400' : 'text-slate-300 border-slate-700'
                }`}>
                  "{rev.text}"
                </blockquote>
              </div>
            );
          })}
        </div>
      </div>

    </div>
  );
}
