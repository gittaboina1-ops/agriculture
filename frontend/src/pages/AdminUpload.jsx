import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Header } from '../components/Header';
import { adminAPI } from '../api/api';
import {
  UploadCloud,
  FileText,
  CheckCircle,
  AlertCircle,
  Loader2,
  Play,
  RotateCw,
  Clock
} from 'lucide-react';

export const AdminUpload = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileBase64, setFileBase64] = useState('');
  const [title, setTitle] = useState('');
  const [authors, setAuthors] = useState('');
  const [publicationYear, setPublicationYear] = useState(2026);
  const [confidenceScore, setConfidenceScore] = useState(0.92);
  
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [error, setError] = useState('');

  // Documents list
  const [documents, setDocuments] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(true);

  // Ingestion tracking state for selected document
  const [activeProcessingDocId, setActiveProcessingDocId] = useState(null);
  const [processingStats, setProcessingStats] = useState(null);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = () => {
    setLoadingDocs(true);
    adminAPI.getDocuments()
      .then(res => setDocuments(res.data || []))
      .catch(() => {})
      .finally(() => setLoadingDocs(false));
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setTitle(file.name.replace(/\.[^/.]+$/, "").replace(/_/g, ' '));
      
      const reader = new FileReader();
      reader.onload = () => {
        setFileBase64(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleUploadOnly = async (e) => {
    e.preventDefault();
    if (!selectedFile || !fileBase64) return;

    setUploading(true);
    setError('');
    setUploadSuccess(null);

    try {
      const res = await adminAPI.uploadResource({
        filename: selectedFile.name,
        file_content_base64: fileBase64,
        title: title || selectedFile.name,
        authors: authors || 'Research Team',
        publication_year: parseInt(publicationYear) || 2026,
        confidence_score: parseFloat(confidenceScore) || 0.92,
        process_immediately: false // Upload only; awaits Create Knowledge Graph click
      });

      setUploadSuccess({
        message: 'Resource uploaded successfully! Click "Create Knowledge Graph" below to process.',
        doc: res.data
      });
      fetchDocuments();
      setSelectedFile(null);
      setFileBase64('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed.');
    } finally {
      setUploading(false);
    }
  };

  const handleCreateKnowledgeGraph = async (docId) => {
    setActiveProcessingDocId(docId);
    setError('');

    try {
      const res = await adminAPI.triggerCreateGraph(docId);
      setProcessingStats(res.data);
      fetchDocuments();
    } catch (err) {
      setError(err.response?.data?.detail || 'Graph construction failed.');
    } finally {
      setActiveProcessingDocId(null);
    }
  };

  return (
    <div className="app-container">
      <Header />

      <main className="main-content">
        {/* Navigation Tabs */}
        <div style={{
          display: 'flex',
          gap: '0.75rem',
          flexWrap: 'wrap',
          marginBottom: '2rem',
          backgroundColor: '#ffffff',
          padding: '0.75rem',
          borderRadius: '12px',
          border: '1px solid #e2e8f0'
        }}>
          <Link to="/admin" style={{ textDecoration: 'none', backgroundColor: '#f1f5f9', color: '#475569', padding: '0.5rem 1rem', borderRadius: '8px', fontSize: '0.875rem', fontWeight: '600' }}>
            Overview
          </Link>
          <Link to="/admin/upload" style={{ textDecoration: 'none', backgroundColor: '#15803d', color: '#ffffff', padding: '0.5rem 1rem', borderRadius: '8px', fontSize: '0.875rem', fontWeight: '700' }}>
            Upload Resources
          </Link>
          <Link to="/admin/graph" style={{ textDecoration: 'none', backgroundColor: '#f1f5f9', color: '#475569', padding: '0.5rem 1rem', borderRadius: '8px', fontSize: '0.875rem', fontWeight: '600' }}>
            Knowledge Graph
          </Link>
          <Link to="/admin/sources" style={{ textDecoration: 'none', backgroundColor: '#f1f5f9', color: '#475569', padding: '0.5rem 1rem', borderRadius: '8px', fontSize: '0.875rem', fontWeight: '600' }}>
            Sources & Provenance
          </Link>
          <Link to="/admin/conflicts" style={{ textDecoration: 'none', backgroundColor: '#f1f5f9', color: '#475569', padding: '0.5rem 1rem', borderRadius: '8px', fontSize: '0.875rem', fontWeight: '600' }}>
            Conflict Audit
          </Link>
          <Link to="/admin/validation" style={{ textDecoration: 'none', backgroundColor: '#f1f5f9', color: '#475569', padding: '0.5rem 1rem', borderRadius: '8px', fontSize: '0.875rem', fontWeight: '600' }}>
            Data Quality
          </Link>
        </div>

        {/* Upload Container */}
        <div style={{
          backgroundColor: '#ffffff',
          borderRadius: '16px',
          border: '1px solid #e2e8f0',
          padding: '2rem',
          marginBottom: '2rem',
          boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)'
        }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: '800', color: '#0f172a', marginBottom: '0.5rem' }}>
            Add Agricultural Knowledge Resource
          </h2>
          <p style={{ fontSize: '0.9375rem', color: '#64748b', marginBottom: '1.5rem' }}>
            Upload research documents (PDF), disease datasets (CSV), or farm observations (JSON).
          </p>

          {error && (
            <div style={{
              backgroundColor: '#fef2f2',
              border: '1px solid #fecaca',
              color: '#b91c1c',
              padding: '0.875rem 1rem',
              borderRadius: '10px',
              fontSize: '0.875rem',
              marginBottom: '1.5rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          {uploadSuccess && (
            <div style={{
              backgroundColor: '#f0fdf4',
              border: '1px solid #bbf7d0',
              color: '#166534',
              padding: '1rem',
              borderRadius: '10px',
              fontSize: '0.9375rem',
              marginBottom: '1.5rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '1rem'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle size={20} color="#166534" />
                <span>{uploadSuccess.message}</span>
              </div>
              <button
                type="button"
                onClick={() => handleCreateKnowledgeGraph(uploadSuccess.doc.document_id)}
                style={{
                  backgroundColor: '#15803d',
                  color: '#ffffff',
                  border: 'none',
                  padding: '0.5rem 1rem',
                  borderRadius: '8px',
                  fontWeight: '700',
                  fontSize: '0.875rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.375rem'
                }}
              >
                <Play size={16} /> Create Knowledge Graph
              </button>
            </div>
          )}

          <form onSubmit={handleUploadOnly}>
            {/* Drag & Drop Area */}
            <div style={{
              border: '2px dashed #cbd5e1',
              borderRadius: '12px',
              padding: '2.5rem 1.5rem',
              textAlign: 'center',
              backgroundColor: '#f8fafc',
              marginBottom: '1.5rem',
              cursor: 'pointer'
            }}>
              <input
                type="file"
                id="file-upload"
                accept=".pdf,.csv,.json"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
              <label htmlFor="file-upload" style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{ backgroundColor: '#f0fdf4', color: '#15803d', padding: '0.875rem', borderRadius: '50%' }}>
                  <UploadCloud size={32} />
                </div>
                <div>
                  <span style={{ fontSize: '1.0625rem', fontWeight: '700', color: '#15803d' }}>
                    Click to Choose File
                  </span>
                  <span style={{ fontSize: '0.9375rem', color: '#64748b' }}> or drag and drop</span>
                </div>
                <p style={{ fontSize: '0.8125rem', color: '#94a3b8', margin: 0 }}>
                  Supports PDF (research publications), CSV (disease/treatment registries), and JSON (observations)
                </p>
              </label>

              {selectedFile && (
                <div style={{
                  marginTop: '1.25rem',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  backgroundColor: '#ffffff',
                  border: '1px solid #bbf7d0',
                  padding: '0.5rem 1rem',
                  borderRadius: '8px'
                }}>
                  <FileText size={18} color="#15803d" />
                  <span style={{ fontWeight: '600', color: '#0f172a', fontSize: '0.875rem' }}>
                    {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                  </span>
                </div>
              )}
            </div>

            {/* Metadata Fields */}
            {selectedFile && (
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: '1rem',
                marginBottom: '1.5rem'
              }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: '700', color: '#334155', marginBottom: '0.35rem' }}>
                    Resource Title
                  </label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    style={{ width: '100%', padding: '0.625rem', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.875rem' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: '700', color: '#334155', marginBottom: '0.35rem' }}>
                    Authors / Publisher
                  </label>
                  <input
                    type="text"
                    value={authors}
                    placeholder="e.g. Agronomy Research Consortium"
                    onChange={(e) => setAuthors(e.target.value)}
                    style={{ width: '100%', padding: '0.625rem', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.875rem' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: '700', color: '#334155', marginBottom: '0.35rem' }}>
                    Publication Year
                  </label>
                  <input
                    type="number"
                    value={publicationYear}
                    onChange={(e) => setPublicationYear(e.target.value)}
                    style={{ width: '100%', padding: '0.625rem', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.875rem' }}
                  />
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={!selectedFile || uploading}
              style={{
                backgroundColor: !selectedFile || uploading ? '#94a3b8' : '#15803d',
                color: '#ffffff',
                border: 'none',
                padding: '0.875rem 1.75rem',
                borderRadius: '10px',
                fontSize: '1rem',
                fontWeight: '700',
                cursor: !selectedFile || uploading ? 'not-allowed' : 'pointer'
              }}
            >
              {uploading ? 'Uploading Resource...' : 'Upload Resource'}
            </button>
          </form>
        </div>

        {/* Processing Result Display */}
        {processingStats && (
          <div style={{
            backgroundColor: '#ffffff',
            borderRadius: '16px',
            border: '2px solid #86efac',
            padding: '1.75rem',
            marginBottom: '2rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <CheckCircle size={22} color="#15803d" />
              <h3 style={{ fontSize: '1.25rem', fontWeight: '800', color: '#166534', margin: 0 }}>
                Knowledge Graph Successfully Updated!
              </h3>
            </div>
            <p style={{ fontSize: '0.9375rem', color: '#334155', marginBottom: '1.25rem' }}>
              Document Source: <strong>{processingStats.document_id}</strong>
            </p>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '1rem',
              backgroundColor: '#f8fafc',
              padding: '1.25rem',
              borderRadius: '12px'
            }}>
              <div><span style={{ fontSize: '0.75rem', color: '#64748b' }}>Pages Processed</span><p style={{ fontSize: '1.25rem', fontWeight: '800', margin: 0 }}>{processingStats.stats?.pages_processed}</p></div>
              <div><span style={{ fontSize: '0.75rem', color: '#64748b' }}>Chunks Created</span><p style={{ fontSize: '1.25rem', fontWeight: '800', margin: 0 }}>{processingStats.stats?.chunks_created}</p></div>
              <div><span style={{ fontSize: '0.75rem', color: '#64748b' }}>Entities Extracted</span><p style={{ fontSize: '1.25rem', fontWeight: '800', color: '#15803d', margin: 0 }}>{processingStats.stats?.entities_extracted}</p></div>
              <div><span style={{ fontSize: '0.75rem', color: '#64748b' }}>Relationships Created</span><p style={{ fontSize: '1.25rem', fontWeight: '800', color: '#2563eb', margin: 0 }}>{processingStats.stats?.new_relationships}</p></div>
              <div><span style={{ fontSize: '0.75rem', color: '#64748b' }}>New Graph Nodes</span><p style={{ fontSize: '1.25rem', fontWeight: '800', color: '#0f172a', margin: 0 }}>{processingStats.stats?.new_nodes}</p></div>
              <div><span style={{ fontSize: '0.75rem', color: '#64748b' }}>Duplicates Skipped</span><p style={{ fontSize: '1.25rem', fontWeight: '800', color: '#64748b', margin: 0 }}>{processingStats.stats?.duplicates_skipped}</p></div>
              <div><span style={{ fontSize: '0.75rem', color: '#64748b' }}>Conflicts Detected</span><p style={{ fontSize: '1.25rem', fontWeight: '800', color: '#d97706', margin: 0 }}>{processingStats.stats?.conflicts_detected}</p></div>
            </div>
          </div>
        )}

        {/* Cataloged Resources Table */}
        <div style={{
          backgroundColor: '#ffffff',
          borderRadius: '16px',
          border: '1px solid #e2e8f0',
          padding: '1.75rem'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: '800', color: '#0f172a', margin: 0 }}>
              Cataloged Resources & Ingestion Status
            </h3>
            <button
              onClick={fetchDocuments}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.375rem',
                backgroundColor: '#f1f5f9',
                border: '1px solid #cbd5e1',
                padding: '0.4rem 0.75rem',
                borderRadius: '8px',
                fontSize: '0.8125rem',
                fontWeight: '600'
              }}
            >
              <RotateCw size={14} /> Refresh
            </button>
          </div>

          {loadingDocs ? (
            <p style={{ textAlign: 'center', color: '#64748b' }}>Loading documents...</p>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #e2e8f0', color: '#475569' }}>
                    <th style={{ padding: '0.75rem' }}>Source ID</th>
                    <th style={{ padding: '0.75rem' }}>Title</th>
                    <th style={{ padding: '0.75rem' }}>Type</th>
                    <th style={{ padding: '0.75rem' }}>Status</th>
                    <th style={{ padding: '0.75rem', textAlign: 'right' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map((doc, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '0.75rem', fontWeight: '700', color: '#15803d' }}>
                        {doc.document_id}
                      </td>
                      <td style={{ padding: '0.75rem', fontWeight: '600', color: '#1e293b' }}>
                        {doc.title}
                      </td>
                      <td style={{ padding: '0.75rem', color: '#64748b' }}>
                        {doc.source_type}
                      </td>
                      <td style={{ padding: '0.75rem' }}>
                        <span style={{
                          backgroundColor: doc.status === 'COMPLETED' ? '#dcfce7' : '#fef3c7',
                          color: doc.status === 'COMPLETED' ? '#166534' : '#92400e',
                          padding: '0.2rem 0.6rem',
                          borderRadius: '9999px',
                          fontSize: '0.75rem',
                          fontWeight: '700'
                        }}>
                          {doc.status}
                        </span>
                      </td>
                      <td style={{ padding: '0.75rem', textAlign: 'right' }}>
                        {doc.status !== 'COMPLETED' ? (
                          <button
                            onClick={() => handleCreateKnowledgeGraph(doc.document_id)}
                            disabled={activeProcessingDocId === doc.document_id}
                            style={{
                              backgroundColor: '#15803d',
                              color: '#ffffff',
                              border: 'none',
                              padding: '0.4rem 0.75rem',
                              borderRadius: '8px',
                              fontSize: '0.75rem',
                              fontWeight: '700',
                              cursor: 'pointer',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '0.25rem'
                            }}
                          >
                            {activeProcessingDocId === doc.document_id ? (
                              <><Loader2 size={12} className="spinner" /> Processing...</>
                            ) : (
                              <><Play size={12} /> Create Knowledge Graph</>
                            )}
                          </button>
                        ) : (
                          <span style={{ fontSize: '0.75rem', color: '#166534', fontWeight: '600' }}>
                            ✓ Ingested
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};
