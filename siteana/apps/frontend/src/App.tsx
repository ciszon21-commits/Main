import ProjectList, { SiteList } from './components/Sidebar/ProjectList';
import SiteDetails from './components/Sidebar/SiteDetails';
import Map from './components/Map/Map';
import StyleSelector from './components/Sidebar/StyleSelector';

function App() {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 font-sans text-slate-900">
      {/* Sidebar */}
      <aside className="w-80 h-full border-r bg-white shadow-sm z-10 flex flex-col">
        <header className="p-6 border-b">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-8 h-8 rounded bg-brand-500 flex items-center justify-center text-white font-bold text-lg shadow-sm">S</div>
            <h1 className="text-xl font-bold tracking-tight">SiteANA</h1>
          </div>
          <p className="text-xs text-slate-400 font-medium">Design-oriented Web GIS Tool</p>
        </header>
        <div className="flex-1 overflow-y-auto p-4 custom-scrollbar space-y-8">
          <div>
            <ProjectList />
            <SiteList />
          </div>
          <div className="border-t pt-8">
            <StyleSelector />
          </div>
          <div className="border-t pt-8">
            <SiteDetails />
          </div>
        </div>
        <footer className="p-4 border-t bg-slate-50">
          <div className="text-[10px] text-slate-400 font-mono flex justify-between">
            <span>v0.1.0-alpha</span>
            <span>2026-03-26</span>
          </div>
        </footer>
      </aside>

      {/* Main Content */}
      <main className="flex-1 relative">
        <Map />
      </main>
    </div>
  );
}

export default App;
