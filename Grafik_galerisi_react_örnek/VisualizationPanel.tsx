import { useState, useRef } from 'react';
import { cn } from '../lib/utils';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, LabelList
} from 'recharts';
import {
  BarChart as BarChartIcon,
  PieChart as PieChartIcon,
  Download,
  Settings2,
  AlignLeft,
  Circle,
  LayoutTemplate
} from 'lucide-react';

const mockData = {
  codes: [
    { name: 'Dil Sorunu', value: 45 },
    { name: 'Ekonomik Sıkıntılar', value: 32 },
    { name: 'Kültürel Uyum', value: 28 },
    { name: 'Akademik Başarı', value: 15 },
    { name: 'Sosyal Destek', value: 22 },
  ],
  variables: [
    { name: 'Kadın', value: 18 },
    { name: 'Erkek', value: 12 },
    { name: 'Belirtmek İstemiyor', value: 2 },
  ]
};

const COLORS = ['#1D4ED8', '#047857', '#B45309', '#6D28D9', '#BE123C'];

export function VisualizationPanel() {
  const [chartType, setChartType] = useState<'bar-vertical' | 'bar-horizontal' | 'pie' | 'donut'>('bar-vertical');
  const [dataSource, setDataSource] = useState<'codes' | 'variables'>('codes');
  const [showLegend, setShowLegend] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const chartRef = useRef<HTMLDivElement>(null);

  const data = mockData[dataSource];

  const handleExport = () => {
    const svgElement = chartRef.current?.querySelector('svg');
    if (!svgElement) return;

    const svgData = new XMLSerializer().serializeToString(svgElement);
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();

    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      if (ctx) {
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0);
        const pngFile = canvas.toDataURL('image/png');
        const downloadLink = document.createElement('a');
        downloadLink.download = 'lexischolar_grafik.png';
        downloadLink.href = pngFile;
        downloadLink.click();
      }
    };

    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#F0F2F5]">
      {/* Toolbar */}
      <div className="h-12 bg-white border-b border-slate-300 flex items-center px-2 justify-between shrink-0">
        <div className="flex items-center gap-1">
          <div className="flex bg-slate-100 p-0.5 rounded border border-slate-200">
            <button onClick={() => setChartType('bar-vertical')} className={cn("p-1.5 rounded", chartType === 'bar-vertical' ? "bg-white shadow-sm border border-slate-200" : "hover:bg-slate-200 text-slate-500")} title="Dikey Bar">
              <BarChartIcon size={16} />
            </button>
            <button onClick={() => setChartType('bar-horizontal')} className={cn("p-1.5 rounded", chartType === 'bar-horizontal' ? "bg-white shadow-sm border border-slate-200" : "hover:bg-slate-200 text-slate-500")} title="Yatay Bar">
              <AlignLeft size={16} />
            </button>
            <button onClick={() => setChartType('pie')} className={cn("p-1.5 rounded", chartType === 'pie' ? "bg-white shadow-sm border border-slate-200" : "hover:bg-slate-200 text-slate-500")} title="Pasta Grafik">
              <PieChartIcon size={16} />
            </button>
            <button onClick={() => setChartType('donut')} className={cn("p-1.5 rounded", chartType === 'donut' ? "bg-white shadow-sm border border-slate-200" : "hover:bg-slate-200 text-slate-500")} title="Donut Grafik">
              <Circle size={16} />
            </button>
          </div>
          <div className="w-px h-6 bg-slate-300 mx-2" />
          <button onClick={handleExport} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 rounded border border-transparent hover:border-slate-200">
            <Download size={14} className="text-blue-600" />
            Dışa Aktar
          </button>
        </div>
        <div className="text-xs font-medium text-slate-500 flex items-center gap-2">
          <LayoutTemplate size={14} />
          Grafik Görüntüleyici
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chart Area */}
        <div className="flex-1 p-6 overflow-auto flex items-center justify-center">
          <div ref={chartRef} className="w-full max-w-3xl h-[500px] bg-white border border-slate-300 shadow-sm p-6 flex flex-col">
            <h2 className="text-center font-bold text-slate-800 mb-6 text-lg">
              {dataSource === 'codes' ? 'Kod Frekansları' : 'Belge Değişkenleri Dağılımı'}
            </h2>
            <div className="flex-1 min-h-0">
              <ResponsiveContainer width="100%" height="100%">
                {chartType.includes('bar') ? (
                  <BarChart
                    data={data}
                    layout={chartType === 'bar-horizontal' ? 'vertical' : 'horizontal'}
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                    {chartType === 'bar-horizontal' ? (
                      <>
                        <XAxis type="number" tick={{ fontSize: 12, fill: '#4B5563' }} />
                        <YAxis dataKey="name" type="category" width={120} tick={{ fontSize: 12, fill: '#4B5563' }} />
                      </>
                    ) : (
                      <>
                        <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#4B5563' }} />
                        <YAxis tick={{ fontSize: 12, fill: '#4B5563' }} />
                      </>
                    )}
                    <Tooltip
                      cursor={{ fill: '#F3F4F6' }}
                      contentStyle={{ backgroundColor: '#fff', border: '1px solid #D1D5DB', borderRadius: '4px', fontSize: '12px' }}
                    />
                    {showLegend && <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '20px' }} />}
                    <Bar dataKey="value" name="Frekans" fill="#1D4ED8" radius={chartType === 'bar-horizontal' ? [0, 4, 4, 0] : [4, 4, 0, 0]}>
                      {data.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                      {showLabels && <LabelList dataKey="value" position={chartType === 'bar-horizontal' ? 'right' : 'top'} style={{ fontSize: '12px', fill: '#4B5563' }} />}
                    </Bar>
                  </BarChart>
                ) : (
                  <PieChart>
                    <Pie
                      data={data}
                      cx="50%"
                      cy="50%"
                      innerRadius={chartType === 'donut' ? 80 : 0}
                      outerRadius={150}
                      fill="#8884d8"
                      paddingAngle={chartType === 'donut' ? 2 : 0}
                      dataKey="value"
                      label={showLabels ? ({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)` : false}
                      labelLine={showLabels}
                    >
                      {data.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #D1D5DB', borderRadius: '4px', fontSize: '12px' }} />
                    {showLegend && <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '20px' }} />}
                  </PieChart>
                )}
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Settings Sidebar */}
        <div className="w-64 bg-white border-l border-slate-300 flex flex-col shrink-0">
          <div className="h-10 bg-[#F9FAFB] border-b border-slate-200 flex items-center px-3">
            <Settings2 size={14} className="text-slate-500 mr-2" />
            <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">Grafik Ayarları</span>
          </div>
          
          <div className="p-4 flex flex-col gap-6 overflow-y-auto">
            {/* Data Source */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-900">Veri Kaynağı</label>
              <select 
                value={dataSource}
                onChange={(e) => setDataSource(e.target.value as any)}
                className="w-full text-xs border border-slate-300 rounded p-1.5 outline-none focus:border-blue-500"
              >
                <option value="codes">Kod Frekansları</option>
                <option value="variables">Belge Değişkenleri</option>
              </select>
            </div>

            {/* Chart Type */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-900">Grafik Tipi</label>
              <div className="grid grid-cols-2 gap-2">
                <button onClick={() => setChartType('bar-vertical')} className={cn("flex items-center gap-2 p-2 border rounded text-xs transition-colors", chartType === 'bar-vertical' ? "border-blue-500 bg-blue-50 text-blue-700" : "border-slate-200 hover:bg-slate-50 text-slate-600")}>
                  <BarChartIcon size={14} /> Dikey
                </button>
                <button onClick={() => setChartType('bar-horizontal')} className={cn("flex items-center gap-2 p-2 border rounded text-xs transition-colors", chartType === 'bar-horizontal' ? "border-blue-500 bg-blue-50 text-blue-700" : "border-slate-200 hover:bg-slate-50 text-slate-600")}>
                  <AlignLeft size={14} /> Yatay
                </button>
                <button onClick={() => setChartType('pie')} className={cn("flex items-center gap-2 p-2 border rounded text-xs transition-colors", chartType === 'pie' ? "border-blue-500 bg-blue-50 text-blue-700" : "border-slate-200 hover:bg-slate-50 text-slate-600")}>
                  <PieChartIcon size={14} /> Pasta
                </button>
                <button onClick={() => setChartType('donut')} className={cn("flex items-center gap-2 p-2 border rounded text-xs transition-colors", chartType === 'donut' ? "border-blue-500 bg-blue-50 text-blue-700" : "border-slate-200 hover:bg-slate-50 text-slate-600")}>
                  <Circle size={14} /> Donut
                </button>
              </div>
            </div>

            {/* Options */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-900">Görünüm Seçenekleri</label>
              <div className="space-y-2 mt-2">
                <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={showLabels} 
                    onChange={(e) => setShowLabels(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                  Veri Etiketlerini Göster
                </label>
                <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={showLegend} 
                    onChange={(e) => setShowLegend(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                  Açıklamaları (Legend) Göster
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
