const API_BASE_URL = 'http://localhost:8000/api/v1';

// 切換模擬模式，如果後端還沒啟動可以使用模擬數據
const IS_MOCK_MODE = true;

export const apiClient = {
  async getProjects() {
    if (IS_MOCK_MODE) {
      return [
        { id: 1, name: 'Sample Urban Project' },
        { id: 2, name: 'Riverside Development' }
      ];
    }
    const response = await fetch(`${API_BASE_URL}/projects/`);
    if (!response.ok) throw new Error('Failed to fetch projects');
    return response.json();
  },

  async createProject(name: string) {
    if (IS_MOCK_MODE) {
      return { id: Math.floor(Math.random() * 1000), name };
    }
    const response = await fetch(`${API_BASE_URL}/projects/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
    if (!response.ok) throw new Error('Failed to create project');
    return response.json();
  },

  async getSites(projectId: number) {
    if (IS_MOCK_MODE) {
      return [
        { id: 101, name: 'Main Site A', project_id: projectId },
        { id: 102, name: 'Auxiliary B', project_id: projectId }
      ];
    }
    const response = await fetch(`${API_BASE_URL}/sites/project/${projectId}`);
    if (!response.ok) throw new Error('Failed to fetch sites');
    return response.json();
  },

  async createSite(projectId: number, name: string, geometry: any) {
    if (IS_MOCK_MODE) {
      return { id: Math.floor(Math.random() * 1000), name, project_id: projectId, geometry };
    }
    const response = await fetch(`${API_BASE_URL}/sites/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_id: projectId, name, geometry }),
    });
    if (!response.ok) throw new Error('Failed to create site');
    return response.json();
  },
};
