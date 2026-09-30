import React, { useState } from 'react';
import { GitBranch, ChevronDown, ChevronUp, ArrowRight } from 'lucide-react';

export const EvidenceCard = ({ evidence }) => {
  const [isOpen, setIsOpen] = useState(true);

  if (!evidence || evidence.length === 0) return null;

  return (
    <div style={{
      backgroundColor: '#ffffff',
      borderRadius: '16px',
      border: '1px solid #e2e8f0',
      padding: '1.25rem 1.75rem',
      marginBottom: '1.5rem',
      boxShadow: '0 2px 4px rgba(0, 0, 0, 0.03)'
    }}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        style={{
          width: '100%',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'none',
          border: 'none',
          padding: 0,
          cursor: 'pointer'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
          <div style={{
            backgroundColor: '#eff6ff',
            color: '#2563eb',
            padding: '0.375rem',
            borderRadius: '8px'
          }}>
            <GitBranch size={20} />
          </div>
          <div style={{ textAlign: 'left' }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: '700', color: '#0f172a', margin: 0 }}>
              Why am I seeing this?
            </h3>
            <p style={{ fontSize: '0.8125rem', color: '#64748b', margin: 0 }}>
              Connected agricultural relationships backing this insight
            </p>
          </div>
        </div>
        {isOpen ? <ChevronUp size={20} color="#64748b" /> : <ChevronDown size={20} color="#64748b" />}
      </button>

      {isOpen && (
        <div style={{ marginTop: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {evidence.map((item, idx) => (
            <div
              key={idx}
              style={{
                backgroundColor: '#f8fafc',
                border: '1px solid #cbd5e1',
                borderRadius: '10px',
                padding: '0.875rem 1.25rem',
                display: 'flex',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '0.75rem'
              }}
            >
              <span style={{ fontWeight: '700', color: '#166534', fontSize: '1rem' }}>
                {item.subject}
              </span>
              <span style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.25rem',
                backgroundColor: '#e2e8f0',
                color: '#475569',
                fontSize: '0.75rem',
                fontWeight: '700',
                padding: '0.2rem 0.6rem',
                borderRadius: '9999px'
              }}>
                <ArrowRight size={12} /> {item.relationship}
              </span>
              <span style={{ fontWeight: '700', color: '#0369a1', fontSize: '1rem' }}>
                {item.object}
              </span>
              {item.provenance && (
                <span style={{
                  marginLeft: 'auto',
                  fontSize: '0.75rem',
                  color: '#64748b',
                  backgroundColor: '#f1f5f9',
                  padding: '0.2rem 0.5rem',
                  borderRadius: '6px',
                  fontWeight: '600'
                }}>
                  Source: {item.provenance}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
