import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import ResumeVerify from './pages/ResumeVerify'
import ProjectVerify from './pages/ProjectVerify'
import CertificateVerify from './pages/CertificateVerify'
import FullVerify from './pages/FullVerify'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/resume" element={<ResumeVerify />} />
        <Route path="/project" element={<ProjectVerify />} />
        <Route path="/certificate" element={<CertificateVerify />} />
        <Route path="/full" element={<FullVerify />} />
      </Routes>
    </Layout>
  )
}
