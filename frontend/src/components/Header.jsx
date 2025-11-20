import React from 'react';
import { Link } from 'react-router-dom';
import { BarChart3, Sun, Moon } from 'lucide-react';
import './Header.css';

const Header = ({ darkMode, toggleDarkMode }) => {
  return (
    <header className="header">
      <div className="container">
        <div className="header-content">
          <Link to="/" className="logo">
            <BarChart3 size={32} />
            <span className="logo-text">EDA-Analyzer</span>
          </Link>
          <nav className="nav">
            <Link to="/" className="nav-link">Home</Link>
            <a 
              href="https://github.com/souvagyadey/Eda-analyzer" 
              target="_blank" 
              rel="noopener noreferrer"
              className="nav-link"
            >
              GitHub
            </a>
            <button 
              onClick={toggleDarkMode} 
              className="theme-toggle"
              aria-label="Toggle dark mode"
              title={darkMode ? "Switch to light mode" : "Switch to dark mode"}
            >
              {darkMode ? <Sun size={20} /> : <Moon size={20} />}
            </button>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;
