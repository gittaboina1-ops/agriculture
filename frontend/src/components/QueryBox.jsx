import React from 'react';
import { Search } from 'lucide-react';
import { VoiceInput } from './VoiceInput';

export const QueryBox = ({ query, setQuery, onSearch, loading }) => {
  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !loading) {
      onSearch(query);
    }
  };

  const handleVoiceConverted = (text) => {
    setQuery(text);
  };

  return (
    <form onSubmit={handleSubmit} style={{ width: '100%' }}>
      <div style={{
        backgroundColor: '#ffffff',
        border: '2px solid #bbf7d0',
        borderRadius: '16px',
        padding: '1.25rem',
        boxShadow: '0 4px 12px rgba(21, 128, 61, 0.08)'
      }}>
        <label htmlFor="farmer-query" style={{
          display: 'block',
          fontSize: '1.125rem',
          fontWeight: '700',
          color: '#166534',
          marginBottom: '0.75rem'
        }}>
          Ask your agricultural question...
        </label>

        <textarea
          id="farmer-query"
          rows={3}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. Why is my tomato crop at high disease risk? or What soil is best for tomatoes?"
          style={{
            width: '100%',
            fontSize: '1.125rem',
            lineHeight: 1.5,
            padding: '0.875rem',
            borderRadius: '10px',
            border: '1px solid #cbd5e1',
            outline: 'none',
            resize: 'vertical',
            color: '#0f172a',
            backgroundColor: '#f8fafc'
          }}
          onFocus={(e) => { e.target.style.borderColor = '#15803d'; e.target.style.backgroundColor = '#ffffff'; }}
          onBlur={(e) => { e.target.style.borderColor = '#cbd5e1'; }}
        />

        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginTop: '1rem',
          flexWrap: 'wrap',
          gap: '1rem'
        }}>
          {/* Voice Input Button */}
          <VoiceInput onSpeechConverted={handleVoiceConverted} />

          {/* Ask AgriGraph Button */}
          <button
            type="submit"
            disabled={loading || !query.trim()}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.625rem',
              backgroundColor: loading || !query.trim() ? '#94a3b8' : '#15803d',
              color: '#ffffff',
              border: 'none',
              padding: '0.875rem 2rem',
              borderRadius: '12px',
              fontSize: '1.125rem',
              fontWeight: '800',
              cursor: loading || !query.trim() ? 'not-allowed' : 'pointer',
              boxShadow: '0 4px 6px -1px rgba(21, 128, 61, 0.2)'
            }}
            onMouseEnter={(e) => {
              if (!loading && query.trim()) e.currentTarget.style.backgroundColor = '#166534';
            }}
            onMouseLeave={(e) => {
              if (!loading && query.trim()) e.currentTarget.style.backgroundColor = '#15803d';
            }}
          >
            <Search size={22} strokeWidth={2.5} />
            <span>{loading ? 'Finding Answer...' : 'Ask AgriGraph'}</span>
          </button>
        </div>
      </div>
    </form>
  );
};
