import { create } from 'zustand';

interface Project {
  id: number;
  name: string;
}

interface Site {
  id: number;
  name: string;
  projectId: number;
}

interface AppState {
  projects: Project[];
  setProjects: (projects: Project[]) => void;
  selectedProject: Project | null;
  setSelectedProject: (project: Project | null) => void;
  
  sites: Site[];
  setSites: (sites: Site[]) => void;
  selectedSite: Site | null;
  setSelectedSite: (site: Site | null) => void;
}

export const useStore = create<AppState>((set) => ({
  projects: [],
  setProjects: (projects) => set({ projects }),
  selectedProject: null,
  setSelectedProject: (selectedProject) => set({ selectedProject }),
  
  sites: [],
  setSites: (sites) => set({ sites }),
  selectedSite: null,
  setSelectedSite: (selectedSite) => set({ selectedSite }),
}));
