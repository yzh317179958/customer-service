import React, { useEffect, useMemo, useState } from 'react';
import { Download, RefreshCw, Search, Pencil, FileDown, X } from 'lucide-react';
import {
  HistoryMessageItem,
  HistoryRole,
  HistorySessionSummary,
  ExportJobItem,
  historyApi,
} from '../src/api';

function formatTime(ts?: number | null): string {
  if (!ts) return '--';
  const d = new Date(ts * 1000);
  return d.toLocaleString();
}

function toUnixSeconds(datetimeLocalValue: string): number | undefined {
  const v = (datetimeLocalValue || '').trim();
  if (!v) return undefined;
  const date = new Date(v);
  const ms = date.getTime();
  if (Number.isNaN(ms)) return undefined;
  return ms / 1000;
}

function toDatetimeLocal(tsSeconds: number): string {
  const d = new Date(tsSeconds * 1000);
  const pad = (n: number) => String(n).padStart(2, '0');
  const yyyy = d.getFullYear();
  const mm = pad(d.getMonth() + 1);
  const dd = pad(d.getDate());
  const hh = pad(d.getHours());
  const mi = pad(d.getMinutes());
  return `${yyyy}-${mm}-${dd}T${hh}:${mi}`;
}

function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

const roleBadgeStyles: Record<HistoryRole, string> = {
  user: 'bg-slate-100 text-slate-700 border-slate-200',
  assistant: 'bg-fiido/10 text-fiido border-fiido/20',
  agent: 'bg-black/5 text-black border-black/10',
};

const roleLabels: Record<HistoryRole, string> = {
  user: '用户',
  assistant: 'AI',
  agent: '坐席',
};

const exportStatusLabels: Record<ExportJobItem['status'], string> = {
  pending: '排队中',
  running: '生成中',
  done: '已完成',
  failed: '失败',
};

