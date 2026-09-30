import React, { useState, useEffect } from 'react';
import { Header } from '../components/Header';
import { QueryBox } from '../components/QueryBox';
import { AnswerCard } from '../components/AnswerCard';
import { EvidenceCard } from '../components/EvidenceCard';
import { SourceCard } from '../components/SourceCard';
import { ConflictCard } from '../components/ConflictCard';
import { DataQualityCard } from '../components/DataQualityCard';
import { farmerAPI } from '../api/api';
import { Sparkles, History, Loader2, AlertCircle } from 'lucide-react';

const SAMPLE_QUESTIONS = [
  "What diseases affect tomato?",
  "What soil is suitable for tomato?",
  "Why is my tomato crop at high disease risk?",
  "What treatments are available for Early Blight?",
  "What evidence supports Neem Oil Extract?",
  "Are there conflicting recommendations on neem oil?"
];

export const FarmerHome = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [originalResult, setOriginalResult] = useState(null);
  const [displayedResult, setDisplayedResult] = useState(null);
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);
  
  // Translation state
  const [currentLanguage, setCurrentLanguage] = useState('English');
  const [translating, setTranslating] = useState(false);

  // Friendly progress messages during search
  const [progressMsg, setProgressMsg] = useState('Understanding your question...');

  useEffect(() => {
    // Fetch query history on load
    farmerAPI.getHistory()
      .then(res => setHistory(res.data || []))
      .catch(() => {});
  }, []);

  const handleSearch = async (questionToAsk) => {
    const q = questionToAsk || query;
    if (!q.trim()) return;

    setLoading(true);
    setError('');
    setOriginalResult(null);
    setDisplayedResult(null);
    setCurrentLanguage('English');

    // Progressive loading messages
    setProgressMsg('Understanding your question...');
    const t1 = setTimeout(() => setProgressMsg('Finding relevant agricultural information...'), 600);
    const t2 = setTimeout(() => setProgressMsg('Checking evidence and source provenance...'), 1200);
    const t3 = setTimeout(() => setProgressMsg('Preparing your evidence-backed answer...'), 1800);

    try {
      const res = await farmerAPI.submitQuery(q);
      setOriginalResult(res.data);
      setDisplayedResult(res.data);
      // Refresh history
      farmerAPI.getHistory().then(h => setHistory(h.data || [])).catch(() => {});
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not retrieve answer. Please try asking again.');
    } finally {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      setLoading(false);
    }
  };

  const handleSelectLanguage = async (targetLang) => {
    if (targetLang === currentLanguage) return;
    if (targetLang === 'English') {
      setCurrentLanguage('English');
      setDisplayedResult(originalResult);
      return;
    }

    if (!originalResult) return;

    setTranslating(true);
    try {
      // Send complete structured result for comprehensive translation
      const res = await farmerAPI.translate({
        target_language: targetLang,
        result: originalResult
      });

      if (res.data && res.data.translated_result) {
        setDisplayedResult(res.data.translated_result);
      } else if (res.data && res.data.translated_text) {
        setDisplayedResult({
          ...originalResult,
          agricultural_insight: res.data.translated_text
        });
      }
      setCurrentLanguage(targetLang);
    } catch (err) {
      alert('Translation is temporarily unavailable. Your original answer is still available.');
    } finally {
      setTranslating(false);
    }
  };

  const handleShowOriginal = () => {
    setCurrentLanguage('English');
    setDisplayedResult(originalResult);
  };

  const handleSampleClick = (sampleQ) => {
    setQuery(sampleQ);
    handleSearch(sampleQ);
  };

  return (
    <div className="app-container">
      <Header />

      <main className="main-content">
        {/* Welcome Section */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h2 style={{ fontSize: '2rem', fontWeight: '800', color: '#15803d', letterSpacing: '-0.02em' }}>
            Ask About Your Farm
          </h2>
          <p style={{ fontSize: '1.0625rem', color: '#64748b', marginTop: '0.25rem', fontWeight: '500' }}>
            Evidence-grounded knowledge from agricultural research, weather telemetry, and verified field logs.
          </p>
        </div>

        {/* Large Query Box */}
        <QueryBox
          query={query}
          setQuery={setQuery}
          onSearch={() => handleSearch(query)}
          loading={loading}
        />

        {/* Sample Farmer Questions */}
        <div style={{ marginTop: '1.5rem', marginBottom: '2.5rem' }}>
          <p style={{ fontSize: '0.875rem', fontWeight: '700', color: '#64748b', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
            <Sparkles size={16} color="#15803d" />
            Suggested Questions:
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {SAMPLE_QUESTIONS.map((sq, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSampleClick(sq)}
                style={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #cbd5e1',
                  borderRadius: '9999px',
                  padding: '0.5rem 1rem',
                  fontSize: '0.875rem',
                  color: '#334155',
                  fontWeight: '600'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#f0fdf4';
                  e.currentTarget.style.borderColor = '#86efac';
                  e.currentTarget.style.color = '#15803d';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#ffffff';
                  e.currentTarget.style.borderColor = '#cbd5e1';
                  e.currentTarget.style.color = '#334155';
                }}
              >
                {sq}
              </button>
            ))}
          </div>
        </div>

        {/* Loading Progress State */}
        {loading && (
          <div style={{
            backgroundColor: '#ffffff',
            borderRadius: '16px',
            border: '2px dashed #bbf7d0',
            padding: '2.5rem 1.5rem',
            textAlign: 'center',
            marginBottom: '2rem'
          }}>
            <Loader2 size={36} className="spinner" color="#15803d" style={{ margin: '0 auto 1rem' }} />
            <p style={{ fontSize: '1.125rem', fontWeight: '700', color: '#166534', margin: 0 }}>
              {progressMsg}
            </p>
            <p style={{ fontSize: '0.875rem', color: '#64748b', marginTop: '0.5rem' }}>
              Traversing knowledge graph and verifying source citations...
            </p>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div style={{
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            color: '#b91c1c',
            padding: '1rem 1.25rem',
            borderRadius: '12px',
            fontSize: '1rem',
            marginBottom: '2rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.625rem'
          }}>
            <AlertCircle size={22} />
            <span>{error}</span>
          </div>
        )}

        {/* Results Section */}
        {displayedResult && !loading && (
          <div>
            {/* 1. AgriGraph Answer Card with Complete Translation */}
            <AnswerCard
              answerText={displayedResult.agricultural_insight}
              relevantFactors={displayedResult.relevant_factors}
              matchedCrop={displayedResult.matched_crop}
              matchedDisease={displayedResult.matched_disease}
              currentLanguage={currentLanguage}
              onSelectLanguage={handleSelectLanguage}
              translating={translating}
              onShowOriginal={handleShowOriginal}
              generationMode={displayedResult.generation_mode}
              provider={displayedResult.provider}
              model={displayedResult.model}
              fallbackReason={displayedResult.fallback_reason}
            />

            {/* 2. Connected Knowledge Evidence */}
            <EvidenceCard evidence={displayedResult.evidence} />

            {/* 3. Conflicting Evidence Warning */}
            <ConflictCard conflicts={displayedResult.conflicts} />

            {/* 4. Sourced Citations / Provenance */}
            <SourceCard sources={displayedResult.sources} />

            {/* 5. Data Quality / Excluded Sensor Telemetry */}
            <DataQualityCard warnings={displayedResult.data_quality_warnings} />
          </div>
        )}

        {/* Farmer Query History */}
        {history && history.length > 0 && (
          <div style={{
            marginTop: '3rem',
            backgroundColor: '#ffffff',
            borderRadius: '16px',
            border: '1px solid #e2e8f0',
            padding: '1.5rem',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <History size={18} color="#475569" />
              <h3 style={{ fontSize: '1rem', fontWeight: '700', color: '#334155', margin: 0 }}>
                Recent Questions
              </h3>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {history.slice(0, 5).map((item, idx) => (
                <div
                  key={idx}
                  onClick={() => handleSampleClick(item.query)}
                  style={{
                    padding: '0.625rem 0.875rem',
                    borderRadius: '8px',
                    backgroundColor: '#f8fafc',
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    border: '1px solid #f1f5f9'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f0fdf4'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#f8fafc'}
                >
                  <span style={{ fontSize: '0.875rem', color: '#1e293b', fontWeight: '500' }}>
                    {item.query}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                    {item.matched_crop ? `Crop: ${item.matched_crop}` : ''}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
