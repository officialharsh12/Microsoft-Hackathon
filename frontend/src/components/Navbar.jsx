import React, { useState } from 'react';
import { UploadCloud, Bell, ChevronDown, Search, CalendarRange, LogOut, User, Settings } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Navbar({ activeTab, setActiveTab, datasetInfo, datasets = [], activeDatasetId, onDatasetChange }) {
  const { user, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);

  return (
    <header className="border-b border-slate-800/80 bg-white/[0.02] backdrop-blur-xl sticky top-0 z-40">
      <div className="h-[60px] px-4 sm:px-6 flex items-center justify-between gap-3">
        {/* Left side - Search + Date Range */}
        <div className="flex-1 min-w-0 flex items-center gap-3">
          {/* Search input */}
          <div className="hidden md:flex items-center gap-2 rounded-lg border border-slate-700/60 bg-slate-900/60 px-3 py-1.5 text-xs text-slate-300 min-w-[240px] max-w-xs">
            <Search className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
            <input
              id="navbar-search"
              type="text"
              placeholder="Search reviews, themes, or insights..."
              className="w-full bg-transparent text-slate-200 placeholder:text-slate-500 outline-none text-xs"
            />
          </div>

          {/* Date range selector */}
          <div className="hidden lg:flex items-center gap-2 rounded-lg border border-slate-700/60 bg-slate-900/60 px-3 py-1.5 text-xs text-slate-300 cursor-pointer hover:border-slate-600 transition-colors">
            <CalendarRange className="w-3.5 h-3.5 text-slate-400" />
            <span>Last 30 Days</span>
            <ChevronDown className="w-3 h-3 text-slate-500" />
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-2">
          {/* Upload button */}
          <button
            id="navbar-upload-btn"
            onClick={() => setActiveTab('upload')}
            className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 px-4 py-1.5 text-xs font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all"
          >
            <UploadCloud className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Upload Reviews</span>
          </button>

          {/* Notification bell */}
          <button
            id="navbar-bell-btn"
            className="relative w-8 h-8 rounded-lg border border-slate-700/60 bg-slate-900/60 flex items-center justify-center text-slate-400 hover:text-slate-100 hover:border-slate-600 transition-all"
          >
            <Bell className="w-3.5 h-3.5" />
            <span className="absolute top-1 right-1 w-1.5 h-1.5 bg-rose-500 rounded-full" />
          </button>

          {/* User avatar + menu */}
          <div className="relative">
            <button
              id="navbar-user-btn"
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2 rounded-lg border border-slate-700/60 bg-slate-900/60 pl-1.5 pr-3 py-1 hover:border-slate-600 transition-all"
            >
              {/* Avatar circle */}
              <div className="w-7 h-7 rounded-md bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                {user?.avatar || user?.name?.charAt(0) || 'U'}
              </div>
              <div className="hidden sm:block text-left leading-tight">
                <div className="text-xs font-semibold text-slate-100 truncate max-w-[100px]">{user?.name || 'User'}</div>
                <div className="text-[10px] text-slate-500">{user?.role || 'Product Manager'}</div>
              </div>
              <ChevronDown className="w-3 h-3 text-slate-500 flex-shrink-0" />
            </button>

            {/* Dropdown menu */}
            {showUserMenu && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setShowUserMenu(false)} />
                <div className="absolute right-0 top-full mt-2 w-52 bg-slate-900 border border-slate-700/60 rounded-xl shadow-xl shadow-slate-950/50 z-50 overflow-hidden">
                  <div className="p-3 border-b border-slate-800">
                    <div className="text-xs font-semibold text-slate-100">{user?.name}</div>
                    <div className="text-[10px] text-slate-400 truncate">{user?.email}</div>
                  </div>
                  <div className="p-1">
                    <button className="w-full flex items-center gap-2 px-3 py-2 text-xs text-slate-300 hover:bg-slate-800 rounded-lg transition-colors">
                      <User className="w-3.5 h-3.5" />
                      <span>Profile</span>
                    </button>
                    <button className="w-full flex items-center gap-2 px-3 py-2 text-xs text-slate-300 hover:bg-slate-800 rounded-lg transition-colors">
                      <Settings className="w-3.5 h-3.5" />
                      <span>Settings</span>
                    </button>
                    <div className="border-t border-slate-800 mt-1 pt-1">
                      <button
                        id="navbar-logout-btn"
                        onClick={logout}
                        className="w-full flex items-center gap-2 px-3 py-2 text-xs text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
                      >
                        <LogOut className="w-3.5 h-3.5" />
                        <span>Sign Out</span>
                      </button>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
