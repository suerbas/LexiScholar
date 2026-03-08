import { useTheme } from '../context/ThemeContext';
import { cn } from '../lib/utils';
import { motion } from 'framer-motion';
import { 
  MessageSquare, 
  Highlighter, 
  X,
  Maximize2,
  Minimize2,
  Bot,
  Sparkles,
  Send,
  Search,
  Tag,
  Filter,
  FileText,
  PieChart,
  MoreVertical,
  Type,
  Download,
  Share2,
  Printer,
  Save,
  Undo,
  Redo,
  ZoomIn,
  ZoomOut,
  Grid,
  List,
  Settings,
  HelpCircle,
  Bold,
  Italic,
  Underline
} from 'lucide-react';
import { sampleText } from '../data/mockData';
import { VisualizationPanel } from './VisualizationPanel';
import { useState, useEffect } from 'react';
import { Button } from './ui/Button';

export function Workspace({ activeModule = 'data' }: { activeModule?: string }) {
  const { currentTheme } = useTheme();
  const { colors, shape, typography, layout } = currentTheme;
  const [ribbonTab, setRibbonTab] = useState<'home' | 'view' | 'analysis' | 'coding'>('home');

  const isProfessional = currentTheme.id === 'professional';

  useEffect(() => {
    if (activeModule === 'analysis') {
      setRibbonTab('analysis');
    } else {
      setRibbonTab('home');
    }
  }, [activeModule]);

  return (
    <div className={cn(
      "flex-1 overflow-hidden flex flex-col h-full relative",
      isProfessional ? "bg-[#F0F2F5]" : "bg-slate-100/50 dark:bg-black/20 p-3 gap-3"
    )}>
      
      {/* PROFESSIONAL RIBBON HEADER */}
      {isProfessional && (
        <div className="bg-white border-b border-slate-300 flex flex-col shrink-0">
          {/* Title Bar */}
          <div className="h-8 flex items-center justify-between px-3 bg-[#1D4ED8] text-white">
            <div className="flex items-center gap-2">
              <FileText size={14} className="opacity-80" />
              <span className="text-xs font-semibold tracking-wide">LexiScholar Pro - [K13 - Mülakat Transkripti.docx]</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-[10px] opacity-70 mr-2">Dr. Yılmaz (Admin)</span>
              <button className="p-1 hover:bg-white/10 rounded"><Minimize2 size={12} /></button>
              <button className="p-1 hover:bg-white/10 rounded"><Maximize2 size={12} /></button>
              <button className="p-1 hover:bg-red-500 rounded"><X size={12} /></button>
            </div>
          </div>

          {/* Ribbon Tabs */}
          <div className="flex px-1 pt-1 border-b border-slate-200 bg-slate-50">
            {['home', 'view', 'analysis', 'coding'].map((tab) => (
              <button
                key={tab}
                onClick={() => setRibbonTab(tab as any)}
                className={cn(
                  "px-4 py-1.5 text-xs font-medium rounded-t-sm transition-colors border-t border-x border-transparent -mb-px",
                  ribbonTab === tab 
                    ? "bg-white text-blue-700 border-slate-300 border-b-white z-10" 
                    : "text-slate-600 hover:bg-slate-100"
                )}
              >
                {tab === 'home' && 'Giriş'}
                {tab === 'view' && 'Görünüm'}
                {tab === 'analysis' && 'Analiz'}
                {tab === 'coding' && 'Kodlama'}
              </button>
            ))}
          </div>

          {/* Ribbon Toolbar */}
          <div className="h-24 bg-white flex items-center px-2 py-1 gap-2 overflow-x-auto shadow-sm">
            {ribbonTab === 'home' && (
              <>
                {/* Group: Clipboard */}
                <div className="flex flex-col h-full px-2 border-r border-slate-200 pr-2">
                  <div className="flex gap-1 mb-1">
                    <button className="flex flex-col items-center justify-center p-2 hover:bg-slate-100 rounded text-slate-700 w-12">
                      <Save size={20} className="mb-1 text-blue-600" />
                      <span className="text-[10px]">Kaydet</span>
                    </button>
                  </div>
                  <div className="flex gap-1 justify-center">
                    <button className="p-1 hover:bg-slate-100 rounded" title="Geri Al"><Undo size={14} /></button>
                    <button className="p-1 hover:bg-slate-100 rounded" title="Yinele"><Redo size={14} /></button>
                  </div>
                  <span className="mt-auto text-[10px] text-slate-400 text-center w-full">Dosya</span>
                </div>

                {/* Group: Font */}
                <div className="flex flex-col h-full px-2 border-r border-slate-200 pr-2">
                  <div className="flex items-center gap-1 mb-1">
                    <select className="text-xs border border-slate-300 rounded px-1 py-0.5 w-24">
                      <option>Calibri</option>
                      <option>Arial</option>
                    </select>
                    <select className="text-xs border border-slate-300 rounded px-1 py-0.5 w-12">
                      <option>11</option>
                      <option>12</option>
                    </select>
                  </div>
                  <div className="flex gap-0.5">
                    <button className="p-1 hover:bg-slate-100 rounded"><Bold size={14} /></button>
                    <button className="p-1 hover:bg-slate-100 rounded"><Italic size={14} /></button>
                    <button className="p-1 hover:bg-slate-100 rounded"><Underline size={14} /></button>
                    <div className="w-px h-4 bg-slate-300 mx-1" />
                    <button className="p-1 hover:bg-slate-100 rounded"><Highlighter size={14} className="text-yellow-500" /></button>
                    <button className="p-1 hover:bg-slate-100 rounded"><Type size={14} className="text-red-500" /></button>
                  </div>
                  <span className="mt-auto text-[10px] text-slate-400 text-center w-full">Yazı Tipi</span>
                </div>

                {/* Group: Coding */}
                <div className="flex flex-col h-full px-2 border-r border-slate-200 pr-2">
                  <div className="flex gap-1">
                    <button className="flex flex-col items-center justify-center p-2 hover:bg-slate-100 rounded text-slate-700 w-16">
                      <Tag size={20} className="mb-1 text-purple-600" />
                      <span className="text-[10px]">Kodla</span>
                    </button>
                    <button className="flex flex-col items-center justify-center p-2 hover:bg-slate-100 rounded text-slate-700 w-16">
                      <MessageSquare size={20} className="mb-1 text-green-600" />
                      <span className="text-[10px]">Not Ekle</span>
                    </button>
                  </div>
                  <span className="mt-auto text-[10px] text-slate-400 text-center w-full">Kodlama</span>
                </div>
              </>
            )}
            
            {ribbonTab === 'view' && (
               <div className="flex flex-col h-full px-2 border-r border-slate-200 pr-2">
                 <div className="flex gap-1">
                   <button className="flex flex-col items-center justify-center p-2 hover:bg-slate-100 rounded text-slate-700 w-14">
                     <ZoomIn size={20} className="mb-1" />
                     <span className="text-[10px]">Yakınlaş</span>
                   </button>
                   <button className="flex flex-col items-center justify-center p-2 hover:bg-slate-100 rounded text-slate-700 w-14">
                     <ZoomOut size={20} className="mb-1" />
                     <span className="text-[10px]">Uzaklaş</span>
                   </button>
                 </div>
                 <span className="mt-auto text-[10px] text-slate-400 text-center w-full">Yakınlaştırma</span>
               </div>
            )}
          </div>
        </div>
      )}

      {/* MAIN CONTENT SPLIT */}
      <div className={cn(
        "flex-1 flex overflow-hidden",
        isProfessional ? "" : "gap-3"
      )}>
        
        {activeModule === 'analysis' ? (
          <VisualizationPanel />
        ) : (
          <>
            {/* Center Panel: Document */}
            <motion.div 
              layout
          className={cn(
            "flex-1 flex flex-col overflow-hidden relative min-w-0 bg-white dark:bg-zinc-900",
            isProfessional ? "border-r border-slate-300" : "shadow-sm rounded-xl border border-slate-200"
          )}
        >
          {!isProfessional && (
            /* Standard Header for other themes */
            <div className="flex flex-col border-b border-slate-200 dark:border-zinc-800">
              {/* ... (Keep existing header code for non-pro themes) ... */}
              <div className="flex items-center justify-between px-4 py-2 bg-slate-50 dark:bg-zinc-900/50">
                 {/* ... */}
              </div>
            </div>
          )}

          {/* Document Content */}
          <div className={cn(
            "flex-1 overflow-y-auto w-full bg-white dark:bg-zinc-900",
            isProfessional ? "p-8" : "p-12",
            typography.fontSerif,
            colors.text
          )}>
            <div className={cn(
              "max-w-3xl mx-auto min-h-full bg-white dark:bg-zinc-900",
              isProfessional ? "" : "shadow-sm border border-slate-100 p-12"
            )}>
              <h1 className="text-2xl font-bold mb-6 text-slate-900 dark:text-white pb-2 border-b">Mülakat K13: Eğitimde Fırsat Eşitliği</h1>
              <div className="whitespace-pre-wrap text-base text-slate-800 dark:text-slate-300 leading-relaxed">
                {sampleText.split('\n\n').map((para, i) => (
                  <p key={i} className="mb-4 relative group pl-4 border-l-2 border-transparent hover:border-blue-300 transition-colors">
                    {para}
                    <span className="absolute -left-8 top-1 text-[10px] font-mono text-slate-400 opacity-0 group-hover:opacity-100 select-none">
                      {String(i + 1).padStart(2, '0')}
                    </span>
                  </p>
                ))}
              </div>
            </div>
          </div>
        </motion.div>

        {/* Right Panel: Coding & AI */}
        <div className={cn(
          "flex flex-col shrink-0",
          isProfessional ? "w-72 bg-[#F9FAFB] border-l border-slate-300" : "w-80 gap-3"
        )}>
          
          {/* Retrieved Segments / Active Codes */}
          <div className={cn(
            "flex-1 flex flex-col overflow-hidden bg-white dark:bg-zinc-900",
            isProfessional ? "border-b border-slate-300" : "shadow-sm rounded-xl border border-slate-200"
          )}>
            <div className={cn(
              "flex items-center justify-between px-3 py-2 border-b",
              isProfessional ? "bg-[#F3F4F6] border-slate-300 h-8" : "bg-white border-slate-100 p-3"
            )}>
              <span className={cn("font-semibold text-xs uppercase tracking-wider", isProfessional ? "text-slate-700" : "")}>
                Aktif Kodlar
              </span>
              <Button variant="ghost" size="icon" className="h-5 w-5"><Filter size={12} /></Button>
            </div>

            <div className="flex-1 overflow-y-auto p-2 space-y-2">
              <div className="p-2 border border-slate-200 rounded bg-slate-50 hover:border-blue-300 transition-colors cursor-pointer">
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-2 h-2 rounded-full bg-red-500" />
                  <span className="font-bold text-xs text-slate-700">Dil Sorunu</span>
                  <span className="ml-auto text-[9px] text-slate-500 bg-white px-1 rounded border">Ref: 3</span>
                </div>
                <p className="text-[10px] text-slate-500 italic line-clamp-2">"...akademik dili anlamakta zorlanıyorlar..."</p>
              </div>
              
              <div className="p-2 border border-slate-200 rounded bg-slate-50 hover:border-yellow-300 transition-colors cursor-pointer">
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-2 h-2 rounded-full bg-yellow-500" />
                  <span className="font-bold text-xs text-slate-700">Ekonomik Sıkıntılar</span>
                  <span className="ml-auto text-[9px] text-slate-500 bg-white px-1 rounded border">Ref: 5</span>
                </div>
                <p className="text-[10px] text-slate-500 italic line-clamp-2">"...okuldan sonra çalışmak zorunda..."</p>
              </div>
            </div>
          </div>

          {/* AI Chat Panel */}
          <div className={cn(
            "flex flex-col overflow-hidden bg-white dark:bg-zinc-900 relative",
            isProfessional ? "h-1/2" : "h-[45%] shadow-sm rounded-xl border border-slate-200"
          )}>
            <div className={cn(
              "flex items-center justify-between px-3 py-2 border-b",
              isProfessional ? "bg-[#F3F4F6] border-slate-300 h-8" : "bg-gradient-to-r from-blue-50 to-purple-50 p-3"
            )}>
              <div className="flex items-center gap-2">
                <Bot size={14} className="text-blue-600" />
                <span className={cn("font-semibold text-xs", isProfessional ? "text-slate-700 uppercase tracking-wider" : "text-blue-700")}>
                  AI Asistanı
                </span>
              </div>
            </div>
            
            <div className="flex-1 p-3 flex flex-col gap-3 overflow-y-auto bg-slate-50">
              <div className="flex gap-2">
                <div className="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center shrink-0 text-white shadow-sm">
                  <Bot size={12} />
                </div>
                <div className="p-2 text-xs bg-white rounded-lg rounded-tl-none shadow-sm border border-slate-200 text-slate-700">
                  <p><strong>'K13'</strong> belgesini analiz ettim. Temel temalar: <em>Dil Bariyeri</em> ve <em>Ekonomik Zorluklar</em>.</p>
                </div>
              </div>
            </div>

            <div className="p-2 bg-white border-t border-slate-200">
              <div className="flex items-center gap-2 px-2 py-1.5 bg-slate-50 rounded border border-slate-200">
                <input 
                  type="text" 
                  placeholder="Soru sor..." 
                  className="flex-1 bg-transparent border-none outline-none text-xs text-slate-700"
                />
                <Button size="icon" className="h-6 w-6 rounded bg-blue-600 text-white">
                  <Send size={10} />
                </Button>
              </div>
            </div>
          </div>

        </div>
          </>
        )}
      </div>
    </div>
  );
}
