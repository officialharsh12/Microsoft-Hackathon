import React, { useState } from 'react';
import { BarChart3, Sparkles, TrendingUp, Shield, ChevronRight, Eye, EyeOff, Loader2, X, CheckCircle2, ArrowRight, Star, Zap, Brain, Rocket, MessageSquare, PieChart, Activity, Fingerprint } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

// Auth Modal Component
function AuthModal({ mode, onClose, onSwitchMode }) {
  const { login, signup } = useAuth();
  const [form, setForm] = useState({ name: '', email: '', password: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      if (mode === 'login') {
        await login(form.email, form.password);
      } else {
        await signup(form.name, form.email, form.password);
      }
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-slate-950/80 backdrop-blur-md"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-md bg-slate-900 border border-slate-700/60 rounded-2xl shadow-2xl shadow-indigo-950/50 overflow-hidden">
        {/* Gradient top bar */}
        <div className="h-1 w-full bg-gradient-to-r from-indigo-500 via-violet-500 to-cyan-400" />

        {/* Header */}
        <div className="flex items-center justify-between p-6 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 via-violet-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <BarChart3 className="w-4 h-4 text-white" />
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-[0.2em] text-indigo-300/80 font-medium">FeedbackPulse</p>
              <h2 className="text-lg font-bold text-slate-100">
                {mode === 'login' ? 'Welcome back' : 'Create account'}
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-all"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-6 pb-6 space-y-4">
          
          {/* Demo Credentials Alert */}
          <div className="bg-indigo-500/10 border border-indigo-500/30 rounded-xl p-3 mb-2 flex items-start gap-2">
            <div className="text-indigo-400 mt-0.5">ℹ️</div>
            <div className="text-xs text-indigo-200">
              <span className="font-bold block mb-1">Demo Credentials:</span>
              <div className="flex justify-between items-center bg-indigo-950/50 p-1.5 rounded border border-indigo-500/20 mb-1">
                <span className="font-mono text-indigo-300">demo@microsoft.com</span>
              </div>
              <div className="flex justify-between items-center bg-indigo-950/50 p-1.5 rounded border border-indigo-500/20">
                <span className="font-mono text-indigo-300">hackathon2026</span>
              </div>
            </div>
          </div>

          {mode === 'signup' && (
            <div>
              <label className="text-xs font-medium text-slate-300 mb-1.5 block">Full Name</label>
              <input
                type="text"
                id="auth-name"
                placeholder="Mohit Lalani"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full bg-slate-950/60 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/30 transition-all"
                required
              />
            </div>
          )}

          <div>
            <label className="text-xs font-medium text-slate-300 mb-1.5 block">Email</label>
            <input
              type="email"
              id="auth-email"
              placeholder="mohit@company.com"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="w-full bg-slate-950/60 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/30 transition-all"
              required
            />
          </div>

          <div>
            <label className="text-xs font-medium text-slate-300 mb-1.5 block">Password</label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                id="auth-password"
                placeholder="Min. 6 characters"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="w-full bg-slate-950/60 border border-slate-700 rounded-xl px-4 py-2.5 pr-10 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/30 transition-all"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 transition-colors"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {error && (
            <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg px-3 py-2 text-xs text-rose-300">
              {error}
            </div>
          )}

          <button
            type="submit"
            id="auth-submit-btn"
            disabled={isLoading}
            className="w-full bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold rounded-xl py-2.5 text-sm flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/25 transition-all disabled:opacity-70 disabled:cursor-not-allowed mt-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>{mode === 'login' ? 'Signing in...' : 'Creating account...'}</span>
              </>
            ) : (
              <>
                <span>{mode === 'login' ? 'Sign In' : 'Get Started Free'}</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>

          {mode === 'login' && (
            <button
              type="button"
              id="auth-autofill-btn"
              onClick={() => {
                setForm({ email: 'demo@microsoft.com', password: 'hackathon2026' });
                setError('');
              }}
              className="w-full bg-slate-800/80 hover:bg-slate-700/80 border border-indigo-500/30 hover:border-indigo-500/60 text-indigo-300 hover:text-indigo-200 font-medium rounded-xl py-2.5 text-xs flex items-center justify-center gap-2 transition-all shadow-sm cursor-pointer"
            >
              <Zap className="w-3.5 h-3.5 text-amber-400" />
              <span>Auto-Fill Demo Credentials</span>
            </button>
          )}

          <p className="text-center text-xs text-slate-400">
            {mode === 'login' ? "Don't have an account? " : "Already have an account? "}
            <button
              type="button"
              id="auth-switch-mode"
              onClick={onSwitchMode}
              className="text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
            >
              {mode === 'login' ? 'Sign up for free' : 'Sign in'}
            </button>
          </p>
        </form>
      </div>
    </div>
  );
}

