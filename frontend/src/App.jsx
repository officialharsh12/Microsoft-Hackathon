import React, { useState, useEffect } from 'react';
import {
  LayoutGrid, UploadCloud, BarChart3, Database, MessageSquareText,
  Sparkles, ShieldCheck, TrendingUp, SlidersHorizontal, Settings,
  Bot, FileText, SearchCheck, ChevronDown, LogOut, Star, Zap,
  FolderKanban, AlertTriangle
} from 'lucide-react';
import Navbar from './components/Navbar';
import UploadPage from './pages/UploadPage';
import DashboardPage from './pages/DashboardPage';
import IssueDetailPage from './pages/IssueDetailPage';
import PMBriefPage from './pages/PMBriefPage';
import LandingPage from './pages/LandingPage';
import { AuthProvider, useAuth } from './context/AuthContext';
import { api } from './services/api';

// ─── Sidebar navigation config (matches FeedbackPulse screenshot) ────────────
const NAV_SECTIONS = [
  {
    items: [
      { key: 'dashboard', label: 'Overview', icon: LayoutGrid },
      { key: 'reviews', label: 'Reviews', icon: MessageSquareText },
      { key: 'themes', label: 'Themes', icon: Sparkles },
      { key: 'sentiment', label: 'Sentiment', icon: SearchCheck },
      { key: 'trends', label: 'Trends', icon: TrendingUp },
      { key: 'validation', label: 'Validation', icon: Database },
      { key: 'privacy', label: 'Privacy', icon: SlidersHorizontal },
    ],
  },
  {
    label: 'Tools',
    items: [
      { key: 'assistant', label: 'AI Assistant', icon: Bot, badge: 'New' },
      { key: 'settings', label: 'Settings', icon: Settings },
    ],
  },
];

