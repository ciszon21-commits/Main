import React, { useEffect } from 'react';
import { useStore } from '../../store/useStore';
import { Folder, Plus, Loader2 } from 'lucide-react';
import { apiClient } from '../../api/client';

const ProjectList: React.FC = () => {
  const { projects, setProjects, selectedProject, setSelectedProject, setSites } = useStore();
  const [isLoading, setIsLoading] = React.useState(true);

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const data = await apiClient.getProjects();
        setProjects(data);
      } catch (error) {
        console.error('Failed to fetch projects:', error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchProjects();
  }, [setProjects]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between px-2">
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Projects</h2>
        <button className="p-1 hover:bg-slate-100 rounded-full text-slate-400 hover:text-brand-500 transition-colors">
          <Plus size={16} />
        </button>
      </div>
      
      <div className="space-y-1">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="animate-spin text-slate-300" />
          </div>
        ) : projects.length === 0 ? (
          <p className="px-3 py-4 text-sm text-slate-400 text-center border-2 border-dashed border-slate-100 rounded-lg">
            No projects yet. Create one to start.
          </p>
        ) : (
          projects.map((project) => (
            <button
              key={project.id}
              onClick={async () => {
                setSelectedProject(project);
                try {
                  const sites = await apiClient.getSites(project.id);
                  setSites(sites);
                } catch (error) {
                  console.error('Failed to fetch sites:', error);
                }
              }}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-all text-sm font-medium ${
                selectedProject?.id === project.id
                  ? 'bg-brand-50 text-brand-600 border border-brand-100'
                  : 'text-slate-600 hover:bg-slate-50 border border-transparent'
              }`}
            >
              <Folder size={18} className={selectedProject?.id === project.id ? 'text-brand-500' : 'text-slate-400'} />
              {project.name}
            </button>
          ))
        )}
      </div>
    </div>
  );
};

export default ProjectList;

const SiteList: React.FC = () => {
  const { sites, selectedSite, setSelectedSite, selectedProject } = useStore();

  if (!selectedProject) return null;

  return (
    <div className="space-y-4 mt-6">
      <div className="flex items-center justify-between px-2">
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Sites</h2>
        <button className="p-1 hover:bg-slate-100 rounded-full text-slate-400 hover:text-brand-500 transition-colors">
          <Plus size={16} />
        </button>
      </div>
      
      <div className="space-y-1">
        {sites.length === 0 ? (
          <p className="px-3 py-4 text-xs text-slate-400 text-center border-2 border-dashed border-slate-100 rounded-lg">
            No sites defined for this project.
          </p>
        ) : (
          sites.map((site) => (
            <button
              key={site.id}
              onClick={() => setSelectedSite(site)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-all text-xs font-medium ${
                selectedSite?.id === site.id
                  ? 'bg-slate-100 text-slate-900 border border-slate-200'
                  : 'text-slate-500 hover:bg-slate-50 border border-transparent'
              }`}
            >
              <div className="w-2 h-2 rounded-full bg-brand-500" />
              {site.name}
            </button>
          ))
        )}
      </div>
    </div>
  );
};

export { SiteList };
