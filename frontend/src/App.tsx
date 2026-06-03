import { Navigate, Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import Assessments from "./pages/Assessments";
import Dashboard from "./pages/Dashboard";
import KnowledgeBase from "./pages/KnowledgeBase";
import Settings from "./pages/Settings";
import Skills from "./pages/Skills";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="assessments" element={<Assessments />} />
        <Route path="kb" element={<KnowledgeBase />} />
        <Route path="skills" element={<Skills />} />
        <Route path="settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
