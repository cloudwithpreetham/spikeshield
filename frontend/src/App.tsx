import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard';
import Environments from './pages/Environments';
import EnvironmentDetail from './pages/EnvironmentDetail';
import BlueprintGenerator from './pages/BlueprintGenerator';
import Events from './pages/Events';
import Scaling from './pages/Scaling';
import Chaos from './pages/Chaos';
import FinOps from './pages/FinOps';
import Incidents from './pages/Incidents';
import { useWebSocket } from './hooks/useWebSocket';

function AppRoutes() {
  useWebSocket();
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/environments" element={<Environments />} />
        <Route path="/environments/:envName" element={<EnvironmentDetail />} />
        <Route path="/blueprint" element={<BlueprintGenerator />} />
        <Route path="/events" element={<Events />} />
        <Route path="/scaling" element={<Scaling />} />
        <Route path="/chaos" element={<Chaos />} />
        <Route path="/finops" element={<FinOps />} />
        <Route path="/incidents" element={<Incidents />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

export default function App() {
  return <BrowserRouter><AppRoutes /></BrowserRouter>;
}
