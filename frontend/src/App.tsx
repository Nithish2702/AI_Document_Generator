import { Routes, Route } from 'react-router-dom'
import ChatPage from './pages/ChatPage'
import DocumentListPage from './pages/DocumentListPage'
import DocumentViewPage from './pages/DocumentViewPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<ChatPage />} />
      <Route path="documents" element={<DocumentListPage />} />
      <Route path="documents/:id" element={<DocumentViewPage />} />
    </Routes>
  )
}

export default App
