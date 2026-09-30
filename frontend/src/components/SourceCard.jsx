import React, { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';

export const SourceCard = ({ sources }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!sources || sources.length === 0) return null;

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
            backgroundColor: '#fef3c7',
            color: '#b45309',
            padding: '0.375rem',
            borderRadius: '8px'
          }}>
            <BookOpen size={20} />
          </div>
          <div style={{ textAlign: 'left' }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: '700', color: '#0f172a', margin: 0 }}>
              Where did this information come from?
            </h3>
            <p style={{ fontSize: '0.8125rem', color: '#64748b', margin: 0 }}>
              {sources.length} documented scientific source{sources.length > 1 ? 's' : ''} cited
            </p>
          </div>
        </div>
        {isOpen ? <ChevronUp size={20} color="#64748b" /> : <ChevronDown size={20} color="#64748b" />}
      </button>

      {isOpen && (
        <div style={{ marginTop: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {sources.map((src, idx) => (
            <div
              key={idx}
              style={{
                backgroundColor: '#fffbeb',
                border: '1px solid #fde68a',
                borderRadius: '12px',
                padding: '1rem 1.25rem'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
                <span style={{
                  backgroundColor: '#fef3c7',
                  color: '#92400e',
                  fontSize: '0.75rem',
                  fontWeight: '800',
                  padding: '0.2rem 0.5rem',
                  borderRadius: '6px'
                }}>
                  {src.source_id} • {src.source_type}
                </span>

                {src.confidence_score && (
                  <span style={{ fontSize: '0.75rem', fontWeight: '700', color: '#166534', backgroundColor: '#dcfce7', padding: '0.2rem 0.5rem', borderRadius: '6px' }}>
                    Confidence: {Math.round(src.confidence_score * 100)}%
                  </span>
                )}
              </div>

              <h4 style={{ fontSize: '1rem', fontWeight: '700', color: '#78350f', margin: '0.5rem 0 0.25rem' }}>
                {src.title}
              </h4>

              {src.authors_or_publisher && (
                <p style={{ fontSize: '0.8125rem', color: '#92400e', margin: 0, fontWeight: '500' }}>
                  Publisher: {src.authors_or_publisher} ({src.publication_year || '2024'})
                </p>
              )}

              {src.summary && (
                <p style={{ fontSize: '0.875rem', color: '#451a03', marginTop: '0.5rem', lineHeight: 1.5 }}>
                  {src.summary}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
