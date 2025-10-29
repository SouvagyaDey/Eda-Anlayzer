import React, { useState } from 'react';
import { Upload, FileText, X } from 'lucide-react';
import './FileUpload.css';

const FileUpload = ({ onUpload, isUploading }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragActive, setIsDragActive] = useState(false);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file && file.name.endsWith('.csv')) {
      setSelectedFile(file);
    }
  };

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    const file = e.dataTransfer.files[0];
    if (file && file.name.endsWith('.csv')) {
      setSelectedFile(file);
    }
  };

  const handleUpload = () => {
    if (selectedFile && onUpload) {
      onUpload(selectedFile);
    }
  };

  const handleRemove = () => {
    setSelectedFile(null);
  };

  return (
    <div className="file-upload-container">
      <div
        className={`dropzone ${isDragActive ? 'active' : ''} ${isUploading ? 'disabled' : ''}`}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => !isUploading && document.getElementById('file-input').click()}
      >
        <input
          id="file-input"
          type="file"
          accept=".csv"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
          disabled={isUploading}
        />
        <div className="dropzone-content">
          <Upload size={48} className="upload-icon" />
          {selectedFile ? (
            <div className="file-selected">
              <FileText size={24} />
              <span className="file-name">{selectedFile.name}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleRemove();
                }}
                className="remove-file-btn"
                disabled={isUploading}
              >
                <X size={20} />
              </button>
            </div>
          ) : (
            <>
              <p className="dropzone-text">
                {isDragActive
                  ? 'Drop your CSV file here'
                  : 'Drag & drop a CSV file here, or click to select'}
              </p>
              <p className="dropzone-subtext">Only CSV files are accepted</p>
            </>
          )}
        </div>
      </div>

      {selectedFile && (
        <button
          onClick={handleUpload}
          disabled={isUploading}
          className="btn btn-primary upload-btn"
        >
          {isUploading ? (
            <>
              <div className="spinner-small"></div>
              Uploading...
            </>
          ) : (
            <>
              <Upload size={20} />
              Upload and Analyze
            </>
          )}
        </button>
      )}
    </div>
  );
};

export default FileUpload;
