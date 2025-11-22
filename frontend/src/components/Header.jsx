import React from 'react';
import { Link } from 'react-router-dom';
import { BarChart3, Sun, Moon, Home as HomeIcon, Github } from 'lucide-react';
import './Header.css';

const Header = ({ darkMode, toggleDarkMode }) => {
  return (
    <header className="header">
      <div className="header-container">
        <Link to="/" className="logo">
          <BarChart3 size={28} className="logo-icon" />
          <span className="logo-text">EDA-Analyzer</span>
        </Link>
        
        <nav className="nav">
          <Link to="/" className="nav-link">
            <HomeIcon size={18} />
            <span>Home</span>
          </Link>
          <a 
            href="https://github.com/souvagyadey/Eda-analyzer" 
            className="nav-link" 
            target="_blank" 
            rel="noopener noreferrer"
          >
            <Github size={18} />
            <span>GitHub</span>
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
    </header>
  );
};

export default Header;
