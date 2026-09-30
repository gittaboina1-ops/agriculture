import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Header } from '../components/Header';
import { adminAPI } from '../api/api';
import { ShieldAlert, CheckCircle2, XCircle } from 'lucide-react';

export const AdminDataQuality = () => {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    adminAPI.getValidation()
      .then((res) => setReport(res.data))
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
          <Link to="/admin/conflicts" style={{ textDecoration: 'none', backgroundColor: '#f1f5f9', color: '#475569', padding: '0.5rem 1rem', borderRadius: '8px', fontSize: '0.875rem', fontWeight: '600' }}>
            Conflict Audit
          </Link>
          <Link to="/admin/validation" style={{ textDecoration: 'none', backgroundColor: '#15803d', color: '#ffffff', padding: '0.5rem 1rem', borderRadius: '8px', fontSize: '0.875rem', fontWeight: '700' }}>
            Data Quality
          </Link>
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.75rem', fontWeight: '800', color: '#0f172a', margin: 0 }}>
            Sensor Validation & Telemetry Boundaries
          </h2>
          <p style={{ fontSize: '0.9375rem', color: '#64748b', marginTop: '0.25rem' }}>
            Screening incoming agro-meteorological sensor streams against thermodynamic and physical limits.
          </p>
        </div>

        {report && (
          <>
            {/* Top Stat Summary */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '1.25rem',
              marginBottom: '2rem'
            }}>
              <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.25rem' }}>
                <span style={{ fontSize: '0.8125rem', color: '#64748b', fontWeight: '600' }}>Total Processed</span>
                <p style={{ fontSize: '1.75rem', fontWeight: '800', color: '#0f172a', margin: '0.25rem 0 0' }}>{report.total_processed}</p>
              </div>
              <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.25rem' }}>
                <span style={{ fontSize: '0.8125rem', color: '#166534', fontWeight: '600' }}>Accepted Readings</span>
                <p style={{ fontSize: '1.75rem', fontWeight: '800', color: '#15803d', margin: '0.25rem 0 0' }}>{report.valid_count}</p>
              </div>
              <div style={{ backgroundColor: '#ffffff', border: '1px solid #fecaca', borderRadius: '12px', padding: '1.25rem' }}>
                <span style={{ fontSize: '0.8125rem', color: '#991b1b', fontWeight: '600' }}>Quarantined / Rejected</span>
                <p style={{ fontSize: '1.75rem', fontWeight: '800', color: '#dc2626', margin: '0.25rem 0 0' }}>{report.invalid_count}</p>
              </div>
            </div>

            {/* Quarantined Readings Table */}
            <div style={{
              backgroundColor: '#ffffff',
              borderRadius: '16px',
              border: '2px solid #fecaca',
              padding: '1.5rem',
              marginBottom: '2rem'
            }}>
              <h3 style={{ fontSize: '1.1875rem', fontWeight: '800', color: '#991b1b', margin: '0 0 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <ShieldAlert size={20} color="#dc2626" />
                Quarantined Telemetry (Excluded from Knowledge Graph Reasoning)
              </h3>

              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid #fee2e2', color: '#991b1b' }}>
                      <th style={{ padding: '0.625rem' }}>Sensor ID</th>
                      <th style={{ padding: '0.625rem' }}>Metric</th>
                      <th style={{ padding: '0.625rem' }}>Value</th>
                      <th style={{ padding: '0.625rem' }}>Anomaly Reason</th>
                      <th style={{ padding: '0.625rem' }}>Action Taken</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.invalid_records?.map((r, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid #fee2e2' }}>
                        <td style={{ padding: '0.625rem', fontWeight: '700', color: '#991b1b' }}>{r.sensor_id}</td>
                        <td style={{ padding: '0.625rem', textTransform: 'capitalize' }}>{r.metric}</td>
                        <td style={{ padding: '0.625rem', fontWeight: '700' }}>{r.value} {r.unit}</td>
                        <td style={{ padding: '0.625rem', color: '#475569' }}>{r.anomaly_reason}</td>
                        <td style={{ padding: '0.625rem' }}>
                          <span style={{ backgroundColor: '#fee2e2', color: '#dc2626', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: '700' }}>
                            {r.action_taken || 'Excluded'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Valid Readings Table */}
            <div style={{
              backgroundColor: '#ffffff',
              borderRadius: '16px',
              border: '1px solid #bbf7d0',
              padding: '1.5rem'
            }}>
              <h3 style={{ fontSize: '1.1875rem', fontWeight: '800', color: '#166534', margin: '0 0 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle2 size={20} color="#15803d" />
                Verified & Calibrated Readings
              </h3>

              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid #dcfce7', color: '#166534' }}>
                      <th style={{ padding: '0.625rem' }}>Sensor ID</th>
                      <th style={{ padding: '0.625rem' }}>Type</th>
                      <th style={{ padding: '0.625rem' }}>Metric</th>
                      <th style={{ padding: '0.625rem' }}>Value</th>
                      <th style={{ padding: '0.625rem' }}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.valid_records?.map((r, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid #f0fdf4' }}>
                        <td style={{ padding: '0.625rem', fontWeight: '700', color: '#166534' }}>{r.sensor_id}</td>
                        <td style={{ padding: '0.625rem', color: '#475569' }}>{r.sensor_type}</td>
                        <td style={{ padding: '0.625rem', textTransform: 'capitalize' }}>{r.metric}</td>
                        <td style={{ padding: '0.625rem', fontWeight: '700' }}>{r.value} {r.unit}</td>
                        <td style={{ padding: '0.625rem' }}>
                          <span style={{ backgroundColor: '#dcfce7', color: '#15803d', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: '700' }}>
                            VALID
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
};