const ChatHistoryView: React.FC = () => {
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [sessionsError, setSessionsError] = useState<string | null>(null);
  const [sessions, setSessions] = useState<Array<HistorySessionSummary & { match_count?: number; last_match_preview?: string; last_match_at?: number }>>([]);
  const [sessionsTotal, setSessionsTotal] = useState(0);

  const [selectedSession, setSelectedSession] = useState<string | null>(null);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [messagesError, setMessagesError] = useState<string | null>(null);
  const [messages, setMessages] = useState<HistoryMessageItem[]>([]);
  const [messagesTotal, setMessagesTotal] = useState(0);
  const [messagesOffsetDesc, setMessagesOffsetDesc] = useState(0);
  const [messagesLimit, setMessagesLimit] = useState(50);
  const [canLoadOlder, setCanLoadOlder] = useState(false);

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(100);
  const [compactMode, setCompactMode] = useState(true);

  const [startTimeLocal, setStartTimeLocal] = useState('');
  const [endTimeLocal, setEndTimeLocal] = useState('');
  const [timePreset, setTimePreset] = useState<'today' | 'yesterday' | '7d' | 'custom'>('today');

  const [sessionKeyword, setSessionKeyword] = useState('');

  const [messageSearchQuery, setMessageSearchQuery] = useState('');
  const [messageSearchRole, setMessageSearchRole] = useState<HistoryRole | ''>('');
  const [messageSearchScope, setMessageSearchScope] = useState<'session' | 'all'>('session');
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<HistoryMessageItem[]>([]);
  const [searchTotal, setSearchTotal] = useState(0);

  const [translationEnabled, setTranslationEnabled] = useState(false);
  const [translationByMessageId, setTranslationByMessageId] = useState<Record<string, string>>({});
  const [translationLoadingByMessageId, setTranslationLoadingByMessageId] = useState<Record<string, boolean>>({});
  const [translationErrorByMessageId, setTranslationErrorByMessageId] = useState<Record<string, string>>({});
  const [translationVisibleByMessageId, setTranslationVisibleByMessageId] = useState<Record<string, boolean>>({});

  const [showMetaEditor, setShowMetaEditor] = useState(false);
  const [metaDisplayName, setMetaDisplayName] = useState('');
  const [metaNote, setMetaNote] = useState('');
  const [metaTags, setMetaTags] = useState('');
  const [metaSaving, setMetaSaving] = useState(false);

  const [showExportPanel, setShowExportPanel] = useState(false);
  const [exportKeyword, setExportKeyword] = useState('');
  const [exportRole, setExportRole] = useState<HistoryRole | ''>('');
  const [exportScope, setExportScope] = useState<'session' | 'all'>('all');
  const [exportJobs, setExportJobs] = useState<ExportJobItem[]>([]);
  const [exportJobsLoading, setExportJobsLoading] = useState(false);
  const [exportJobsError, setExportJobsError] = useState<string | null>(null);

  const startTime = useMemo(() => toUnixSeconds(startTimeLocal), [startTimeLocal]);
  const endTime = useMemo(() => toUnixSeconds(endTimeLocal), [endTimeLocal]);

  const selectedSessionSummary = useMemo(() => {
    if (!selectedSession) return null;
    return sessions.find((s) => s.session_name === selectedSession) || null;
  }, [selectedSession, sessions]);
  const selectedSessionDisplayName = (selectedSessionSummary as any)?.meta?.display_name as string | undefined;
  const selectedSessionTitle = (selectedSessionDisplayName && selectedSessionDisplayName.trim()) || selectedSession || '';

  const loadSessions = async () => {
    setIsLoadingSessions(true);
    setSessionsError(null);
    try {
      const keyword = sessionKeyword.trim();
      if (keyword.length >= 2) {
        const res = await historyApi.searchSessions({
          q: keyword,
          page,
          page_size: pageSize,
          start_time: startTime,
          end_time: endTime,
        });
        setSessions(
          (res.items || []).map((it) => ({
            session_name: it.session_name,
            meta: it.meta || null,
            last_message_preview: it.last_match_preview,
            message_count: it.match_count,
            first_message_at: 0,
            last_message_at: it.last_match_at,
            conversation_count: 0,
            match_count: it.match_count,
            last_match_preview: it.last_match_preview,
            last_match_at: it.last_match_at,
          }))
        );
        setSessionsTotal(res.total || 0);
        if (!selectedSession && res.items?.length) {
          setSelectedSession(res.items[0].session_name);
        }
      } else {
        const res = await historyApi.listSessions({
          page,
          page_size: pageSize,
          start_time: startTime,
          end_time: endTime,
        });
        setSessions(res.items || []);
        setSessionsTotal(res.total || 0);
        if (!selectedSession && res.items?.length) {
          setSelectedSession(res.items[0].session_name);
        }
      }
    } catch (e: any) {
      setSessionsError(e?.message || '加载会话列表失败');
    } finally {
      setIsLoadingSessions(false);
    }
  };

  const loadLatestMessages = async (sessionName: string) => {
    setIsLoadingMessages(true);
    setMessagesError(null);
    try {
      const res = await historyApi.getSessionDetail(sessionName, { limit: messagesLimit, offset: 0, order: 'desc' });
      const chunkAsc = [...(res.items || [])].reverse();
      setMessages(chunkAsc);
      setMessagesTotal(res.total || 0);
      setMessagesOffsetDesc(0);
      setCanLoadOlder((res.total || 0) > chunkAsc.length);
    } catch (e: any) {
      setMessagesError(e?.message || '加载会话详情失败');
    } finally {
      setIsLoadingMessages(false);
    }
  };

  const loadOlderMessages = async () => {
    if (!selectedSession) return;
    if (!canLoadOlder) return;
    const nextOffset = messagesOffsetDesc + messagesLimit;
    setIsLoadingMessages(true);
    setMessagesError(null);
    try {
      const res = await historyApi.getSessionDetail(selectedSession, { limit: messagesLimit, offset: nextOffset, order: 'desc' });
      const chunkAsc = [...(res.items || [])].reverse();
      setMessages((prev) => [...chunkAsc, ...prev]);
      setMessagesTotal(res.total || 0);
      setMessagesOffsetDesc(nextOffset);
      setCanLoadOlder(nextOffset + messagesLimit < (res.total || 0));
    } catch (e: any) {
      setMessagesError(e?.message || '加载更多消息失败');
    } finally {
      setIsLoadingMessages(false);
    }
  };

  useEffect(() => {
    loadSessions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, pageSize, startTime, endTime]);

  useEffect(() => {
    if (!selectedSession) return;
    loadLatestMessages(selectedSession);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedSession]);

  useEffect(() => {
    if (startTimeLocal || endTimeLocal) return;
    const now = new Date();
    const start = new Date(now);
    start.setHours(0, 0, 0, 0);
    setStartTimeLocal(toDatetimeLocal(start.getTime() / 1000));
    setEndTimeLocal(toDatetimeLocal(now.getTime() / 1000));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const runSearch = async () => {
    const q = messageSearchQuery.trim();
    if (q.length < 2) {
      setSearchError('搜索词至少 2 个字符。');
      return;
    }

    setIsSearching(true);
    setSearchError(null);
    try {
      const res = await historyApi.searchMessages({
        q,
        start_time: startTime,
        end_time: endTime,
        role: messageSearchRole || undefined,
        session_name: messageSearchScope === 'session' ? selectedSession || undefined : undefined,
        page: 1,
        page_size: 50,
      });
      setSearchResults(res.items || []);
      setSearchTotal(res.total || 0);
    } catch (e: any) {
      setSearchError(e?.message || '搜索失败');
    } finally {
      setIsSearching(false);
    }
  };

  const exportCsv = async () => {
    if (!selectedSession) return;
    try {
      const blob = await historyApi.exportMessagesCsv({
        session_name: selectedSession,
        start_time: startTime,
        end_time: endTime,
      });
      const filename = `chat_history_${selectedSession.replace(/[\\/]/g, '_')}.csv`;
      downloadBlob(blob, filename);
    } catch (e: any) {
      setMessagesError(e?.message || '导出失败');
    }
  };

  const openMetaEditor = async () => {
    if (!selectedSession) return;
    try {
      const res = await historyApi.getSessionMeta(selectedSession);
      const meta = res.meta;
      setMetaDisplayName(meta?.display_name || '');
      setMetaNote(meta?.note || '');
      if (meta?.tags) {
        if (Array.isArray(meta.tags)) {
          setMetaTags(meta.tags.join(','));
        } else {
          setMetaTags(JSON.stringify(meta.tags));
        }
      } else {
        setMetaTags('');
      }
      setShowMetaEditor(true);
    } catch (e: any) {
      setMessagesError(e?.message || '加载会话备注失败');
    }
  };

  const saveMeta = async () => {
    if (!selectedSession) return;
    setMetaSaving(true);
    try {
      let tags: any = null;
      const raw = metaTags.trim();
      if (raw) {
        if (raw.startsWith('[') || raw.startsWith('{')) {
          tags = JSON.parse(raw);
        } else {
          tags = raw
            .split(',')
            .map((t) => t.trim())
            .filter(Boolean);
        }
      }

      const res = await historyApi.updateSessionMeta(selectedSession, {
        display_name: metaDisplayName || null,
        note: metaNote || null,
        tags,
      });

      setSessions((prev) =>
        prev.map((s) =>
          s.session_name === selectedSession
            ? {
                ...s,
                meta: res.meta || null,
              }
            : s
        )
      );
      setShowMetaEditor(false);
    } catch (e: any) {
      setMessagesError(e?.message || '保存会话备注失败');
    } finally {
      setMetaSaving(false);
    }
  };

  const loadExportJobs = async () => {
    setExportJobsLoading(true);
    setExportJobsError(null);
    try {
      const res = await historyApi.listExportJobs({ limit: 50, offset: 0 });
      setExportJobs(res.items || []);
    } catch (e: any) {
      setExportJobsError(e?.message || '加载导出任务失败');
    } finally {
      setExportJobsLoading(false);
    }
  };

  const openExportCenter = async () => {
    setShowExportPanel(true);
    await loadExportJobs();
  };

  useEffect(() => {
    if (!showExportPanel) return;
    const interval = setInterval(() => {
      const hasRunning = exportJobs.some((j) => j.status === 'pending' || j.status === 'running');
      if (hasRunning) {
        loadExportJobs();
      }
    }, 5000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showExportPanel, exportJobs]);

  const createBatchExportJob = async () => {
    if (!startTime || !endTime) {
      setExportJobsError('请先选择开始时间/结束时间（批量导出必须指定时间范围）。');
      return;
    }
    try {
      setExportJobsError(null);
      await historyApi.createExportJob({
        start_time: startTime,
        end_time: endTime,
        q: exportKeyword.trim() || null,
        role: exportRole || null,
        session_name: exportScope === 'session' ? selectedSession : null,
      });
      await loadExportJobs();
    } catch (e: any) {
      setExportJobsError(e?.message || '创建导出任务失败');
    }
  };

  const downloadExportJob = async (jobId: string) => {
    try {
      const blob = await historyApi.downloadExportJobCsv(jobId);
      downloadBlob(blob, `chat_export_${jobId}.csv`);
    } catch (e: any) {
      setExportJobsError(e?.message || '下载失败');
    }
  };

  const toggleTranslationEnabled = () => {
    setTranslationEnabled((v) => !v);
    setTranslationErrorByMessageId({});
  };

  const toggleTranslationVisible = (messageId: string) => {
    setTranslationVisibleByMessageId((prev) => ({ ...prev, [messageId]: !prev[messageId] }));
  };

  const translateMessage = async (message: HistoryMessageItem) => {
    if (!translationEnabled) return;
    const key = message.message_id;
    if (translationByMessageId[key]) {
      setTranslationVisibleByMessageId((prev) => ({ ...prev, [key]: true }));
      return;
    }

    const text = message.content || '';
    if (text.trim().length < 1) return;

    setTranslationLoadingByMessageId((prev) => ({ ...prev, [key]: true }));
    setTranslationErrorByMessageId((prev) => ({ ...prev, [key]: '' }));
    try {
      const result = await historyApi.translateToZh({ text });
      const translated = (result?.translated_text || '').trim();
      if (!translated) {
        throw new Error('empty translation');
      }
      setTranslationByMessageId((prev) => ({ ...prev, [key]: translated }));
      setTranslationVisibleByMessageId((prev) => ({ ...prev, [key]: true }));
    } catch (e: any) {
      setTranslationErrorByMessageId((prev) => ({ ...prev, [key]: e?.message || '翻译失败' }));
    } finally {
      setTranslationLoadingByMessageId((prev) => ({ ...prev, [key]: false }));
    }
  };

  const showSearchResults = messageSearchQuery.trim().length >= 2 && (searchResults.length > 0 || searchTotal > 0);

  return (
    <div className="h-full bg-slate-50/30 p-8 overflow-hidden font-sans">
      <div className="h-full max-w-7xl mx-auto flex flex-col gap-6">
        <header className="flex items-end justify-between">
          <div>
            <h1 className="text-3xl font-brand font-black text-slate-800 tracking-tighter uppercase">聊天记录</h1>
            <p className="text-slate-400 text-xs font-bold uppercase tracking-[0.4em] mt-2">
              按 <span className="text-slate-600">session_name</span> 聚合 · 搜索 · 导出 CSV
            </p>
          </div>
          <button
            onClick={loadSessions}
            className="px-4 py-2 bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-all text-slate-700 font-bold text-xs uppercase tracking-widest flex items-center gap-2"
            disabled={isLoadingSessions}
          >
            <RefreshCw size={14} className={isLoadingSessions ? 'animate-spin' : ''} />
            刷新
          </button>
        </header>

        <div className="grid grid-cols-12 gap-6 flex-1 min-h-0">
          {/* Left: session list */}
          <div className="col-span-12 md:col-span-4 bg-white rounded-[32px] border border-slate-100 shadow-[0_12px_32px_rgba(0,0,0,0.02)] flex flex-col min-h-0">
            <div className="p-6 border-b border-slate-100">
              <div className="grid grid-cols-1 gap-3">
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <div className="flex items-center gap-2 flex-wrap">
                    <button
                      className={`px-3 py-2 rounded-xl border text-xs font-black ${timePreset === 'today' ? 'bg-black text-white border-black' : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'}`}
                      onClick={() => {
                        const now = new Date();
                        const start = new Date(now);
                        start.setHours(0, 0, 0, 0);
                        setTimePreset('today');
                        setPage(1);
                        setStartTimeLocal(toDatetimeLocal(start.getTime() / 1000));
                        setEndTimeLocal(toDatetimeLocal(now.getTime() / 1000));
                      }}
                    >
                      今天
                    </button>
                    <button
                      className={`px-3 py-2 rounded-xl border text-xs font-black ${timePreset === 'yesterday' ? 'bg-black text-white border-black' : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'}`}
                      onClick={() => {
                        const now = new Date();
                        const start = new Date(now);
                        start.setDate(start.getDate() - 1);
                        start.setHours(0, 0, 0, 0);
                        const end = new Date(start);
                        end.setHours(23, 59, 0, 0);
                        setTimePreset('yesterday');
                        setPage(1);
                        setStartTimeLocal(toDatetimeLocal(start.getTime() / 1000));
                        setEndTimeLocal(toDatetimeLocal(end.getTime() / 1000));
                      }}
                    >
                      昨天
                    </button>
                    <button
                      className={`px-3 py-2 rounded-xl border text-xs font-black ${timePreset === '7d' ? 'bg-black text-white border-black' : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'}`}
                      onClick={() => {
                        const now = new Date();
                        const start = new Date(now);
                        start.setDate(start.getDate() - 6);
                        start.setHours(0, 0, 0, 0);
                        setTimePreset('7d');
                        setPage(1);
                        setStartTimeLocal(toDatetimeLocal(start.getTime() / 1000));
                        setEndTimeLocal(toDatetimeLocal(now.getTime() / 1000));
                      }}
                    >
                      近7天
                    </button>
                    <button
                      className={`px-3 py-2 rounded-xl border text-xs font-black ${timePreset === 'custom' ? 'bg-black text-white border-black' : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'}`}
                      onClick={() => setTimePreset('custom')}
                    >
                      自定义
                    </button>
                  </div>

                  <button
                    onClick={openExportCenter}
                    className="px-3 py-2 rounded-xl border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 text-xs font-black uppercase tracking-widest flex items-center gap-2"
                    title="面向运营/质检：按时间范围 + 关键词/角色/会话范围批量导出"
                  >
                    <FileDown size={14} />
                    批量导出
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 mb-1">开始时间</label>
                    <input
                      type="datetime-local"
                      value={startTimeLocal}
                      onChange={(e) => {
                        setPage(1);
                        setStartTimeLocal(e.target.value);
                        setTimePreset('custom');
                      }}
                      className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-700"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 mb-1">结束时间</label>
                    <input
                      type="datetime-local"
                      value={endTimeLocal}
                      onChange={(e) => {
                        setPage(1);
                        setEndTimeLocal(e.target.value);
                        setTimePreset('custom');
                      }}
                      className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-700"
                    />
                  </div>
                </div>

                <div className="relative">
                  <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    value={sessionKeyword}
                    onChange={(e) => {
                      setPage(1);
                      setSelectedSession(null);
                      setSessionKeyword(e.target.value);
                    }}
                    placeholder="会话关键词筛选（命中则显示会话）"
                    className="w-full pl-9 pr-10 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-700"
                  />
                  {sessionKeyword.trim().length > 0 && (
                    <button
                      onClick={() => {
                        setSessionKeyword('');
                        setPage(1);
                      }}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded-lg hover:bg-slate-100 text-slate-400"
                      title="清空"
                    >
                      <X size={14} />
                    </button>
                  )}
                </div>

                <div className="flex items-center justify-between">
                  <div className="text-[11px] font-bold text-slate-500">
                    总数: <span className="text-slate-700">{sessionsTotal}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setCompactMode((v) => !v)}
                      className={`px-3 py-2 rounded-xl border text-xs font-black ${
                        compactMode ? 'bg-black text-white border-black' : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                      }`}
                      title="紧凑模式适合高频翻查"
                    >
                      紧凑
                    </button>
                    <select
                      value={pageSize}
                      onChange={(e) => {
                        setPage(1);
                        setPageSize(parseInt(e.target.value, 10));
                      }}
                      className="px-3 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-700"
                    >
                      {[50, 100, 200].map((n) => (
                        <option key={n} value={n}>
                          {n}/页
                        </option>
                      ))}
                    </select>
                    <div className="flex items-center gap-1">
                      <button
                        className="px-3 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-700 disabled:opacity-50"
                        disabled={page <= 1}
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                      >
                        上一页
                      </button>
                      <button
                        className="px-3 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-700 disabled:opacity-50"
                        disabled={page * pageSize >= sessionsTotal}
                        onClick={() => setPage((p) => p + 1)}
                      >
                        下一页
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {sessionsError && <div className="mt-3 text-xs font-bold text-red-600">{sessionsError}</div>}
            </div>

            <div className="flex-1 overflow-y-auto overflow-x-hidden p-3 space-y-2">
              {sessions.map((s) => {
                const isActive = selectedSession === s.session_name;
                const displayName = (s as any).meta?.display_name as string | undefined;
                const title = (displayName && displayName.trim()) || s.session_name;
                const preview = ((s as any).last_match_preview || s.last_message_preview || '').trim();
                const matchCount = (s as any).match_count as number | undefined;
                return (
                  <button
                    key={s.session_name}
                    onClick={() => setSelectedSession(s.session_name)}
                    className={`w-full text-left ${compactMode ? 'p-3' : 'p-4'} rounded-2xl border transition-all ${
                      isActive ? 'border-fiido bg-fiido/5 shadow-sm' : 'border-slate-100 hover:border-slate-200 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <div className="text-sm font-black text-slate-800 truncate">{title}</div>
                        {!compactMode && <div className="text-[10px] font-bold text-slate-400 mt-1 truncate">会话ID: {s.session_name}</div>}
                        <div className="text-[11px] font-bold text-slate-400 mt-1">
                          {typeof matchCount === 'number'
                            ? `命中 ${matchCount} 条 · 最近命中 ${formatTime((s as any).last_match_at)}`
                            : `${s.message_count} 条消息 · 最近 ${formatTime(s.last_message_at)}`}
                        </div>
                        {!compactMode && preview && <div className="text-[11px] font-bold text-slate-600 mt-2 line-clamp-2">{preview}</div>}
                      </div>
                    </div>
                  </button>
                );
              })}
              {!isLoadingSessions && sessions.length === 0 && (
                <div className="p-6 text-center text-slate-400 text-xs font-bold">暂无会话</div>
              )}
            </div>
          </div>

          {/* Right: session detail + search + export */}
          <div className="col-span-12 md:col-span-8 bg-white rounded-[32px] border border-slate-100 shadow-[0_12px_32px_rgba(0,0,0,0.02)] flex flex-col min-h-0">
            <div className="p-6 border-b border-slate-100 flex flex-col gap-4">
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <div className="text-sm font-black text-slate-800 truncate">{selectedSession ? selectedSessionTitle : '请选择一个会话'}</div>
                  {selectedSession && selectedSessionDisplayName && selectedSessionDisplayName.trim() && (
                    <div className="text-[11px] font-bold text-slate-400 mt-1 truncate">会话ID: {selectedSession}</div>
                  )}
                  <div className="text-[11px] font-bold text-slate-400 mt-1">
                    消息数: <span className="text-slate-700">{messagesTotal}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={openMetaEditor}
                    disabled={!selectedSession}
                    className="px-4 py-2 bg-white text-slate-700 rounded-2xl font-black text-xs uppercase tracking-widest border border-slate-200 hover:bg-slate-50 disabled:opacity-50 flex items-center gap-2"
                    title="为会话设置展示名/备注/标签（仅用于工作台展示）"
                  >
                    <Pencil size={14} />
                    会话备注
                  </button>
                  <button
                    onClick={toggleTranslationEnabled}
                    className={`px-4 py-2 rounded-2xl font-black text-xs uppercase tracking-widest border transition-all ${
                      translationEnabled ? 'bg-black text-white border-black' : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                    }`}
                    title="默认关闭；开启后可对单条消息点击翻译（仅展示，不入库）"
                  >
                    {translationEnabled ? '翻译：开' : '翻译：关'}
                  </button>
                  <button
                    onClick={exportCsv}
                    disabled={!selectedSession}
                    className="px-4 py-2 bg-fiido text-white rounded-2xl font-black text-xs uppercase tracking-widest hover:opacity-90 disabled:opacity-50 flex items-center gap-2"
                  >
                    <Download size={14} />
                    导出 CSV
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-12 gap-3">
                <div className="col-span-12 md:col-span-7">
                  <div className="relative">
                    <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      value={messageSearchQuery}
                      onChange={(e) => setMessageSearchQuery(e.target.value)}
                      placeholder={messageSearchScope === 'session' ? '关键词搜索（当前会话）' : '关键词搜索（全部会话）'}
                      className="w-full pl-9 pr-3 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-700"
                    />
                  </div>
                </div>
                <div className="col-span-6 md:col-span-2">
                  <select
                    value={messageSearchScope}
                    onChange={(e) => setMessageSearchScope(e.target.value as 'session' | 'all')}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-700"
                  >
                    <option value="session">当前会话</option>
                    <option value="all">全部会话</option>
                  </select>
                </div>
                <div className="col-span-6 md:col-span-2">
                  <select
                    value={messageSearchRole}
                    onChange={(e) => setMessageSearchRole((e.target.value || '') as HistoryRole | '')}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-700"
                  >
                    <option value="">全部角色</option>
                    <option value="user">用户</option>
                    <option value="assistant">AI</option>
                    <option value="agent">坐席</option>
                  </select>
                </div>
                <div className="col-span-12 md:col-span-1">
                  <button
                    onClick={runSearch}
                    disabled={isSearching || (messageSearchScope === 'session' && !selectedSession)}
                    className="w-full px-4 py-2 bg-black text-white rounded-xl font-black text-xs uppercase tracking-widest hover:opacity-90 disabled:opacity-50"
                  >
                    {isSearching ? '搜索中…' : '搜索'}
                  </button>
                </div>
              </div>
              {searchError && <div className="text-xs font-bold text-red-600">{searchError}</div>}
            </div>

            {messagesError && <div className="px-6 pt-4 text-xs font-bold text-red-600">{messagesError}</div>}

            <div className="flex-1 overflow-y-auto overflow-x-hidden p-6 space-y-3">
              {showSearchResults ? (
                <>
                  <div className="text-[11px] font-bold text-slate-400">
                    搜索结果: <span className="text-slate-700">{searchTotal}</span>
                  </div>
                  {searchResults.map((m) => (
                    <div key={m.message_id} className="w-full overflow-hidden p-4 rounded-2xl border border-slate-100 bg-slate-50">
                      <div className="flex items-center justify-between gap-3">
                        <span className={`px-2 py-1 rounded-lg border text-[10px] font-black uppercase tracking-widest ${roleBadgeStyles[m.role]}`}>
                          {roleLabels[m.role]}
                        </span>
                        <span className="text-[11px] font-bold text-slate-400">{formatTime(m.created_at)}</span>
                      </div>
                      <div className="mt-2 text-sm font-bold text-slate-700 whitespace-pre-wrap break-words">{m.content}</div>
                    </div>
                  ))}
                  {searchResults.length === 0 && <div className="text-xs font-bold text-slate-400">无匹配结果</div>}
                </>
              ) : (
                <>
                  {isLoadingMessages ? (
                    <div className="text-center text-slate-400 text-xs font-bold">加载中…</div>
                  ) : (
                    <>
                      {canLoadOlder && (
                        <div className="flex justify-center">
                          <button
                            onClick={loadOlderMessages}
                            className="px-4 py-2 rounded-2xl border border-slate-200 text-xs font-black text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                            disabled={isLoadingMessages}
                          >
                            {isLoadingMessages ? '加载中…' : '加载更早消息'}
                          </button>
                        </div>
                      )}
                      {messages.map((m) => (
                        <div key={m.message_id} className={`w-full overflow-hidden ${compactMode ? 'p-3' : 'p-4'} rounded-2xl border border-slate-100`}>
                          <div className="flex flex-wrap items-start justify-between gap-3">
                            <span className={`px-2 py-1 rounded-lg border text-[10px] font-black uppercase tracking-widest ${roleBadgeStyles[m.role]}`}>
                              {roleLabels[m.role]}
                            </span>
                            <div className="flex flex-wrap items-center justify-end gap-2">
                              {translationEnabled && (
                                <button
                                  onClick={() => translateMessage(m)}
                                  className="px-3 py-1.5 rounded-xl border border-slate-200 text-[10px] font-black text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                                  disabled={translationLoadingByMessageId[m.message_id]}
                                >
                                  {translationLoadingByMessageId[m.message_id] ? '翻译中…' : '翻译为中文'}
                                </button>
                              )}
                              {translationEnabled && translationByMessageId[m.message_id] && (
                                <button
                                  onClick={() => toggleTranslationVisible(m.message_id)}
                                  className="px-3 py-1.5 rounded-xl border border-slate-200 text-[10px] font-black text-slate-700 hover:bg-slate-50"
                                >
                                  {translationVisibleByMessageId[m.message_id] ? '隐藏译文' : '显示译文'}
                                </button>
                              )}
                              <span className="text-[11px] font-bold text-slate-400">{formatTime(m.created_at)}</span>
                            </div>
                          </div>
                          <div className={`mt-2 ${compactMode ? 'text-[13px]' : 'text-sm'} font-bold text-slate-700 whitespace-pre-wrap break-words`}>
                            {m.content}
                          </div>
                          {m.agent_name && (
                            <div className="mt-2 text-[11px] font-bold text-slate-400">坐席: {m.agent_name}</div>
                          )}

                          {translationEnabled && translationErrorByMessageId[m.message_id] && (
                            <div className="mt-2 text-[11px] font-bold text-red-600">{translationErrorByMessageId[m.message_id]}</div>
                          )}
                          {translationEnabled && translationByMessageId[m.message_id] && translationVisibleByMessageId[m.message_id] && (
                            <div className="mt-3 p-3 rounded-2xl border border-slate-100 bg-slate-50">
                              <div className="text-[10px] font-black uppercase tracking-widest text-slate-400">译文</div>
                              <div className="mt-1 text-sm font-bold text-slate-800 whitespace-pre-wrap break-words">
                                {translationByMessageId[m.message_id]}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                      {messages.length === 0 && (
                        <div className="text-center text-slate-400 text-xs font-bold">暂无消息</div>
                      )}
                    </>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {showMetaEditor && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-6">
          <div className="w-full max-w-xl bg-white rounded-[32px] border border-slate-100 shadow-2xl p-6">
            <div className="flex items-center justify-between">
              <div className="text-sm font-black text-slate-800">会话备注与标签</div>
              <button onClick={() => setShowMetaEditor(false)} className="p-1 rounded-lg hover:bg-slate-100 text-slate-400">
                <X size={18} />
              </button>
            </div>

            <div className="mt-4 space-y-3">
              <div>
                <label className="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 mb-1">展示名（可选）</label>
                <input
                  value={metaDisplayName}
                  onChange={(e) => setMetaDisplayName(e.target.value)}
                  placeholder="例如：John（US）/ Order#12345 / 电池投诉"
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-700"
                />
              </div>
              <div>
                <label className="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 mb-1">备注（可选）</label>
                <textarea
                  value={metaNote}
                  onChange={(e) => setMetaNote(e.target.value)}
                  placeholder="给主管/同事看的备注，不会影响用户侧"
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-700 min-h-[96px]"
                />
              </div>
              <div>
                <label className="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 mb-1">标签（可选）</label>
                <input
                  value={metaTags}
                  onChange={(e) => setMetaTags(e.target.value)}
                  placeholder="逗号分隔：refund, battery, complaint；或粘贴 JSON"
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-700"
                />
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-2">
              <button
                onClick={() => setShowMetaEditor(false)}
                className="px-4 py-2 rounded-2xl border border-slate-200 text-xs font-black text-slate-700 hover:bg-slate-50"
                disabled={metaSaving}
              >
                取消
              </button>
              <button
                onClick={saveMeta}
                className="px-4 py-2 rounded-2xl bg-fiido text-white text-xs font-black uppercase tracking-widest hover:opacity-90 disabled:opacity-50"
                disabled={metaSaving}
              >
                {metaSaving ? '保存中…' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}

      {showExportPanel && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-6">
          <div className="w-full max-w-3xl bg-white rounded-[32px] border border-slate-100 shadow-2xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-black text-slate-800">批量导出中心</div>
                <div className="text-[11px] font-bold text-slate-400 mt-1">
                  使用左侧时间范围：{startTime ? formatTime(startTime) : '--'} → {endTime ? formatTime(endTime) : '--'}
                </div>
              </div>
              <button onClick={() => setShowExportPanel(false)} className="p-1 rounded-lg hover:bg-slate-100 text-slate-400">
                <X size={18} />
              </button>
            </div>

            <div className="mt-4 grid grid-cols-12 gap-3">
              <div className="col-span-12 md:col-span-6">
                <label className="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 mb-1">关键词（可选）</label>
                <input
                  value={exportKeyword}
                  onChange={(e) => setExportKeyword(e.target.value)}
                  placeholder="支持多词（FTS）"
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-700"
                />
              </div>
              <div className="col-span-6 md:col-span-3">
                <label className="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 mb-1">范围</label>
                <select
                  value={exportScope}
                  onChange={(e) => setExportScope(e.target.value as 'session' | 'all')}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-700"
                >
                  <option value="all">全部会话</option>
                  <option value="session" disabled={!selectedSession}>
                    当前会话
                  </option>
                </select>
              </div>
              <div className="col-span-6 md:col-span-3">
                <label className="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 mb-1">角色</label>
                <select
                  value={exportRole}
                  onChange={(e) => setExportRole((e.target.value || '') as HistoryRole | '')}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-700"
                >
                  <option value="">全部角色</option>
                  <option value="user">用户</option>
                  <option value="assistant">AI</option>
                  <option value="agent">坐席</option>
                </select>
              </div>
              <div className="col-span-12 flex items-center justify-between gap-3">
                <div className="text-[11px] font-bold text-slate-500">
                  说明：运营常用“今天/昨天/近7天 + 关键词”导出；后端默认限制最大 7 天、最大 200k 行。
                </div>
                <button
                  onClick={createBatchExportJob}
                  className="px-4 py-2 bg-black text-white rounded-xl font-black text-xs uppercase tracking-widest hover:opacity-90"
                >
                  生成导出任务
                </button>
              </div>
            </div>

            {exportJobsError && <div className="mt-2 text-xs font-bold text-red-600">{exportJobsError}</div>}

            <div className="mt-5">
              <div className="flex items-center justify-between">
                <div className="text-[11px] font-black text-slate-600">最近任务</div>
                <button
                  onClick={loadExportJobs}
                  className="px-3 py-1.5 rounded-xl border border-slate-200 text-[10px] font-black text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                  disabled={exportJobsLoading}
                >
                  {exportJobsLoading ? '刷新中…' : '刷新列表'}
                </button>
              </div>
              <div className="mt-2 space-y-2 max-h-72 overflow-y-auto">
                {exportJobs.map((j) => (
                  <div key={j.job_id} className="p-3 rounded-xl border border-slate-100 bg-white flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <div className="text-xs font-black text-slate-800 truncate">#{j.job_id.slice(0, 8)}</div>
                      <div className="text-[11px] font-bold text-slate-400 mt-1">
                        状态: {exportStatusLabels[j.status] || j.status} · 行数: {j.row_count ?? '--'} · 创建 {formatTime(j.created_at)}
                      </div>
                      {j.error && <div className="text-[11px] font-bold text-red-600 mt-1 truncate">{j.error}</div>}
                    </div>
                    <div className="flex items-center gap-2">
                      {j.status === 'done' && (
                        <button
                          onClick={() => downloadExportJob(j.job_id)}
                          className="px-3 py-2 bg-fiido text-white rounded-xl font-black text-[10px] uppercase tracking-widest hover:opacity-90"
                        >
                          下载
                        </button>
                      )}
                    </div>
                  </div>
                ))}
                {!exportJobsLoading && exportJobs.length === 0 && <div className="text-xs font-bold text-slate-400">暂无导出任务</div>}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatHistoryView;
