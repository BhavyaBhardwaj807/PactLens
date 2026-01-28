import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Disclaimer from './components/Disclaimer';
import LandingPage from './pages/LandingPage';
import UploadPage from './pages/UploadPage';
import ResultsPage from './pages/ResultsPage';
import './styles/globals.css';

function App() {
  return (
    <Router>
      <Disclaimer />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/results" element={<ResultsPage />} />
      </Routes>
    </Router>
  );
}

export default App;
