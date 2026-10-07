import React, { useState } from 'react';
import {
  AlertTriangle, Flame, TrendingUp, ThumbsUp, ThumbsDown, MessageSquare,
  ArrowRight, ShieldAlert, Sparkles, ChevronRight, BarChart2, Star,
  Zap, Upload, Eye, Filter
} from 'lucide-react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip,
  Cell, AreaChart, Area, PieChart, Pie, LineChart, Line, Legend
} from 'recharts';

// ─── Sentiment donut mock (if no real data) ──────────────────────────────────
function SentimentDonut({ positive = 62.4, neutral = 18.7, negative = 18.9, total }) {
  const COLORS = { positive: '#22c55e', neutral: '#f59e0b', negative: '#f43f5e' };
  const data = [
    { name: 'Positive', value: positive, color: COLORS.positive },
    { name: 'Neutral', value: neutral, color: COLORS.neutral },
    { name: 'Negative', value: negative, color: COLORS.negative },
  ];

  return (
    <div className="flex items-center gap-6">
      <div className="relative w-32 h-32 flex-shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={40}
              outerRadius={58}
              dataKey="value"
              strokeWidth={0}
            >
              {data.map((entry) => (
                <Cell key={entry.name} fill={entry.color} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-lg font-extrabold text-slate-700">{total?.toLocaleString?.() ?? '10K'}</span>
          <span className="text-[9px] text-slate-400 leading-tight text-center">Total{'\n'}Reviews</span>
        </div>
      </div>
      <div className="space-y-2 flex-1">
        {data.map((d) => (
          <div key={d.name} className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: d.color }} />
            <span className="text-xs text-slate-600 w-16">{d.name}</span>
            <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
              <div className="h-full rounded-full" style={{ width: `${d.value}%`, background: d.color }} />
            </div>
            <span className="text-xs font-bold text-slate-700 w-10 text-right">{d.value}%</span>
            <span className="text-[10px] text-slate-400 w-12 text-right">
              {total ? Math.round((d.value / 100) * total).toLocaleString() : '—'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Top Issues list item ─────────────────────────────────────────────────────
function TopIssueRow({ rank, icon, label, percentage, negPct, color, onClick }) {
  return (
    <div className="flex items-center gap-3 py-2 cursor-pointer group" onClick={onClick}>
      <span className="text-xs font-bold text-slate-400 w-4">{rank}</span>
      <div
        className="w-7 h-7 rounded-lg flex items-center justify-center text-white text-xs flex-shrink-0"
        style={{ background: color }}
      >
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-xs font-semibold text-slate-700 group-hover:text-indigo-600 transition-colors truncate">{label}</div>
        <div className="mt-1 h-1 bg-slate-100 rounded-full overflow-hidden w-full">
          <div className="h-full rounded-full" style={{ width: `${percentage}%`, background: color }} />
        </div>
      </div>
      <span className="text-xs font-bold text-slate-600 w-8 text-right">{percentage}%</span>
      <span className="text-[10px] text-rose-500 font-medium w-16 text-right">{negPct}% neg</span>
    </div>
  );
}

export default function DashboardPage({ data, onSelectIssue, onOpenUpload, onOpenBrief }) {
  const [selectedSeverity, setSelectedSeverity] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [reviewFilter, setReviewFilter] = useState('All');
  const [dashboardIntel, setDashboardIntel] = useState(null);
  const [loadingIntel, setLoadingIntel] = useState(false);

  const hasData = data && data.total_reviews > 0;

  React.useEffect(() => {
    async function loadIntel() {
      if (hasData && data.dataset_id) {
        try {
          setLoadingIntel(true);
          const intel = await api.getDashboardIntelligence(data.dataset_id);
          setDashboardIntel(intel);
        } catch (err) {
          console.error("Failed to load dashboard intelligence", err);
        } finally {
          setLoadingIntel(false);
        }
      }
    }
    loadIntel();
  }, [hasData, data?.dataset_id]);

  // ── Empty state ────────────────────────────────────────────────────────────
  if (!hasData) {
    return (
      <div className="flex-1 bg-[#f0f2f8] p-8">
        <div className="max-w-2xl mx-auto text-center space-y-6 pt-20">
          <div className="w-16 h-16 rounded-2xl bg-indigo-100 border border-indigo-200 flex items-center justify-center mx-auto text-indigo-500">
            <MessageSquare className="w-8 h-8" />
          </div>
          <h2 className="text-2xl font-bold text-slate-700">No Review Intelligence Data Yet</h2>
          <p className="text-slate-500 max-w-md mx-auto text-sm">
            Upload a CSV or load our pre-configured demo dataset to view automated sentiment, emotion clusters, and emerging issues.
          </p>
          <button
            onClick={onOpenUpload}
            className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold text-sm transition-all shadow-lg shadow-indigo-500/25"
          >
            Upload & Run Analysis
          </button>
        </div>
      </div>
    );
  }

  // ── Filter issues ──────────────────────────────────────────────────────────
  const filteredIssues = (data.top_issues || []).filter((issue) => {
    const matchesSev = selectedSeverity === 'ALL' || issue.severity === selectedSeverity;
    const matchesSearch = !searchQuery || issue.theme.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSev && matchesSearch;
  });

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'CRITICAL': return 'text-rose-600 bg-rose-50 border-rose-200';
      case 'HIGH': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'MEDIUM': return 'text-amber-600 bg-amber-50 border-amber-200';
      default: return 'text-blue-600 bg-blue-50 border-blue-200';
    }
  };

  // Extract top issues from actual data for the right panel
  const topIssuesPanel = (data.top_issues || []).slice(0, 5).map((issue, idx) => ({
    id: issue.id,
    rank: idx + 1,
    icon: idx === 0 ? '🔐' : idx === 1 ? '💳' : idx === 2 ? '⚡' : idx === 3 ? '🐛' : '🎨', // Fallback icons
    label: issue.theme,
    percentage: Math.round((issue.review_count / Math.max(1, data.total_reviews)) * 100),
    negPct: Math.round(issue.negative_percentage),
    color: issue.severity === 'CRITICAL' ? '#f43f5e' : issue.severity === 'HIGH' ? '#f59e0b' : '#6366f1',
  }));

  // Sentiment trend mock data
  const sentimentTrendData = [
    { date: 'Apr 10', positive: 65, neutral: 20, negative: 15 },
    { date: 'Apr 17', positive: 60, neutral: 22, negative: 18 },
    { date: 'Apr 24', positive: 63, neutral: 19, negative: 18 },
    { date: 'May 1', positive: 62, neutral: 18, negative: 20 },
    { date: 'May 8', positive: 64, neutral: 18, negative: 18 },
  ];

  // Recent reviews mock
  const recentReviews = [
    { id: 1, issue: 'Login & Authentication', stars: 1, rating: '4621 • 1 Star', text: '"OTP never arrives even after multiple attempts..."', time: '2h ago', sentiment: 'Negative' },
    { id: 2, issue: 'Payment Issues', stars: 3, rating: '43197 • 3 Stars', text: '"Payment failed but money was deducted..."', time: '3h ago', sentiment: 'Neutral' },
    { id: 3, issue: 'App Performance', stars: 5, rating: '6023 • 5 Stars', text: '"Love the new update! The app is so smooth now."', time: '4h ago', sentiment: 'Positive' },
  ];

  const sentimentColor = (s) => {
    if (s === 'Positive') return 'text-emerald-600 bg-emerald-50';
    if (s === 'Negative') return 'text-rose-600 bg-rose-50';
    return 'text-amber-600 bg-amber-50';
  };

  return (
    <div className="flex-1 bg-[#f0f2f8] overflow-auto">
      <div className="flex gap-0">
        {/* ── LEFT+CENTER main content ────────────────────────────────────── */}
        <div className="flex-1 min-w-0 p-5 space-y-4">

          {/* Header greeting */}
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-500 mb-0.5">Good morning, Mohit 👋</p>
              <h1 className="text-2xl font-extrabold text-slate-800 leading-tight">
                Here's what your users are saying.
              </h1>
              <p className="text-sm text-slate-500 mt-1 max-w-lg">
                We analyzed{' '}
                <span className="font-semibold text-slate-700">{data.total_reviews.toLocaleString()} reviews</span>{' '}
                and found key themes, sentiment trends and actionable insights to help you build a better product.
              </p>
            </div>
            {/* AI badge */}
            <div className="hidden lg:flex flex-col items-center justify-center w-24 h-20 relative">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-100 via-violet-100 to-cyan-100 border border-indigo-200/60 flex items-center justify-center animate-float shadow-lg shadow-indigo-200/50">
                <Sparkles className="w-7 h-7 text-indigo-500" />
              </div>
              <span className="text-[9px] text-indigo-400 font-medium mt-1 text-center leading-tight">AI-powered<br/>insights</span>
            </div>
          </div>

          {/* KPI cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {[
              {
                label: 'Total Reviews',
                value: data.total_reviews.toLocaleString(),
                sub: '↑ 1.2% vs. last 30 days',
                subColor: 'text-emerald-600',
                icon: MessageSquare,
                iconColor: 'text-indigo-500',
                sparkColor: '#6366f1',
              },
              {
                label: 'Positive Sentiment',
                value: `${data.positive_percentage}%`,
                sub: '↑ 4.3% vs. last 30 days',
                subColor: 'text-emerald-600',
                icon: ThumbsUp,
                iconColor: 'text-emerald-500',
                sparkColor: '#22c55e',
              },
              {
                label: 'Negative Sentiment',
                value: `${data.negative_percentage}%`,
                sub: '↑ 2.1% vs. last 30 days',
                subColor: 'text-rose-500',
                icon: ThumbsDown,
                iconColor: 'text-rose-500',
                sparkColor: '#f43f5e',
              },
              {
                label: 'Neutral Sentiment',
                value: `${(100 - data.positive_percentage - data.negative_percentage).toFixed(1)}%`,
                sub: '↓ 1.2% vs. last 36 days',
                subColor: 'text-slate-400',
                icon: MessageSquare,
                iconColor: 'text-amber-500',
                sparkColor: '#f59e0b',
              },
            ].map((kpi) => (
              <div key={kpi.label} className="bg-white border border-slate-200/80 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-slate-400 font-medium">{kpi.label}</span>
                  <kpi.icon className={`w-4 h-4 ${kpi.iconColor}`} />
                </div>
                <div className="text-2xl font-extrabold text-slate-800 mb-1">{kpi.value}</div>
                <div className={`text-[11px] font-medium ${kpi.subColor}`}>{kpi.sub}</div>
                {/* Mini sparkline */}
                <div className="mt-2 h-6">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={sentimentTrendData}>
                      <Line type="monotone" dataKey="positive" stroke={kpi.sparkColor} strokeWidth={1.5} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            ))}
          </div>

          {/* Sentiment Overview + Trend */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Sentiment Overview */}
            <div className="bg-white border border-slate-200/80 rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-slate-700">Sentiment Overview</h3>
                <span className="text-xs border border-slate-200 rounded-md px-2 py-0.5 text-slate-400 flex items-center gap-1">
                  Sentiment Distribution <ChevronRight className="w-3 h-3" />
                </span>
              </div>
              <SentimentDonut
                positive={data.positive_percentage}
                negative={data.negative_percentage}
                neutral={100 - data.positive_percentage - data.negative_percentage}
                total={data.total_reviews}
              />
            </div>

            {/* Sentiment Trend */}
            <div className="bg-white border border-slate-200/80 rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-slate-700">Sentiment Trend</h3>
                <div className="flex items-center gap-3 text-[10px] text-slate-400">
                  <span className="flex items-center gap-1"><span className="w-2 h-0.5 bg-emerald-500 inline-block rounded" />Positive</span>
                  <span className="flex items-center gap-1"><span className="w-2 h-0.5 bg-amber-400 inline-block rounded" />Neutral</span>
                  <span className="flex items-center gap-1"><span className="w-2 h-0.5 bg-rose-500 inline-block rounded" />Negative</span>
                </div>
              </div>
              <div className="h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={sentimentTrendData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                    <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#94a3b8' }} />
                    <YAxis tick={{ fontSize: 9, fill: '#94a3b8' }} domain={[0, 100]} tickFormatter={v => `${v}%`} />
                    <Tooltip
                      contentStyle={{ fontSize: '11px', borderRadius: '8px', border: '1px solid #e2e8f0', background: '#fff' }}
                      formatter={(val) => [`${val}%`]}
                    />
                    <Line type="monotone" dataKey="positive" stroke="#22c55e" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="neutral" stroke="#f59e0b" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="negative" stroke="#f43f5e" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* What Are Users Saying — Themes + Bubble + Recent Reviews */}
          <div>
            <h2 className="text-base font-bold text-slate-700 mb-3">What Are Users Saying?</h2>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

              {/* Top Themes */}
              <div className="bg-white border border-slate-200/80 rounded-xl p-5 shadow-sm">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-xs font-bold text-slate-600 uppercase tracking-wider">Top Themes</h3>
                  <button className="text-[10px] text-indigo-500 hover:text-indigo-700 font-medium">View All</button>
                </div>
                <div className="space-y-3">
                  {topIssuesPanel.map((issue) => (
                    <TopIssueRow
                      key={issue.rank}
                      {...issue}
                      onClick={() => filteredIssues[issue.rank - 1] && onSelectIssue(filteredIssues[issue.rank - 1].id)}
                    />
                  ))}
                </div>
              </div>

              {/* Theme Breakdown bubble chart (simplified) */}
              <div className="bg-white border border-slate-200/80 rounded-xl p-5 shadow-sm flex flex-col">
                <h3 className="text-xs font-bold text-slate-600 uppercase tracking-wider mb-3">Theme Breakdown</h3>
                <div className="flex-1 flex items-center justify-center">
                  <div className="relative w-48 h-48">
                    {/* Central Login bubble */}
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-20 h-20 rounded-full bg-indigo-100 border-2 border-indigo-300 flex flex-col items-center justify-center shadow-sm">
                      <span className="text-xs font-extrabold text-indigo-700">Login</span>
                      <span className="text-[10px] text-indigo-500 font-bold">24%</span>
                    </div>
                    {/* Surrounding bubbles */}
                    {[
                      { label: 'Perf', pct: '15%', color: 'bg-violet-100 border-violet-300 text-violet-700', pos: 'top-0 right-3' },
                      { label: 'Bugs', pct: '12%', color: 'bg-amber-100 border-amber-300 text-amber-700', pos: 'bottom-2 left-4' },
                      { label: 'UI/UX', pct: '9%', color: 'bg-pink-100 border-pink-300 text-pink-700', pos: 'bottom-2 right-4' },
                      { label: 'Others', pct: '22%', color: 'bg-slate-100 border-slate-300 text-slate-600', pos: 'top-6 left-0' },
                    ].map((b) => (
                      <div key={b.label} className={`absolute ${b.pos} w-13 h-13 rounded-full border-2 ${b.color} flex flex-col items-center justify-center`} style={{ width: '52px', height: '52px' }}>
                        <span className="text-[10px] font-bold">{b.label}</span>
                        <span className="text-[9px] font-semibold">{b.pct}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <p className="text-[9px] text-indigo-400 text-center mt-2">Click on any theme to explore real reviews →</p>
              </div>

              {/* Recent Reviews */}
              <div className="bg-white border border-slate-200/80 rounded-xl p-5 shadow-sm">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-xs font-bold text-slate-600 uppercase tracking-wider">Recent Reviews</h3>
                  <button className="text-[10px] text-indigo-500 hover:text-indigo-700 font-medium">View All</button>
                </div>
                {/* Filter tabs */}
                <div className="flex gap-1 mb-3">
                  {['All', 'Positive', 'Neutral', 'Negative'].map((f) => (
                    <button
                      key={f}
                      onClick={() => setReviewFilter(f)}
                      className={`text-[9px] px-2 py-0.5 rounded-full font-medium transition-all ${
                        reviewFilter === f ? 'bg-slate-700 text-white' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
                      }`}
                    >
                      {f}
                    </button>
                  ))}
                </div>
                <div className="space-y-3">
                  {recentReviews
                    .filter(r => reviewFilter === 'All' || r.sentiment === reviewFilter)
                    .map((r) => (
                    <div key={r.id} className="border-b border-slate-100 pb-3 last:border-0 last:pb-0">
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <div>
                          <span className="text-[10px] font-semibold text-slate-700 block">{r.stars}★ · {r.issue}</span>
                          <span className="text-[9px] text-slate-400">{r.rating}</span>
                        </div>
                        <div className="flex items-center gap-1 flex-shrink-0">
                          <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-medium ${sentimentColor(r.sentiment)}`}>{r.sentiment}</span>
                          <span className="text-[9px] text-slate-400">{r.time}</span>
                        </div>
                      </div>
                      <p className="text-[10px] text-slate-500 italic">{r.text}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Pipeline footer */}
          <div className="bg-white border border-slate-200/80 rounded-xl p-4 shadow-sm">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-center">
              {[
                { icon: '☁️', step: 'Upload', desc: 'Your review dataset (CSV, XLSX, JSON)' },
                { icon: '🧠', step: 'Analyze', desc: 'AI processes & detects themes and sentiment' },
                { icon: '📊', step: 'Understand', desc: 'Get insights, trends and Visualisations' },
                { icon: '✅', step: 'Verify', desc: 'Validate accuracy & check for drift' },
                { icon: '🚀', step: 'Act', desc: 'Make data-driven product decisions' },
              ].map((s) => (
                <div key={s.step} className="flex flex-col items-center gap-1">
                  <span className="text-xl">{s.icon}</span>
                  <span className="text-xs font-bold text-slate-700">{s.step}</span>
                  <span className="text-[9px] text-slate-400 leading-tight">{s.desc}</span>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* ── RIGHT panel (AI insights + top issues + activity) ───────────── */}
        <div className="hidden xl:flex flex-col w-72 border-l border-slate-200/80 bg-white/60 p-4 space-y-4 min-h-screen flex-shrink-0">

          {/* Generate Executive Report */}
          <div className="bg-gradient-to-br from-indigo-50 to-violet-50 border border-indigo-200/60 rounded-xl p-4">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center flex-shrink-0">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <div className="flex-1">
                <h4 className="text-xs font-bold text-slate-700">Generate Executive Report</h4>
                <p className="text-[10px] text-slate-500 mt-0.5">Get a detailed summary with key insights, trends and recommendations.</p>
              </div>
              <button
                onClick={() => onOpenBrief && onOpenBrief(null)}
                className="w-6 h-6 rounded-full bg-indigo-600 hover:bg-indigo-500 flex items-center justify-center flex-shrink-0 transition-colors cursor-pointer"
                title="Generate Executive PM Brief"
              >
                <ArrowRight className="w-3 h-3 text-white" />
              </button>
            </div>
          </div>

          {/* AI Insights */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
                AI Insights
              </h3>
              <button className="text-[10px] text-indigo-500 font-medium">View All</button>
            </div>
            
            {loadingIntel ? (
              <div className="bg-white border border-slate-200/80 rounded-xl p-5 shadow-sm text-center">
                <span className="text-xs text-slate-400">Loading intelligence...</span>
              </div>
            ) : dashboardIntel && dashboardIntel.insights?.length > 0 ? (
              <div className="space-y-3">
                {dashboardIntel.insights.slice(0, 2).map(insight => (
                  <div key={insight.issue_id} className="bg-white border border-slate-200/80 rounded-xl p-3 shadow-sm space-y-2 relative overflow-hidden group cursor-pointer" onClick={() => onSelectIssue(insight.issue_id)}>
                    <div className="absolute top-0 right-0 w-16 h-16 bg-gradient-to-br from-indigo-500/5 to-violet-500/5 rounded-bl-full pointer-events-none" />
                    
                    <div className="flex items-center justify-between">
                      <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${insight.severity === 'CRITICAL' ? 'text-rose-500 bg-rose-50 border border-rose-200' : 'text-orange-500 bg-orange-50 border border-orange-200'}`}>
                        {insight.severity} Priority
                      </span>
                      {insight.is_emerging && (
                        <span className="text-[9px] font-bold text-rose-500 flex items-center gap-1">
                          <AlertTriangle className="w-2.5 h-2.5" /> Emerging
                        </span>
                      )}
                    </div>
                    
                    <p className="text-xs font-bold text-slate-700 leading-tight">
                      {insight.executive_summary?.split('.')[0] || insight.theme}
                    </p>
                    
                    <div className="bg-slate-50 p-2 rounded-lg border border-slate-100">
                      <span className="text-[9px] font-bold text-slate-500 block mb-0.5">RL Strategy:</span>
                      <span className="text-[10px] font-bold text-indigo-600">{insight.rl_action}</span>
                    </div>
                    
                    <div className="flex items-center justify-between pt-1 border-t border-slate-100">
                      <span className="text-[9px] text-slate-400">Impact Score <span className="font-bold text-slate-600">{(insight.priority_score * 100).toFixed(0)}</span></span>
                      <button className="text-[9px] bg-indigo-600 text-white px-2 py-0.5 rounded-md font-medium group-hover:bg-indigo-700 transition-colors flex items-center gap-1">
                        View <ArrowRight className="w-2.5 h-2.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-white border border-slate-200/80 rounded-xl p-5 shadow-sm text-center">
                <span className="text-xs text-slate-400">Run analysis to generate insights.</span>
              </div>
            )}
          </div>

          {/* Top Issues */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-bold text-slate-700">Top Issues</h3>
              <button className="text-[10px] text-indigo-500 font-medium">View All</button>
            </div>
            <div className="space-y-1">
              {topIssuesPanel.map((issue) => (
                <div
                  key={issue.rank}
                  className="flex items-center gap-2 bg-white border border-slate-100 rounded-lg px-3 py-2 hover:border-indigo-200 transition-all cursor-pointer group"
                  onClick={() => filteredIssues[issue.rank - 1] && onSelectIssue(filteredIssues[issue.rank - 1].id)}
                >
                  <span className="text-xs font-bold text-slate-400 w-3">{issue.rank}</span>
                  <span className="text-sm">{issue.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="text-[10px] font-semibold text-slate-700 truncate group-hover:text-indigo-600 transition-colors">{issue.label}</div>
                    <div className="mt-1 h-1 bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${issue.negPct}%`, background: issue.color }} />
                    </div>
                  </div>
                  <span className="text-[10px] text-rose-500 font-bold">{issue.negPct}%</span>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Activity */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-bold text-slate-700">Recent Activity</h3>
              <button className="text-[10px] text-indigo-500 font-medium">View All</button>
            </div>
            <div className="space-y-2">
              {[
                { icon: '📦', text: 'New batch of 1,000 reviews processed', time: '2 hours ago' },
                { icon: '📉', text: 'Sentiment drift detected (115%)', time: '5 hours ago' },
                { icon: '✅', text: 'PII redaction completed (327 instances)', time: '6 hours ago' },
              ].map((a, i) => (
                <div key={i} className="flex items-start gap-2 bg-white border border-slate-100 rounded-lg px-3 py-2">
                  <span className="text-sm flex-shrink-0">{a.icon}</span>
                  <div>
                    <div className="text-[10px] text-slate-600">{a.text}</div>
                    <div className="text-[9px] text-slate-400">{a.time}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* CTA bottom */}
          <div className="bg-gradient-to-br from-indigo-600 to-violet-600 rounded-xl p-4 text-center mt-auto">
            <h4 className="text-sm font-extrabold text-white mb-0.5">Better insights.</h4>
            <p className="text-xs text-indigo-200">Happier users.</p>
            <button className="mt-3 bg-white/20 hover:bg-white/30 text-white text-[10px] font-semibold rounded-lg px-3 py-1.5 transition-all w-full flex items-center justify-center gap-1">
              <Sparkles className="w-3 h-3" /> Generate Report
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
