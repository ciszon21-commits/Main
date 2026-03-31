import React from 'react';
import { useStore } from '../../store/useStore';
import { Folder, Plus, Trash2, Map } from 'lucide-react';

const ProjectList: React.FC = () => {
  const { localProjects, saveAsProject, loadProject, deleteProject } = useStore();

  const handleAddProject = () => {
    const defaultName = `新專案 ${new Date().toLocaleTimeString()}`;
    const name = window.prompt("請輸入專案名稱:", defaultName);
    if (name) {
      saveAsProject(name);
    }
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
          localProjects.map((project: any) => (
            <div
              key={project.id}
              className="group w-full flex items-center justify-between px-3 py-2.5 rounded-xl transition-all border border-slate-100 bg-white hover:border-brand-200 hover:shadow-md cursor-pointer"
              onClick={() => loadProject(project.id)}
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-brand-50 flex items-center justify-center text-brand-500">
                  <Map size={16} />
                </div>
                <div className="flex flex-col items-start gap-0.5">
                  <span className="text-xs font-bold text-slate-700">{project.name}</span>
                  <span className="text-[9px] text-slate-400">
                    {new Date(project.updatedAt).toLocaleString('zh-TW', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'})}
                  </span>
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  if (window.confirm(`確定要刪除專案「${project.name}」嗎？`)) {
                    deleteProject(project.id);
                  }
                }}
                className="p-1.5 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                title="刪除專案"
              >
                <Trash2 size={13} />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ProjectList;
export const SiteList = () => null; // Deprecated
