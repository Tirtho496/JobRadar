import { NavLink, Route, Routes } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Jobs from './pages/Jobs'
import Digest from './pages/Digest'
import Market from './pages/Market'
import Applications from './pages/Applications'
import System from './pages/System'
import ModelLab from './pages/ModelLab'
import Settings from './pages/Settings'

const links = [
  ['/', 'Dashboard'],
  ['/jobs', 'Jobs'],
  ['/digest', 'Daily digest'],
  ['/applications', 'Applications'],
  ['/market', 'Skills market'],
  ['/system', 'System'],
  ['/model-lab', 'Model lab'],
  ['/settings', 'Settings']
]

export default function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">JobRadar</div>
        <div className="brand-sub">Junior AI/ML job intelligence</div>
        <nav>
          {links.map(([to, label]) => (
            <NavLink key={to} to={to} end={to === '/'} className={({isActive}) => isActive ? 'nav-link active' : 'nav-link'}>
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-note">Private local application. No paid API required.</div>
      </aside>
      <main className="content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/jobs" element={<Jobs />} />
          <Route path="/digest" element={<Digest />} />
          <Route path="/applications" element={<Applications />} />
          <Route path="/market" element={<Market />} />
          <Route path="/system" element={<System />} />
          <Route path="/model-lab" element={<ModelLab />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  )
}