// ─── Main app shell (authenticated) ─────────────────────────────────────────
function AppShell() {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [dashboardData, setDashboardData] = useState(null);
  const [datasets, setDatasets] = useState([]);
  const [selectedIssueId, setSelectedIssueId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeDatasetId, setActiveDatasetId] = useState(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const loadDatasets = async () => {
    try {
      const list = await api.listDatasets();
      setDatasets(list || []);
      if (!activeDatasetId && list?.length) {
        setActiveDatasetId(list[0].id);
      }
    } catch (err) {
      console.error('Failed to load datasets:', err);
    }
  };

  const loadDashboard = async (datasetId = null) => {
    try {
      setIsLoading(true);
      const targetDatasetId = datasetId ?? activeDatasetId;
      const data = await api.getDashboard(targetDatasetId);
      setDashboardData(data);
      if (data && data.dataset_id) {
        setActiveDatasetId(data.dataset_id);
      }
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDatasets();
    loadDashboard();
  }, []);

  useEffect(() => {
    if (activeDatasetId) {
      loadDashboard(activeDatasetId);
    }
  }, [activeDatasetId]);

  const handleAnalysisComplete = (newDatasetId) => {
    setActiveDatasetId(newDatasetId);
    loadDashboard(newDatasetId);
    setActiveTab('dashboard');
  };

  const handleSelectIssue = (issueId) => {
    setSelectedIssueId(issueId);
    setActiveTab('issue-detail');
  };

  const handleOpenBrief = (issueId) => {
    setSelectedIssueId(issueId);
    setActiveTab('pm-brief');
  };

  const datasetInfo = dashboardData?.dataset_id
    ? {
        filename: dashboardData.dataset_filename,
        total_reviews: dashboardData.total_reviews,
      }
    : datasets.find((d) => d.id === activeDatasetId) || null;

  const navTabChange = (key) => {
    if (key === 'upload') {
      setActiveTab('upload');
    } else {
      setActiveTab('dashboard');
      if (key === 'dashboard' && !dashboardData) loadDashboard(activeDatasetId);
    }
  };

  return (
    <div className="min-h-screen bg-[#f0f2f8] text-slate-800 flex" style={{ fontFamily: "'Inter', sans-serif" }}>
      {/* ── Sidebar ────────────────────────────────────────────────────────── */}
      <aside
        className="flex-shrink-0 flex flex-col bg-white border-r border-slate-200/80 shadow-sm"
        style={{ width: sidebarCollapsed ? '64px' : '220px', transition: 'width 0.2s ease' }}
      >
        {/* Logo */}
        <div className="flex items-center gap-2.5 px-4 py-4 border-b border-slate-100">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 via-violet-500 to-cyan-400 flex items-center justify-center shadow-md shadow-indigo-500/30 flex-shrink-0">
            <BarChart3 className="w-4 h-4 text-white" />
          </div>
          {!sidebarCollapsed && (
            <div className="overflow-hidden">
              <p className="text-[10px] font-semibold text-indigo-500 uppercase tracking-wider leading-none">FeedbackPulse</p>
              <p className="text-[9px] text-slate-400 leading-tight mt-0.5">From Reviews to Real Insights</p>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
          {NAV_SECTIONS.map((section, si) => (
            <div key={si} className={si > 0 ? 'pt-3 mt-2 border-t border-slate-100' : ''}>
              {section.label && !sidebarCollapsed && (
                <p className="text-[9px] font-semibold uppercase tracking-widest text-slate-400 px-2 pb-1.5">{section.label}</p>
              )}
              {section.items.map(({ key, label, icon: Icon, badge }) => {
                const isActive = (key === 'upload' && activeTab === 'upload') || (key === 'dashboard' && activeTab === 'dashboard');
                return (
                  <button
                    key={key}
                    id={`sidebar-${key}`}
                    onClick={() => navTabChange(key)}
                    title={sidebarCollapsed ? label : ''}
                    className={`w-full flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-xs font-medium transition-all group ${
                      isActive
                        ? 'bg-indigo-50 text-indigo-700 shadow-sm'
                        : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                    }`}
                  >
                    <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-indigo-500' : 'text-slate-400 group-hover:text-slate-600'}`} />
                    {!sidebarCollapsed && (
                      <>
                        <span className="flex-1 text-left truncate">{label}</span>
                        {badge && (
                          <span className="text-[9px] bg-indigo-100 text-indigo-600 font-semibold px-1.5 py-0.5 rounded-full">{badge}</span>
                        )}
                      </>
                    )}
                  </button>
                );
              })}
            </div>
          ))}
        </nav>

        {/* Datasets section */}
        {!sidebarCollapsed && (
          <div className="border-t border-slate-100 px-2 py-2">
            <p className="text-[9px] font-semibold uppercase tracking-widest text-slate-400 px-2 pb-1">Datasets</p>
            <div className="space-y-0.5 max-h-36 overflow-y-auto">
              {datasets.length === 0 && (
                <div className="text-[10px] text-slate-400 px-2 py-1.5 italic">No datasets yet</div>
              )}
              {datasets.map((ds) => (
                <button
                  key={ds.id}
                  onClick={() => setActiveDatasetId(ds.id)}
                  className={`w-full text-left rounded-lg px-2.5 py-1.5 transition-all ${
                    activeDatasetId === ds.id
                      ? 'bg-indigo-50 text-indigo-700'
                      : 'text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <div className="text-[11px] font-medium truncate">{ds.dataset_name || ds.filename}</div>
                  <div className="text-[9px] text-slate-400">{ds.review_count ?? 0} reviews · {ds.status || 'ready'}</div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Bottom: user + status */}
        <div className="border-t border-slate-100 p-3 space-y-2">
          {/* Pipeline status */}
          {!sidebarCollapsed && (
            <div className="flex items-center gap-2 text-[10px] text-slate-400 bg-slate-50 rounded-lg px-2.5 py-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse flex-shrink-0" />
              <span className="truncate">Pipeline online</span>
            </div>
          )}
          {/* User + logout */}
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-md bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
              {user?.avatar || user?.name?.charAt(0) || 'U'}
            </div>
            {!sidebarCollapsed && (
              <>
                <div className="flex-1 min-w-0">
                  <div className="text-[11px] font-semibold text-slate-700 truncate">{user?.name}</div>
                  <div className="text-[9px] text-slate-400 truncate">{user?.role}</div>
                </div>
                <button
                  id="sidebar-logout-btn"
                  onClick={logout}
                  title="Sign out"
                  className="w-6 h-6 rounded-md flex items-center justify-center text-slate-400 hover:text-rose-500 hover:bg-rose-50 transition-all flex-shrink-0"
                >
                  <LogOut className="w-3.5 h-3.5" />
                </button>
              </>
            )}
          </div>

          {/* Microsoft badge */}
          {!sidebarCollapsed && (
            <div className="text-[9px] text-slate-300 text-center">Powered by Azure AI • Microsoft</div>
          )}
        </div>
      </aside>

      {/* ── Main content ───────────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar
          activeTab={activeTab}
          setActiveTab={navTabChange}
          datasetInfo={datasetInfo}
          datasets={datasets}
          activeDatasetId={activeDatasetId}
          onDatasetChange={setActiveDatasetId}
        />

        <main className="flex-1 overflow-auto">
          {activeTab === 'upload' && (
            <UploadPage onAnalysisComplete={handleAnalysisComplete} />
          )}

          {activeTab === 'dashboard' && (
            <DashboardPage
              data={dashboardData}
              onSelectIssue={handleSelectIssue}
              onOpenUpload={() => setActiveTab('upload')}
              onOpenBrief={handleOpenBrief}
            />
          )}

          {activeTab === 'issue-detail' && selectedIssueId && (
            <IssueDetailPage
              issueId={selectedIssueId}
              onBack={() => setActiveTab('dashboard')}
              onOpenBrief={handleOpenBrief}
            />
          )}

          {activeTab === 'pm-brief' && (
            <PMBriefPage
              issueId={selectedIssueId || null}
              onBack={() => selectedIssueId ? setActiveTab('issue-detail') : setActiveTab('dashboard')}
            />
          )}
        </main>
      </div>
    </div>
  );
}

// ─── Root component with auth gate ──────────────────────────────────────────
function AuthGate() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 via-violet-500 to-cyan-400 flex items-center justify-center shadow-xl shadow-indigo-500/30 animate-pulse">
            <BarChart3 className="w-6 h-6 text-white" />
          </div>
          <p className="text-slate-400 text-sm">Loading FeedbackPulse...</p>
        </div>
      </div>
    );
  }

  return user ? <AppShell /> : <LandingPage />;
}

export default function App() {
  return (
    <AuthProvider>
      <AuthGate />
    </AuthProvider>
  );
}
