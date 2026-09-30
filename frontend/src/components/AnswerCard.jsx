import React from 'react';
import { CheckCircle2, Cpu, ShieldCheck } from 'lucide-react';
import { LanguageSelector } from './LanguageSelector';

export const AnswerCard = ({
  answerText,
  relevantFactors,
  matchedCrop,
  matchedDisease,
  currentLanguage,
  onSelectLanguage,
  translating,
  onShowOriginal,
  generationMode,
  provider,
  model,
  fallbackReason
}) => {
  const isLlm = generationMode === 'llm';

  return (
    <div style={{
      backgroundColor: '#ffffff',
      borderRadius: '16px',
      border: '1px solid #e2e8f0',
      padding: '1.75rem',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
      marginBottom: '1.5rem'
    }}>
      {/* Header with Title and Language Selector */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '1rem',
        marginBottom: '1.25rem',
        paddingBottom: '1rem',
        borderBottom: '1px solid #f1f5f9'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
          <div style={{
            backgroundColor: '#dcfce7',
            color: '#15803d',
            padding: '0.375rem',
            borderRadius: '8px'
          }}>
            <CheckCircle2 size={22} />
          </div>
          <div>
            <h2 style={{ fontSize: '1.375rem', fontWeight: '800', color: '#0f172a', margin: 0 }}>
              AgriGraph Answer
            </h2>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.375rem',
              fontSize: '0.75rem',
              color: '#64748b',
              marginTop: '0.25rem'
            }}>
              {isLlm ? (
                <>
                  <Cpu size={13} color="#2563eb" />
                  <span>Synthesized via <strong>{provider === 'gemini' ? 'Google Gemini' : 'OpenAI'}</strong> ({model || 'LLM'})</span>
                </>
              ) : (
                <>
                  <ShieldCheck size={13} color="#15803d" />
                  <span>Synthesized via <strong>Grounded Rule Engine</strong> {fallbackReason ? `(${fallbackReason})` : ''}</span>
                </>
              )}
            </div>
          </div>
        </div>

        <LanguageSelector
          currentLanguage={currentLanguage}
          onSelectLanguage={onSelectLanguage}
          translating={translating}
          onShowOriginal={onShowOriginal}
        />
      </div>

      {/* Main Answer Insight */}
      <p style={{
        fontSize: '1.1875rem',
        lineHeight: 1.7,
        color: '#1e293b',
        fontWeight: '500',
        marginBottom: '1.5rem'
      }}>
        {answerText}
      </p>

      {/* Important Information Cards */}
      {relevantFactors && relevantFactors.length > 0 && (
        <div>
          <h3 style={{
            fontSize: '0.9375rem',
            fontWeight: '700',
            color: '#64748b',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: '0.875rem'
          }}>
            Important Factors
          </h3>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '0.875rem'
          }}>
            {relevantFactors.map((factor, idx) => (
              <div
                key={idx}
                style={{
                  backgroundColor: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: '12px',
                  padding: '1rem 1.125rem',
                  fontSize: '0.9375rem',
                  color: '#334155',
                  lineHeight: 1.5,
                  fontWeight: '500',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '0.5rem'
                }}
              >
                <span style={{ color: '#15803d', fontWeight: '800' }}>•</span>
                <span>{factor}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
