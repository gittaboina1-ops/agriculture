import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Header } from '../components/Header';
import { adminAPI } from '../api/api';
import cytoscape from 'cytoscape';
import { Search, ZoomIn, ZoomOut, RotateCcw, Info } from 'lucide-react';

const NODE_COLORS = {
  Crop: '#16a34a',         // Green
  Disease: '#dc2626',      // Red
  Treatment: '#2563eb',    // Blue
  WeatherCondition: '#d97706', // Orange
  Soil: '#92400e',         // Brown
  Observation: '#7c3aed',  // Purple
  Sensor: '#0284c7',       // Cyan
  Source: '#475569',       // Slate
  Claim: '#0f766e'         // Teal
};

export const AdminGraph = () => {
  const containerRef = useRef(null);
  const cyRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [stats, setStats] = useState({ nodes: 0, edges: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    adminAPI.getGraph()
      .then((res) => {
        const { nodes, edges } = res.data;
        setStats({ nodes: nodes.length, edges: edges.length });
        initCytoscape(nodes, edges);
      })
      .catch((err) => console.error('Graph fetch error:', err))
      .finally(() => setLoading(false));

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
      }
    };
  }, []);

  const initCytoscape = (nodes, edges) => {
    if (!containerRef.current) return;

    const elements = [
      ...nodes.map((n) => ({
        data: {
          id: n.id,
          label: n.name || n.id,
          type: n.label || 'Entity',
          properties: n.properties || {}
        }
      })),
      ...edges.map((e, idx) => ({
        data: {
          id: `edge_${idx}`,
          source: e.source,
          target: e.target,
          label: e.relationship,
          properties: e.properties || {}
        }
      }))
    ];

    cyRef.current = cytoscape({
      container: containerRef.current,
      elements: elements,
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'color': '#0f172a',
            'font-size': '11px',
            'font-weight': '600',
            'text-valign': 'bottom',
            'text-margin-y': 4,
            'background-color': (ele) => NODE_COLORS[ele.data('type')] || '#64748b',
            'width': 28,
            'height': 28,
            'border-width': 2,
            'border-color': '#ffffff'
          }
        },
        {
          selector: 'edge',
          style: {
            'label': 'data(label)',
            'font-size': '9px',
            'color': '#64748b',
            'curve-style': 'bezier',
            'target-arrow-shape': 'triangle',
            'line-color': '#cbd5e1',
            'target-arrow-color': '#94a3b8',
            'arrow-scale': 0.8,
            'width': 1.5
          }
        },
        {
          selector: ':selected',
          style: {
            'border-width': 3,
            'border-color': '#0f172a',
            'line-color': '#15803d',
            'target-arrow-color': '#15803d'
          }
        }
      ],
      layout: {
        name: 'cose',
        animate: false,
        padding: 40,
        nodeRepulsion: 4500,
        idealEdgeLength: 60
      }
    });

    cyRef.current.on('tap', 'node', (evt) => {
      const node = evt.target;
      setSelectedNode({
        id: node.data('id'),
        label: node.data('type'),
        name: node.data('label'),
        properties: node.data('properties')
      });
    });

    cyRef.current.on('tap', (evt) => {
      if (evt.target === cyRef.current) {
        setSelectedNode(null);
      }
    });
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (!cyRef.current || !searchQuery.trim()) return;

    const matched = cyRef.current.nodes().filter((ele) => {
      return ele.data('label').toLowerCase().includes(searchQuery.toLowerCase());
    });

    if (matched.length > 0) {
      cyRef.current.nodes().unselect();
      matched.select();
      cyRef.current.animate({
        center: { eles: matched },
        zoom: 1.5,
        duration: 400
      });
      const first = matched[0];
      setSelectedNode({
        id: first.data('id'),
        label: first.data('type'),
        name: first.data('label'),
        properties: first.data('properties')
      });
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
          marginBottom: '1.5rem',
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
          <Link to="/admin/graph" style={{ textDecoration: 'none', backgroundColor: '#15803d', color: '#ffffff', padding: '0.5rem 1rem', borderRadius: '8px', fontSize: '0.875rem', fontWeight: '700' }}>
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

        {/* Graph Controls & Legend */}
        <div style={{
          backgroundColor: '#ffffff',
          borderRadius: '16px',
          border: '1px solid #e2e8f0',
          padding: '1.25rem',
          marginBottom: '1rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem'
        }}>
          {/* Search */}
          <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              type="text"
              placeholder="Search entity (e.g. Tomato, Early Blight)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                padding: '0.5rem 0.875rem',
                borderRadius: '8px',
                border: '1px solid #cbd5e1',
                fontSize: '0.875rem',
                width: '260px'
              }}
            />
            <button
              type="submit"
              style={{
                backgroundColor: '#15803d',
                color: '#ffffff',
                border: 'none',
                padding: '0.5rem 0.875rem',
                borderRadius: '8px',
                fontSize: '0.875rem',
                fontWeight: '700',
                display: 'flex',
                alignItems: 'center',
                gap: '0.25rem'
              }}
            >
              <Search size={16} /> Search
            </button>
          </form>

          {/* Zoom controls */}
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={() => cyRef.current && cyRef.current.zoom(cyRef.current.zoom() * 1.2)}
              title="Zoom In"
              style={{ padding: '0.5rem', borderRadius: '8px', border: '1px solid #cbd5e1', backgroundColor: '#ffffff' }}
            >
              <ZoomIn size={16} />
            </button>
            <button
              onClick={() => cyRef.current && cyRef.current.zoom(cyRef.current.zoom() * 0.8)}
              title="Zoom Out"
              style={{ padding: '0.5rem', borderRadius: '8px', border: '1px solid #cbd5e1', backgroundColor: '#ffffff' }}
            >
              <ZoomOut size={16} />
            </button>
            <button
              onClick={() => cyRef.current && cyRef.current.fit(40)}
              title="Reset View"
              style={{ padding: '0.5rem', borderRadius: '8px', border: '1px solid #cbd5e1', backgroundColor: '#ffffff' }}
            >
              <RotateCcw size={16} />
            </button>
          </div>
        </div>

        {/* Legend */}
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '0.75rem',
          marginBottom: '1rem',
          fontSize: '0.75rem',
          fontWeight: '600'
        }}>
          {Object.entries(NODE_COLORS).map(([label, color]) => (
            <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: color }} />
              <span style={{ color: '#475569' }}>{label}</span>
            </div>
          ))}
        </div>

        {/* Visual Graph Viewport and Inspector */}
        <div style={{ display: 'flex', gap: '1.25rem', flexWrap: 'wrap' }}>
          <div
            ref={containerRef}
            style={{
              flex: '1 1 600px',
              height: '560px',
              backgroundColor: '#ffffff',
              borderRadius: '16px',
              border: '1px solid #cbd5e1',
              boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)'
            }}
          />

          {/* Node Inspector Sidebar */}
          {selectedNode ? (
            <div style={{
              flex: '1 1 280px',
              backgroundColor: '#ffffff',
              borderRadius: '16px',
              border: '2px solid #bbf7d0',
              padding: '1.5rem',
              height: 'fit-content'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                <Info size={18} color="#15803d" />
                <span style={{
                  backgroundColor: '#f0fdf4',
                  color: '#15803d',
                  padding: '0.2rem 0.5rem',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  fontWeight: '800'
                }}>
                  {selectedNode.label}
                </span>
              </div>

              <h4 style={{ fontSize: '1.25rem', fontWeight: '800', color: '#0f172a', margin: '0 0 0.5rem' }}>
                {selectedNode.name}
              </h4>
              <p style={{ fontSize: '0.75rem', color: '#94a3b8', margin: '0 0 1rem' }}>
                Node ID: {selectedNode.id}
              </p>

              <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '0.75rem' }}>
                <h5 style={{ fontSize: '0.8125rem', fontWeight: '700', color: '#64748b', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
                  Node Properties
                </h5>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.8125rem' }}>
                  {Object.entries(selectedNode.properties).map(([k, v]) => (
                    <div key={k} style={{ display: 'flex', justifyContent: 'space-between', gap: '0.5rem' }}>
                      <span style={{ color: '#64748b' }}>{k}:</span>
                      <span style={{ fontWeight: '600', color: '#1e293b', textAlign: 'right' }}>{String(v)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div style={{
              flex: '1 1 280px',
              backgroundColor: '#ffffff',
              borderRadius: '16px',
              border: '1px dashed #cbd5e1',
              padding: '1.5rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center',
              color: '#94a3b8',
              fontSize: '0.875rem'
            }}>
              Click any node in the graph to inspect its properties and connected provenance.
            </div>
          )}
        </div>
      </main>
    </div>
  );
};
