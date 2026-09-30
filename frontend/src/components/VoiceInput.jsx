import React, { useState, useEffect, useRef } from 'react';
import { Mic, Square, Volume2 } from 'lucide-react';

const SPEECH_LANGUAGES = [
  { code: 'te-IN', label: 'తెలుగు — Telugu', shortName: 'Telugu' },
  { code: 'hi-IN', label: 'हिन्दी — Hindi', shortName: 'Hindi' },
  { code: 'en-IN', label: 'English', shortName: 'English' }
];

export const VoiceInput = ({ onSpeechConverted }) => {
  const [selectedLanguage, setSelectedLanguage] = useState('te-IN');
  const [isListening, setIsListening] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [isSupported, setIsSupported] = useState(true);
  const recognitionRef = useRef(null);

  const currentLangObj = SPEECH_LANGUAGES.find(l => l.code === selectedLanguage) || SPEECH_LANGUAGES[0];

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setIsSupported(false);
      setStatusMessage('Voice input is not supported in this browser. Please type your question.');
      return;
    }

    try {
      const rec = new SpeechRecognition();
      rec.continuous = false;
      rec.interimResults = false;
      rec.lang = selectedLanguage;

      rec.onstart = () => {
        setIsListening(true);
        setStatusMessage(`Listening in ${currentLangObj.shortName}... Speak your question clearly.`);
      };

      rec.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        if (transcript && transcript.trim()) {
          onSpeechConverted(transcript.trim());
          setStatusMessage(`✓ Voice converted to ${currentLangObj.shortName} text. Review your question and click Ask AgriGraph!`);
        }
      };

      rec.onerror = (event) => {
        setIsListening(false);
        if (event.error === 'no-speech') {
          setStatusMessage('Could not recognize the spoken question. Please try again or type your question.');
        } else if (event.error === 'not-allowed') {
          setStatusMessage('Microphone access denied. Please enable microphone permissions in your browser.');
        } else {
          setStatusMessage('Voice input could not be understood. Please try again.');
        }
      };

      rec.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = rec;
    } catch (e) {
      setIsSupported(false);
      setStatusMessage('Voice input is not supported in this browser. Please type your question.');
    }

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch (e) {}
      }
    };
  }, [selectedLanguage, onSpeechConverted, currentLangObj.shortName]);

  const handleLanguageChange = (e) => {
    const newLang = e.target.value;
    setSelectedLanguage(newLang);
    const langObj = SPEECH_LANGUAGES.find(l => l.code === newLang);
    setStatusMessage(`Language set to ${langObj?.shortName}. Click Speak to ask your question.`);
  };

  const toggleListening = () => {
    if (!isSupported || !recognitionRef.current) {
      setStatusMessage('Voice input is not supported in this browser. Please type your question.');
      return;
    }

    if (isListening) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
      setIsListening(false);
      setStatusMessage('Microphone stopped.');
    } else {
      setStatusMessage(`Initializing microphone in ${currentLangObj.shortName}...`);
      try {
        recognitionRef.current.lang = selectedLanguage;
        recognitionRef.current.start();
      } catch (e) {
        setIsListening(false);
        setStatusMessage('Voice input could not be understood. Please try again.');
      }
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
        {/* Language You Speak Selector */}
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.375rem' }}>
          <label htmlFor="voice-lang-select" style={{ fontSize: '0.875rem', fontWeight: '700', color: '#475569' }}>
            Language you speak:
          </label>
          <select
            id="voice-lang-select"
            value={selectedLanguage}
            onChange={handleLanguageChange}
            disabled={isListening}
            style={{
              padding: '0.45rem 0.75rem',
              borderRadius: '8px',
              border: '1.5px solid #cbd5e1',
              backgroundColor: '#ffffff',
              fontSize: '0.875rem',
              fontWeight: '600',
              color: '#0f172a',
              cursor: isListening ? 'not-allowed' : 'pointer',
              outline: 'none'
            }}
          >
            {SPEECH_LANGUAGES.map(lang => (
              <option key={lang.code} value={lang.code}>
                {lang.label}
              </option>
            ))}
          </select>
        </div>

        {/* Speak / Stop Button */}
        <button
          type="button"
          onClick={toggleListening}
          disabled={!isSupported}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            backgroundColor: isListening ? '#fef2f2' : '#ffffff',
            color: isListening ? '#b91c1c' : '#15803d',
            border: isListening ? '2px solid #ef4444' : '2px solid #86efac',
            padding: '0.5rem 1.25rem',
            borderRadius: '10px',
            fontSize: '0.9375rem',
            fontWeight: '700',
            cursor: !isSupported ? 'not-allowed' : 'pointer',
            transition: 'all 0.15s ease-in-out'
          }}
          onMouseEnter={(e) => {
            if (!isListening && isSupported) {
              e.currentTarget.style.backgroundColor = '#f0fdf4';
              e.currentTarget.style.borderColor = '#15803d';
            }
          }}
          onMouseLeave={(e) => {
            if (!isListening && isSupported) {
              e.currentTarget.style.backgroundColor = '#ffffff';
              e.currentTarget.style.borderColor = '#86efac';
            }
          }}
        >
          {isListening ? (
            <>
              <Square size={18} color="#dc2626" fill="#dc2626" />
              <span>Stop</span>
            </>
          ) : (
            <>
              <Mic size={18} color="#15803d" />
              <span>Speak</span>
            </>
          )}
        </button>
      </div>

      {/* Real-time status / confirmation message */}
      {statusMessage && (
        <div style={{
          fontSize: '0.8125rem',
          color: isListening ? '#b91c1c' : (statusMessage.startsWith('✓') ? '#15803d' : '#475569'),
          fontWeight: '600',
          display: 'flex',
          alignItems: 'center',
          gap: '0.375rem'
        }}>
          {isListening && (
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: '#ef4444',
              display: 'inline-block',
              animation: 'pulse 1s infinite'
            }} />
          )}
          <span>{statusMessage}</span>
        </div>
      )}
    </div>
  );
};
