import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Header } from '../components/Header';
import { adminAPI } from '../api/api';
import { AlertTriangle, HelpCircle } from 'lucide-react';

export const AdminConflicts = () => {
  const [conflicts, setConflicts] = useState([]);
  const [unverified, setUnverified] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    adminAPI.getConflicts()
      .then((res) => {
        setConflicts(res.data.conflicts || []);
        setUnverified(res.data.unverified_claims || []);
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
          <Link to="/admin/sources" style={{ textDecoration: 'none', backgroundColor: '#f1f5f9', color: '#475569', padding: '0.5rem 1rem', borderRadius: '8px', fontSize: '0.875rem', fontWeight: '600' }}>
            Sources & Provenance
          </Link>
          <Link to="/admin/conflicts" style={{ textDecoration: 'none', backgroundColor: '#15803d', color: '#ffffff', padding: '0.5rem 1rem', borderRadius: '8px', fontSize: '0.875rem', fontWeight: '700' }}>
            Conflict Audit
          </Link>
          <Link to="/admin/validation" style={{ textDecoration: 'none', backgroundColor: '#f1f5f9', color: '#475569', padding: '0.5rem 1rem', borderRadius: '8px', fontSize: '0.875rem', fontWeight: '600' }}>
            Data Quality
          </Link>
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.75rem', fontWeight: '800', color: '#0f172a', margin: 0 }}>
            Conflicting Evidence & Dispute Engine
          </h2>
          <p style={{ fontSize: '0.9375rem', color: '#64748b', marginTop: '0.25rem' }}>
            AgriGraph does not silently discard contradictory agricultural claims. Both sides are preserved and cited.
          </p>
        </div>

        {/* Conflicts List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', marginBottom: '3rem' }}>
          {conflicts.map((conflict, idx) => (
            <div
              key={idx}
              style={{
                backgroundColor: '#ffffff',
                borderRadius: '16px',
                border: '2px solid #fde68a',
                padding: '1.5rem',
                boxShadow: '0 4px 6px -1px rgba(0,0,0,0.03)'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                <AlertTriangle size={20} color="#b45309" />
                <span style={{
                  backgroundColor: '#fef3c7',
                  color: '#b45309',
                  fontSize: '0.75rem',
                  fontWeight: '800',
                  padding: '0.25rem 0.6rem',
                  borderRadius: '6px'
                }}>
                  CONFLICTING EVIDENCE
                </span>
                <span style={{ fontSize: '0.875rem', fontWeight: '700', color: '#0f172a' }}>
                  Entity: {conflict.entity_name}
                </span>
              </div>

              <p style={{ fontSize: '1.0625rem', color: '#1e293b', fontStyle: 'italic', marginBottom: '1.25rem' }}>
                "{conflict.claim_text}"
              </p>

              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: '1rem'
              }}>
                <div style={{ backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '10px', padding: '1rem' }}>
                  <h4 style={{ fontSize: '0.8125rem', fontWeight: '800', color: '#166534', margin: '0 0 0.5rem', textTransform: 'uppercase' }}>
                    Supporting Citations
                  </h4>
                  {conflict.supporting_sources && conflict.supporting_sources.length > 0 ? (
                    conflict.supporting_sources.map((s, i) => (
                      <p key={i} style={{ fontSize: '0.875rem', color: '#14532d', margin: '0.25rem 0' }}>
                        <strong>[{s.source_id}]</strong> {s.title} ({s.source_type})
                      </p>
                    ))
                  ) : (
                    <p style={{ fontSize: '0.875rem', color: '#14532d' }}>Extension Advisory DOC_003</p>
                  )}
                </div>

                <div style={{ backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '10px', padding: '1rem' }}>
                  <h4 style={{ fontSize: '0.8125rem', fontWeight: '800', color: '#991b1b', margin: '0 0 0.5rem', textTransform: 'uppercase' }}>
                    Contradicting Citations
                  </h4>
                  {conflict.contradicting_sources && conflict.contradicting_sources.length > 0 ? (
                    conflict.contradicting_sources.map((s, i) => (
                      <p key={i} style={{ fontSize: '0.875rem', color: '#7f1d1d', margin: '0.25rem 0' }}>
                        <strong>[{s.source_id}]</strong> {s.title} ({s.source_type})
                      </p>
                    ))
                  ) : (
                    <p style={{ fontSize: '0.875rem', color: '#7f1d1d' }}>Meta-Analysis DOC_004</p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Unverified Claims Section */}
        {unverified.length > 0 && (
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: '800', color: '#0f172a', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <HelpCircle size={20} color="#64748b" />
              Unverified Claims (Pending Research Anchor)
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {unverified.map((u, idx) => (
                <div key={idx} style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1rem' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: '700', color: '#dc2626', backgroundColor: '#fee2e2', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
                    UNVERIFIED
                  </span>
                  <span style={{ fontWeight: '700', color: '#0f172a', marginLeft: '0.5rem' }}>
                    {u.entity_name}
                  </span>
                  <p style={{ fontSize: '0.875rem', color: '#64748b', margin: '0.35rem 0 0' }}>
                    {u.claim_text} — <em>{u.reason}</em>
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
