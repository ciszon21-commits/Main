import React, { useState } from 'react';
import { useStore } from '../../store/useStore';
import { Plus, Trash2, Map, Settings, Save, Check } from 'lucide-react';

const ProjectList: React.FC = () => {
  const { 
    localProjects, 
    activeProjectId,
    saveAsProject, 
    loadProject, 
    deleteProject,
    updateProject,
    renameProject 
  } = useStore();

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");

  const handleAddProject = () => {
    const defaultName = `新專案 ${new Date().toLocaleTimeString()}`;
    saveAsProject(defaultName);
  };

  const handleRenameSubmit = (id: string) => {
    if (editName.trim()) {
      renameProject(id, editName.trim());
    }
    setEditingId(null);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between px-2">
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">專案與基地 (Projects)</h2>
        <button 
          onClick={handleAddProject}
          className="p-1 hover:bg-slate-100 rounded-full text-slate-400 hover:text-brand-500 transition-colors"
          title="儲存目前基地為新專案"
        >
          <Plus size={16} />
        </button>
      </div>
      
      <div className="space-y-2 max-h-[60vh] overflow-y-auto pr-1">
        {(!localProjects || localProjects.length === 0) ? (
          <p className="px-3 py-4 text-xs text-slate-400 text-center border-2 border-dashed border-slate-100 rounded-lg">
            尚未儲存任何專案。<br/><br/>點擊右上角的「+」將目前的分析狀態儲存起來。
          </p>
        ) : (
          [...localProjects].sort((a: any, b: any) => {
            if (a.id === activeProjectId) return -1;
            if (b.id === activeProjectId) return 1;
            return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
          }).map((project: any) => {
            const isActive = project.id === activeProjectId;
            
            return (
              <div key={project.id} className="flex flex-col gap-1">
                {/* Active Indicator & Update Button */}
                {isActive && (
                   <div className="flex items-center justify-between px-1 pb-1 animate-in fade-in slide-in-from-top-2">
                      <span className="text-[9px] font-bold text-brand-500 uppercase tracking-widest flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-brand-500 animate-pulse" /> CURRENT ACTIVE
                      </span>
                      <button
                        onClick={(e) => { e.stopPropagation(); updateProject(project.id); }}
                        className="text-[9px] font-bold bg-brand-50 text-brand-600 px-2.5 py-0.5 rounded shadow-sm hover:bg-brand-500 hover:text-white transition-all flex items-center gap-1"
                      >
                        <Save size={10} /> + UPDATE
                      </button>
                   </div>
                )}
                
                <div
                  className={`group w-full flex items-center justify-between px-3 py-2.5 rounded-xl transition-all border cursor-pointer ${
                    isActive 
                      ? 'bg-brand-50/30 border-brand-300 shadow-sm ring-1 ring-brand-500/10' 
                      : 'bg-white border-slate-100 hover:border-brand-200 hover:shadow-md'
                  }`}
                  onClick={() => {
                    if (editingId !== project.id) loadProject(project.id);
                  }}
                >
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${
                      isActive ? 'bg-brand-500 text-white shadow-md shadow-brand-500/20' : 'bg-slate-50 text-slate-400 group-hover:text-brand-500 group-hover:bg-brand-50'
                    }`}>
                      <Map size={15} />
                    </div>
                    
                    <div className="flex flex-col items-start gap-0.5 flex-1 min-w-0">
                      {editingId === project.id ? (
                        <div className="flex items-center w-full gap-1">
                          <input
                            autoFocus
                            type="text"
                            value={editName}
                            onChange={(e) => setEditName(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleRenameSubmit(project.id);
                              if (e.key === 'Escape') setEditingId(null);
                            }}
                            onBlur={() => handleRenameSubmit(project.id)}
                            onClick={e => e.stopPropagation()}
                            className="text-xs font-bold text-slate-700 w-full bg-white border-b-2 border-brand-500 focus:outline-none px-1 py-0.5 rounded-sm shadow-inner"
                          />
                        </div>
                      ) : (
                        <span className="text-xs font-bold text-slate-700 truncate w-full pr-2 text-left">{project.name}</span>
                      )}
                      
                      <span className="text-[9px] text-slate-400">
                        {new Date(project.updatedAt).toLocaleString('zh-TW', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'})}
                      </span>
                    </div>
                  </div>
                  
                  {/* Actions */}
                  {editingId !== project.id && (
                    <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setEditName(project.name);
                          setEditingId(project.id);
                        }}
                        className="p-1.5 text-slate-300 hover:text-brand-500 hover:bg-brand-50 rounded-lg transition-colors"
                        title="重新命名"
                      >
                        <Settings size={13} />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          if (window.confirm(`確定要刪除專案「${project.name}」嗎？`)) {
                            deleteProject(project.id);
                          }
                        }}
                        className="p-1.5 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                        title="刪除專案"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default ProjectList;
export const SiteList = () => null; // Deprecated