// Feature card component
function FeatureCard({ icon: Icon, title, description, gradient, delay }) {
  return (
    <div
      className="group relative bg-slate-900/60 border border-slate-800 rounded-2xl p-6 hover:border-indigo-500/40 transition-all duration-300 hover:shadow-xl hover:shadow-indigo-950/30 overflow-hidden animate-fade-in-up"
      style={{ animationDelay: delay }}
    >
      <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />
      <div className="relative">
        <div className="w-11 h-11 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
          <Icon className="w-5 h-5 text-indigo-400" />
        </div>
        <h3 className="text-base font-bold text-slate-100 mb-2">{title}</h3>
        <p className="text-sm text-slate-400 leading-relaxed">{description}</p>
      </div>
    </div>
  );
}

// Stat display
function StatBadge({ value, label }) {
  return (
    <div className="text-center">
      <div className="text-2xl font-extrabold gradient-text">{value}</div>
      <div className="text-xs text-slate-400 mt-0.5">{label}</div>
    </div>
  );
}

export default function LandingPage() {
  const [authMode, setAuthMode] = useState(null); // null | 'login' | 'signup'

  const features = [
    {
      icon: Sparkles,
      title: 'AI-Powered Insights',
      description: 'Azure AI analyzes thousands of reviews in seconds — detecting themes, emotions and sentiment patterns automatically.',
      gradient: 'from-indigo-500/5 to-violet-500/5',
      delay: '0ms',
    },
    {
      icon: Brain,
      title: 'LLM Reasoning',
      description: 'Generates executive summaries, root cause hypotheses, and actionable product recommendations using advanced language models.',
      gradient: 'from-sky-500/5 to-indigo-500/5',
      delay: '100ms',
    },
    {
      icon: Activity,
      title: 'RL Recommendations',
      description: 'A reinforcement learning agent learns to prioritize issues over time based on feedback, automatically suggesting actions like "Prioritize", "Investigate", or "Monitor".',
      gradient: 'from-violet-500/5 to-pink-500/5',
      delay: '200ms',
    },
    {
      icon: Fingerprint,
      title: 'Evidence Traceability',
      description: 'Every LLM-generated insight is strictly traceable to the underlying review and theme evidence, ensuring no hallucinations.',
      gradient: 'from-cyan-500/5 to-sky-500/5',
      delay: '300ms',
    },
  ];

  return (
    <div className="min-h-screen bg-slate-950 relative overflow-hidden">
      {/* Background decorations */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-500/8 rounded-full blur-3xl" />
        <div className="absolute top-1/3 right-1/4 w-80 h-80 bg-violet-500/6 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 left-1/3 w-72 h-72 bg-cyan-500/5 rounded-full blur-3xl" />
        {/* Grid pattern */}
        <div className="absolute inset-0 opacity-[0.015]"
          style={{
            backgroundImage: 'linear-gradient(rgba(99,102,241,1) 1px, transparent 1px), linear-gradient(90deg, rgba(99,102,241,1) 1px, transparent 1px)',
            backgroundSize: '60px 60px',
          }}
        />
      </div>

      {/* Navbar */}
      <nav className="relative z-10 border-b border-slate-800/60 bg-slate-950/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 via-violet-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <BarChart3 className="w-4 h-4 text-white" />
            </div>
            <div>
              <span className="text-base font-bold text-slate-100">FeedbackPulse</span>
              <span className="ml-2 text-[10px] text-indigo-300/70 uppercase tracking-wider">by Microsoft</span>
            </div>
          </div>

          {/* Nav links */}
          <div className="hidden md:flex items-center gap-6 text-sm text-slate-400">
            <a href="#features" className="hover:text-slate-100 transition-colors">Features</a>
            <a href="#pipeline" className="hover:text-slate-100 transition-colors">Pipeline</a>
            <a href="#intelligence" className="hover:text-slate-100 transition-colors">RL + LLM</a>
          </div>

          {/* Auth buttons */}
          <div className="flex items-center gap-3">
            <button
              id="nav-login-btn"
              onClick={() => setAuthMode('login')}
              className="text-sm text-slate-300 hover:text-white transition-colors px-3 py-1.5"
            >
              Sign In
            </button>
            <button
              id="nav-signup-btn"
              onClick={() => setAuthMode('signup')}
              className="text-sm bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold rounded-xl px-4 py-2 shadow-lg shadow-indigo-500/25 transition-all"
            >
              Get Started
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
        <div className="text-center max-w-4xl mx-auto">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/25 rounded-full px-4 py-1.5 mb-8 animate-fade-in-up">
            <Zap className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-xs text-indigo-300 font-medium">Powered by Azure AI · Microsoft Hackathon 2026</span>
          </div>

          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold text-slate-100 tracking-tight mb-6 animate-fade-in-up delay-100">
            AI-powered Review Intelligence that converts thousands of customer reviews into
            <span className="block gradient-text mt-1">actionable product decisions.</span>
          </h1>

          <p className="text-lg sm:text-xl text-slate-400 mb-10 max-w-2xl mx-auto leading-relaxed animate-fade-in-up delay-200">
            FeedbackPulse uses advanced LLMs and Reinforcement Learning to analyze customer reviews, detect sentiment trends, uncover root-cause hypotheses, and deliver prioritized product recommendations — all in seconds.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16 animate-fade-in-up delay-300">
            <button
              id="hero-signup-btn"
              onClick={() => setAuthMode('signup')}
              className="group flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold rounded-2xl px-8 py-4 text-base shadow-xl shadow-indigo-500/30 transition-all hover:-translate-y-0.5"
            >
              <span>Get Started</span>
              <ChevronRight className="w-5 h-5 group-hover:translate-x-0.5 transition-transform" />
            </button>
            <button
              id="hero-demo-btn"
              onClick={() => setAuthMode('login')}
              className="flex items-center gap-2 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-slate-200 font-semibold rounded-2xl px-8 py-4 text-base transition-all hover:-translate-y-0.5"
            >
              <span>View Demo</span>
            </button>
          </div>

          {/* Stats bar */}
          <div id="stats" className="flex flex-wrap items-center justify-center gap-8 py-6 border-y border-slate-800/60 animate-fade-in-up delay-400">
            <StatBadge value="10K+" label="Reviews Analyzed" />
            <div className="w-px h-8 bg-slate-800" />
            <StatBadge value="62.4%" label="Avg Positive Sentiment" />
            <div className="w-px h-8 bg-slate-800" />
            <StatBadge value="5" label="Theme Categories" />
            <div className="w-px h-8 bg-slate-800" />
            <StatBadge value="< 60s" label="Analysis Time" />
          </div>
        </div>
      </section>

      {/* Dashboard Preview */}
      <section className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-24">
        <div className="relative rounded-3xl overflow-hidden border border-slate-700/50 shadow-2xl shadow-slate-950">
          {/* Gradient overlay on top */}
          <div className="absolute top-0 left-0 right-0 h-24 bg-gradient-to-b from-slate-950 to-transparent z-10 pointer-events-none" />
          {/* Dashboard preview mockup */}
          <div className="bg-slate-900 p-6">
            {/* Mock stats row */}
            <div className="grid grid-cols-4 gap-3 mb-4">
              {[
                { label: 'Total Reviews', value: '10,000', color: 'text-slate-100', icon: '📊' },
                { label: 'Positive', value: '62.4%', color: 'text-emerald-400', icon: '😊' },
                { label: 'Negative', value: '18.9%', color: 'text-rose-400', icon: '😞' },
                { label: 'Neutral', value: '18.7%', color: 'text-amber-400', icon: '😐' },
              ].map((stat) => (
                <div key={stat.label} className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span>{stat.icon}</span>
                    <span className="text-xs text-slate-400">{stat.label}</span>
                  </div>
                  <div className={`text-2xl font-extrabold ${stat.color}`}>{stat.value}</div>
                  <div className="mt-2 h-1 bg-slate-700 rounded-full overflow-hidden">
                    <div className="h-full w-3/4 bg-gradient-to-r from-indigo-500 to-violet-500 rounded-full" />
                  </div>
                </div>
              ))}
            </div>
            {/* Mock insight card */}
            <div className="grid grid-cols-3 gap-3">
              <div className="col-span-2 bg-gradient-to-br from-indigo-500/10 to-violet-500/10 border border-indigo-500/25 rounded-xl p-4">
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-xs bg-rose-500/20 text-rose-300 border border-rose-500/30 px-2 py-0.5 rounded-full font-medium">High Priority</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <Sparkles className="w-3.5 h-3.5 text-indigo-400"/>
                        <span className="text-xs font-bold text-indigo-400">AI Intelligence</span>
                    </div>
                </div>
                <h4 className="text-sm font-bold text-slate-100 mb-2">Authentication is your biggest source of negative feedback</h4>
                <p className="text-xs text-slate-400 mb-3">Root Cause: Likely an issue with OTP delivery delays or token refresh failures based on recent review patterns.</p>
                <div className="bg-slate-900/50 p-2 rounded-lg border border-slate-700/50 mb-3">
                    <span className="text-[10px] font-bold text-slate-300 block mb-1">RL Recommendation:</span>
                    <p className="text-xs text-indigo-300">Investigate Root Cause (Confidence: 89%)</p>
                </div>
                <div className="mt-3 h-1.5 bg-slate-700/60 rounded-full overflow-hidden">
                  <div className="h-full w-[71%] bg-rose-500 rounded-full" />
                </div>
              </div>
              <div className="space-y-2">
                {['Login & Auth', 'Payment Issues', 'App Performance'].map((item, i) => (
                  <div key={item} className="bg-slate-800/60 border border-slate-700/50 rounded-lg px-3 py-2 flex items-center justify-between">
                    <span className="text-xs text-slate-300">{item}</span>
                    <span className="text-xs font-bold text-indigo-400">{[24, 18, 15][i]}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          {/* Bottom gradient overlay */}
          <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-slate-950 to-transparent z-10 pointer-events-none" />
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-24">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-100 mb-4">
            Everything you need to
            <span className="gradient-text"> understand your users</span>
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto">
            From raw CSV data to actionable product intelligence — all automated, all AI-powered.
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {features.map((f) => (
            <FeatureCard key={f.title} {...f} />
          ))}
        </div>
      </section>

      {/* AI/ML Pipeline */}
      <section id="pipeline" className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-24">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-extrabold text-slate-100 mb-4">How it works: The AI/ML Pipeline</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-6 gap-4 items-center">
          {[
            { step: '01', icon: '📤', label: 'Upload Data', desc: 'Raw CSV Reviews' },
            { icon: '→', label: '', desc: '', isArrow: true },
            { step: '02', icon: '🧠', label: 'ML Models', desc: 'Sentiment, Emotion, Clustering' },
            { icon: '→', label: '', desc: '', isArrow: true },
            { step: '03', icon: '🤖', label: 'Intelligence', desc: 'LLM Reasoning + RL Actions' },
            { icon: '→', label: '', desc: '', isArrow: true },
            { step: '04', icon: '📈', label: 'Product Impact', desc: 'Executive PM Briefs' },
          ].map((item, i) => (
            item.isArrow ? (
              <div key={i} className="hidden md:block text-center text-slate-600 text-2xl font-bold">→</div>
            ) : (
              <div key={i} className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 text-center hover:border-indigo-500/30 transition-all">
                <div className="text-3xl mb-3">{item.icon}</div>
                <div className="text-xs text-indigo-400 font-bold mb-1">{item.step}</div>
                <div className="text-sm font-bold text-slate-100 mb-1">{item.label}</div>
                <div className="text-[10px] text-slate-400">{item.desc}</div>
              </div>
            )
          ))}
        </div>
      </section>

      {/* RL + LLM Section */}
      <section id="intelligence" className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-24">
          <div className="bg-slate-900/50 border border-slate-800 rounded-3xl p-8 lg:p-12">
              <div className="text-center mb-12">
                  <h2 className="text-3xl font-extrabold text-slate-100 mb-4">Next-Generation <span className="gradient-text">Intelligence</span></h2>
                  <p className="text-slate-400 max-w-2xl mx-auto">We don't just classify sentiment. Our dual-agent architecture reasons about root causes and learns optimal product strategies over time.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div className="bg-slate-950/50 border border-slate-800/80 rounded-2xl p-6">
                      <div className="flex items-center gap-3 mb-4">
                          <div className="p-2 bg-indigo-500/20 rounded-lg text-indigo-400"><Brain className="w-6 h-6"/></div>
                          <h3 className="text-xl font-bold text-slate-100">LLM Reasoning Layer</h3>
                      </div>
                      <p className="text-sm text-slate-400 mb-4">Sits on top of the traditional ML pipeline to provide human-like synthesis of complex data signals.</p>
                      <ul className="space-y-3">
                          {[
                              "Synthesizes Executive Summaries",
                              "Formulates Root-Cause Hypotheses",
                              "Explains 'Why It Matters'",
                              "Grounded in Traceable Review Evidence"
                          ].map((item, idx) => (
                              <li key={idx} className="flex items-start gap-2 text-sm text-slate-300">
                                  <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0"/>
                                  <span>{item}</span>
                              </li>
                          ))}
                      </ul>
                  </div>

                  <div className="bg-slate-950/50 border border-slate-800/80 rounded-2xl p-6">
                      <div className="flex items-center gap-3 mb-4">
                          <div className="p-2 bg-violet-500/20 rounded-lg text-violet-400"><Activity className="w-6 h-6"/></div>
                          <h3 className="text-xl font-bold text-slate-100">RL Recommendation Engine</h3>
                      </div>
                      <p className="text-sm text-slate-400 mb-4">A contextual bandit / Q-learning agent that optimizes issue prioritization based on PM feedback.</p>
                      <ul className="space-y-3">
                          {[
                              "Suggests: Prioritize, Monitor, Investigate, or Fix",
                              "Learns from PM feedback (+1 / -1 rewards)",
                              "Accounts for Severity, Sentiment, Volume, and Trend",
                              "Adapts to your specific product lifecycle"
                          ].map((item, idx) => (
                              <li key={idx} className="flex items-start gap-2 text-sm text-slate-300">
                                  <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0"/>
                                  <span>{item}</span>
                              </li>
                          ))}
                      </ul>
                  </div>
              </div>
          </div>
      </section>

      {/* CTA Section */}
      <section className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-24">
        <div className="bg-gradient-to-br from-indigo-950/60 to-violet-950/60 border border-indigo-500/25 rounded-3xl p-12 text-center relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-violet-500/5" />
          <div className="relative">
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-100 mb-4">
              Better insights. Happier users.
            </h2>
            <p className="text-slate-400 mb-8 max-w-md mx-auto">
              Join product teams using FeedbackPulse to transform raw reviews into product strategy.
            </p>
            <button
              id="cta-signup-btn"
              onClick={() => setAuthMode('signup')}
              className="group inline-flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold rounded-2xl px-10 py-4 text-base shadow-xl shadow-indigo-500/30 transition-all hover:-translate-y-0.5"
            >
              <span>Get Started for Free</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-0.5 transition-transform" />
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-slate-800/60 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center">
              <BarChart3 className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="text-sm font-semibold text-slate-300">FeedbackPulse</span>
            <span className="text-xs text-slate-500">by Microsoft Hackathon Team</span>
          </div>
          <p className="text-xs text-slate-500">Smarter feedback. Better decisions. Powered by Azure AI, LLMs & RL.</p>
        </div>
      </footer>

      {/* Auth Modal */}
      {authMode && (
        <AuthModal
          mode={authMode}
          onClose={() => setAuthMode(null)}
          onSwitchMode={() => setAuthMode(authMode === 'login' ? 'signup' : 'login')}
        />
      )}
    </div>
  );
}
