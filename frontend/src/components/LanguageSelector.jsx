import React from 'react';
import { Languages, Loader2, RotateCcw } from 'lucide-react';

const TRANSLATION_LANGUAGES = [
  { name: 'English', label: 'English' },
  { name: 'Telugu', label: 'తెలుగు — Telugu' },
  { name: 'Hindi', label: 'हिन्दी — Hindi' }
];

export const LanguageSelector = ({ currentLanguage, onSelectLanguage, translating, onShowOriginal }) => {
  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '0.625rem',
      backgroundColor: '#f8fafc',
      padding: '0.5rem 0.875rem',
      borderRadius: '12px',
      border: '1.5px solid #cbd5e1',
      flexWrap: 'wrap'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
        <Languages size={18} color="#15803d" />
        <span style={{ fontSize: '0.875rem', fontWeight: '700', color: '#334155' }}>
          Translate answer to:
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', flexWrap: 'wrap' }}>
        {TRANSLATION_LANGUAGES.map((lang) => (
          <button
            key={lang.name}
            type="button"
            onClick={() => onSelectLanguage(lang.name)}
            disabled={translating}
            style={{
              backgroundColor: currentLanguage === lang.name ? '#15803d' : '#ffffff',
              color: currentLanguage === lang.name ? '#ffffff' : '#334155',
              border: currentLanguage === lang.name ? '1.5px solid #15803d' : '1px solid #cbd5e1',
              borderRadius: '8px',
              padding: '0.35rem 0.75rem',
              fontSize: '0.8125rem',
              fontWeight: '700',
              cursor: translating ? 'wait' : 'pointer',
              transition: 'all 0.15s ease-in-out'
            }}
          >
            {lang.label}
          </button>
        ))}

        {currentLanguage !== 'English' && onShowOriginal && (
          <button
            type="button"
            onClick={onShowOriginal}
            disabled={translating}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.25rem',
              backgroundColor: '#ffffff',
              color: '#475569',
              border: '1px solid #94a3b8',
              borderRadius: '8px',
              padding: '0.35rem 0.75rem',
              fontSize: '0.8125rem',
              fontWeight: '700',
              cursor: 'pointer'
            }}
          >
            <RotateCcw size={14} />
            <span>Show Original</span>
          </button>
        )}
      </div>

      {translating && (
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.375rem' }}>
          <Loader2 size={16} className="spinner" color="#15803d" />
          <span style={{ fontSize: '0.75rem', fontWeight: '600', color: '#166534' }}>
            Translating the complete answer...
          </span>
        </div>
      )}
    </div>
  );
};
