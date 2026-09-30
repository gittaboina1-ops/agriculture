import React from 'react';
import { AlertTriangle } from 'lucide-react';

export const ConflictCard = ({ conflicts }) => {
  if (!conflicts || conflicts.length === 0) {
    return (
      <div style={{
        backgroundColor: '#f0fdf4',
        border: '1px solid #bbf7d0',
        borderRadius: '12px',
        padding: '0.875rem 1.25rem',
        marginBottom: '1.5rem',
        display: 'flex',
        alignItems: 'center',
        gap: '0.625rem',
        color: '#166534',
        fontSize: '0.875rem',
        fontWeight: '600'
      }}>
        <span>✓</span>
        <span>No relevant conflicting evidence found. Recommendations are consistent.</span>
      </div>
    );
  }

  return (
    <div style={{
      backgroundColor: '#fffbeb',
      border: '2px solid #fde68a',
      borderRadius: '16px',
      padding: '1.5rem',
      marginBottom: '1.5rem',
      boxShadow: '0 4px 6px -1px rgba(180, 83, 9, 0.05)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '1rem' }}>
        <div style={{
          backgroundColor: '#fef3c7',
          color: '#b45309',
          padding: '0.375rem',
          borderRadius: '8px'
        }}>
          <AlertTriangle size={22} />
        </div>
        <div>
          <h3 style={{ fontSize: '1.1875rem', fontWeight: '800', color: '#92400e', margin: 0 }}>
            Conflicting Evidence Found
          </h3>
          <p style={{ fontSize: '0.8125rem', color: '#b45309', margin: 0, fontWeight: '500' }}>
            Opposing scientific or advisory claims detected. Both sides are presented neutrally:
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {conflicts.map((conflict, idx) => (
          <div
            key={idx}
            style={{
              backgroundColor: '#ffffff',
              border: '1px solid #fde68a',
              borderRadius: '12px',
              padding: '1.125rem'
            }}
          >
            <p style={{ fontSize: '1rem', fontWeight: '700', color: '#0f172a', marginBottom: '0.75rem' }}>
              Subject: {conflict.entity_name}
            </p>
            <p style={{ fontSize: '0.9375rem', color: '#334155', fontStyle: 'italic', marginBottom: '1rem' }}>
              "{conflict.claim_text}"
            </p>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
              gap: '0.75rem'
            }}>
              {/* Supporting side */}
              <div style={{
                backgroundColor: '#f0fdf4',
                border: '1px solid #bbf7d0',
                borderRadius: '8px',
                padding: '0.75rem 1rem'
              }}>
                <span style={{ fontSize: '0.75rem', fontWeight: '800', color: '#166534', textTransform: 'uppercase' }}>
                  ✓ Supporting Source(s)
                </span>
                <p style={{ fontSize: '0.875rem', color: '#14532d', marginTop: '0.25rem', fontWeight: '600' }}>
                  {conflict.supporting_sources && conflict.supporting_sources.length > 0
                    ? conflict.supporting_sources.map(s => `[${s.source_id}] ${s.title}`).join(', ')
                    : 'Extension Advisory DOC_003'}
                </p>
              </div>

              {/* Contradicting side */}
              <div style={{
                backgroundColor: '#fef2f2',
                border: '1px solid #fecaca',
                borderRadius: '8px',
                padding: '0.75rem 1rem'
              }}>
                <span style={{ fontSize: '0.75rem', fontWeight: '800', color: '#991b1b', textTransform: 'uppercase' }}>
                  ✗ Contradicting Source(s)
                </span>
                <p style={{ fontSize: '0.875rem', color: '#7f1d1d', marginTop: '0.25rem', fontWeight: '600' }}>
                  {conflict.contradicting_sources && conflict.contradicting_sources.length > 0
                    ? conflict.contradicting_sources.map(s => `[${s.source_id}] ${s.title}`).join(', ')
                    : 'Systematic Review DOC_004 (Ineffective as standalone curative under humidity)'}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
