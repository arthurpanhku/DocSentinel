import { Navigate, Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import AgentIntegrations from "./pages/AgentIntegrations";
import Assessments from "./pages/Assessments";
import Dashboard from "./pages/Dashboard";
import Governance from "./pages/Governance";
import KnowledgeBase from "./pages/KnowledgeBase";
import Login from "./pages/Login";
import Settings from "./pages/Settings";
import Skills from "./pages/Skills";

export default function App() {
  return (
    <Routes>
      <Route path="login" element={<Login />} />
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="assessments" element={<Assessments />} />
        <Route path="governance" element={<Governance />} />
        <Route path="kb" element={<KnowledgeBase />} />
        <Route path="skills" element={<Skills />} />
        <Route path="integrations" element={<AgentIntegrations />} />
        <Route path="settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
