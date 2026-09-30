import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Header } from '../components/Header';
import { adminAPI } from '../api/api';
import { BookOpen, ShieldCheck, CheckCircle2 } from 'lucide-react';

export const AdminSources = () => {
  const [sources, setSources] = useState([]);
  const [coverage, setCoverage] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    adminAPI.getSources()
      .then((res) => {
        setSources(res.data.sources || []);
        setCoverage(res.data.coverage || null);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

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
          <Link to="/admin/upload" style={{ textDecoration: 'none', backgroundColor: '#f1f5f9', color: '#475569', padding: '0.5rem 1rem', borderRadius: '8px', fontSize: '0.875rem', fontWeight: '600' }}>
            Upload Resources
          </Link>
          <Link to="/admin/graph" style={{ textDecoration: 'none', backgroundColor: '#f1f5f9', color: '#475569', padding: '0.5rem 1rem', borderRadius: '8px', fontSize: '0.875rem', fontWeight: '600' }}>
            Knowledge Graph
          </Link>
          <Link to="/admin/sources" style={{ textDecoration: 'none', backgroundColor: '#15803d', color: '#ffffff', padding: '0.5rem 1rem', borderRadius: '8px', fontSize: '0.875rem', fontWeight: '700' }}>
            Sources & Provenance
          </Link>
          <Link to="/admin/conflicts" style={{ textDecoration: 'none', backgroundColor: '#f1f5f9', color: '#475569', padding: '0.5rem 1rem', borderRadius: '8px', fontSize: '0.875rem', fontWeight: '600' }}>
            Conflict Audit
          </Link>
          <Link to="/admin/validation" style={{ textDecoration: 'none', backgroundColor: '#f1f5f9', color: '#475569', padding: '0.5rem 1rem', borderRadius: '8px', fontSize: '0.875rem', fontWeight: '600' }}>
            Data Quality
          </Link>
        </div>

        {/* Coverage Header */}
        {coverage && (
          <div style={{
            backgroundColor: '#ffffff',
            borderRadius: '16px',
            border: '1px solid #e2e8f0',
            padding: '1.5rem',
            marginBottom: '1.5rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '1rem'
          }}>
            <div>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '800', color: '#0f172a', margin: 0 }}>
                Cataloged Provenance Lineage
              </h2>
              <p style={{ fontSize: '0.875rem', color: '#64748b', margin: '0.25rem 0 0' }}>
                {coverage.sourced_claims} of {coverage.total_claims} verified claims are anchored to peer-reviewed literature.
              </p>
            </div>
            <div style={{
              backgroundColor: '#f0fdf4',
              border: '1px solid #bbf7d0',
              padding: '0.75rem 1.25rem',
              borderRadius: '12px',
              textAlign: 'center'
            }}>
              <span style={{ fontSize: '0.75rem', fontWeight: '700', color: '#166534', textTransform: 'uppercase' }}>
                Provenance Coverage
              </span>
              <p style={{ fontSize: '1.75rem', fontWeight: '800', color: '#15803d', margin: 0 }}>
                {coverage.coverage_percentage}%
              </p>
            </div>
          </div>
        )}

        {/* Sources Cards Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '1.25rem'
        }}>
          {sources.map((src, idx) => (
            <div
              key={idx}
              style={{
                backgroundColor: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: '16px',
                padding: '1.5rem',
                boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <span style={{
                  backgroundColor: '#f1f5f9',
                  color: '#0f172a',
                  fontWeight: '800',
                  fontSize: '0.75rem',
                  padding: '0.25rem 0.6rem',
                  borderRadius: '6px'
                }}>
                  {src.source_id}
                </span>
                <span style={{
                  backgroundColor: '#dcfce7',
                  color: '#15803d',
                  fontSize: '0.75rem',
                  fontWeight: '700',
                  padding: '0.2rem 0.5rem',
                  borderRadius: '6px'
                }}>
                  {Math.round(src.confidence_score * 100)}% Confidence
                </span>
              </div>

              <h3 style={{ fontSize: '1.0625rem', fontWeight: '700', color: '#0f172a', margin: '0 0 0.5rem', lineHeight: 1.4 }}>
                {src.title}
              </h3>

              <p style={{ fontSize: '0.8125rem', color: '#64748b', marginBottom: '0.75rem' }}>
                Type: <strong>{src.source_type}</strong> • Publisher: {src.authors_or_publisher} ({src.publication_year})
              </p>

              <p style={{ fontSize: '0.875rem', color: '#334155', lineHeight: 1.5 }}>
                {src.summary}
              </p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};
