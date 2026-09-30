import React from 'react';
import { ShieldAlert } from 'lucide-react';

export const DataQualityCard = ({ warnings }) => {
  if (!warnings || warnings.length === 0) return null;

  return (
    <div style={{
      backgroundColor: '#fef2f2',
      border: '2px solid #fecaca',
      borderRadius: '16px',
      padding: '1.25rem 1.5rem',
      marginBottom: '1.5rem'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.875rem' }}>
        <div style={{
          backgroundColor: '#fee2e2',
          color: '#dc2626',
          padding: '0.375rem',
          borderRadius: '8px'
        }}>
          <ShieldAlert size={20} />
        </div>
        <div>
          <h3 style={{ fontSize: '1.125rem', fontWeight: '800', color: '#991b1b', margin: 0 }}>
            Data Quality Check (Unreliable Data Excluded)
          </h3>
          <p style={{ fontSize: '0.8125rem', color: '#b91c1c', margin: 0, fontWeight: '500' }}>
            The following corrupted telemetry readings were quarantined and excluded from reasoning:
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
        {warnings.map((w, idx) => (
          <div
            key={idx}
            style={{
              backgroundColor: '#ffffff',
              border: '1px solid #fecaca',
              borderRadius: '8px',
              padding: '0.75rem 1rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '0.5rem'
            }}
          >
            <div>
              <span style={{ fontWeight: '700', color: '#991b1b', fontSize: '0.875rem' }}>
                {w.sensor_id} ({w.metric}: {w.rejected_value})
              </span>
              <p style={{ fontSize: '0.8125rem', color: '#475569', margin: '0.2rem 0 0' }}>
                {w.reason}
              </p>
            </div>
            <span style={{
              backgroundColor: '#fef2f2',
              color: '#b91c1c',
              border: '1px solid #fca5a5',
              borderRadius: '6px',
              padding: '0.2rem 0.5rem',
              fontSize: '0.75rem',
              fontWeight: '700'
            }}>
              {w.action_taken || 'Excluded'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
