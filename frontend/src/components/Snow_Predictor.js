import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './Snow_Predictor.css';

const SNOWFLAKES = ['❄', '❅', '❆', '✦', '·', '∗'];

const generateSnowflakes = (count) =>
    Array.from({ length: count }, (_, i) => ({
        id: i,
        symbol: SNOWFLAKES[Math.floor(Math.random() * SNOWFLAKES.length)],
        left: `${Math.random() * 100}%`,
        animDuration: `${6 + Math.random() * 14}s`,
        animDelay: `${Math.random() * 10}s`,
        size: `${0.6 + Math.random() * 1.2}rem`,
        opacity: 0.08 + Math.random() * 0.25,
    }));

const FIELDS = [
    { name: 'temperature',    label: 'Temperature',   unit: '°C',   step: '0.1',    icon: '🌡️' },
    { name: 'snowfall_rate',  label: 'Snowfall Rate', unit: 'cm/hr',step: '0.1',    icon: '🌨️' },
    { name: 'snow_depth',     label: 'Snow Depth',    unit: 'cm',   step: '0.1',    icon: '📏' },
    { name: 'elevation',      label: 'Elevation',     unit: 'm',    step: '0.1',    icon: '⛰️' },
    { name: 'latitude',       label: 'Latitude',      unit: '°',    step: '0.0001', icon: '🧭' },
    { name: 'longitude',      label: 'Longitude',     unit: '°',    step: '0.0001', icon: '🧭' },
    { name: 'wind_speed',     label: 'Wind Speed',    unit: 'm/s',  step: '0.1',    icon: '💨' },
    { name: 'humidity',       label: 'Humidity',      unit: '%',    step: '0.1',    icon: '💧' },
    { name: 'pressure',       label: 'Pressure',      unit: 'hPa',  step: '0.1',    icon: '🔵' },
];

const EMPTY = Object.fromEntries(FIELDS.map(f => [f.name, '']));

const EXAMPLES = {
    snow: {
        temperature: '-8', snowfall_rate: '3.5', snow_depth: '45',
        elevation: '2800', latitude: '39.64', longitude: '-106.37',
        wind_speed: '12', humidity: '85', pressure: '980',
    },
    'no-snow': {
        temperature: '28', snowfall_rate: '0', snow_depth: '0',
        elevation: '15', latitude: '17.1167', longitude: '-61.7833',
        wind_speed: '5', humidity: '75', pressure: '1013',
    },
};

function ConfidenceArc({ value }) {
    const r = 52, cx = 64, cy = 64;
    const circum = 2 * Math.PI * r;
    const filled = (value / 100) * circum;
    return (
        <svg viewBox="0 0 128 128" className="arc-svg">
            <circle cx={cx} cy={cy} r={r} fill="none" strokeWidth="8" className="arc-track" />
            <circle
                cx={cx} cy={cy} r={r} fill="none" strokeWidth="8"
                strokeDasharray={`${filled} ${circum}`}
                strokeDashoffset={circum * 0.25}
                strokeLinecap="round"
                className="arc-fill"
                style={{ '--circ': circum, '--filled': filled }}
            />
            <text x="50%" y="50%" dominantBaseline="middle" textAnchor="middle" className="arc-text">
                {value}%
            </text>
            <text x="50%" y="65%" dominantBaseline="middle" textAnchor="middle" className="arc-label">
                CONF.
            </text>
        </svg>
    );
}

function ScoreBar({ value }) {
    const pct = Math.min(100, Math.max(0, ((value + 10) / 20) * 100));
    return (
        <div className="score-bar-wrap">
            <div className="score-bar-track">
                <div className="score-bar-fill" style={{ '--pct': `${pct}%` }} />
                <div className="score-bar-thumb" style={{ '--pct': `${pct}%` }} />
            </div>
            <div className="score-bar-labels">
                <span>No Snow</span>
                <span className="score-val">{value}</span>
                <span>Heavy Snow</span>
            </div>
        </div>
    );
}

const SnowPredictor = () => {
    const [formData, setFormData] = useState(EMPTY);
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [flakes] = useState(() => generateSnowflakes(38));
    const [revealed, setRevealed] = useState(false);
    const resultRef = useRef(null);

    useEffect(() => {
        if (result) {
            setRevealed(false);
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    setRevealed(true);
                    resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                });
            });
        }
    }, [result]);

    const handleChange = (e) =>
        setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setResult(null);
        try {
            const response = await axios.post('http://localhost:5000/api/predict', formData);
            setResult(response.data);
        } catch (err) {
            setError(err.response?.data?.error || 'Prediction failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const isSnow = result?.snow_possible === 'YES';

    return (
        <div className="sp-root">
            {/* Ambient snowfall */}
            <div className="sp-snowfield" aria-hidden="true">
                {flakes.map(f => (
                    <span key={f.id} className="sp-flake"
                        style={{
                            left: f.left, fontSize: f.size, opacity: f.opacity,
                            animationDuration: f.animDuration, animationDelay: f.animDelay,
                        }}>
                        {f.symbol}
                    </span>
                ))}
            </div>

            {/* Glow orbs */}
            <div className="sp-orb sp-orb-1" aria-hidden="true" />
            <div className="sp-orb sp-orb-2" aria-hidden="true" />

            <div className="sp-shell">
                {/* Header */}
                <header className="sp-header">
                    <div className="sp-header-crystal">❄</div>
                    <div className="sp-header-text">
                        <h1>SNOW ORACLE</h1>
                        <p>Atmospheric Snow Probability Engine</p>
                    </div>
                    <div className="sp-header-crystal sp-header-crystal--right">❆</div>
                </header>

                {/* Example presets */}
                <div className="sp-presets">
                    <span className="sp-presets-label">Load Preset →</span>
                    <button className="sp-preset-btn sp-preset-snow"
                        onClick={() => { setFormData(EXAMPLES.snow); setResult(null); setError(null); }}>
                        <span>🏔️</span> Colorado Blizzard
                    </button>
                    <button className="sp-preset-btn sp-preset-tropical"
                        onClick={() => { setFormData(EXAMPLES['no-snow']); setResult(null); setError(null); }}>
                        <span>🌴</span> Tropical Clear
                    </button>
                    <button className="sp-preset-btn sp-preset-clear"
                        onClick={() => { setFormData(EMPTY); setResult(null); setError(null); }}>
                        <span>✕</span> Reset
                    </button>
                </div>

                {/* Form */}
                <form className="sp-form" onSubmit={handleSubmit}>
                    <div className="sp-grid">
                        {FIELDS.map((field, i) => (
                            <div className="sp-field" key={field.name} style={{ '--idx': i }}>
                                <label className="sp-label">
                                    <span className="sp-label-icon">{field.icon}</span>
                                    {field.label}
                                </label>
                                <div className="sp-input-wrap">
                                    <input
                                        type="number"
                                        step={field.step}
                                        name={field.name}
                                        value={formData[field.name]}
                                        onChange={handleChange}
                                        placeholder="—"
                                        required
                                        className="sp-input"
                                    />
                                    <span className="sp-unit">{field.unit}</span>
                                </div>
                            </div>
                        ))}
                    </div>

                    <button className={`sp-submit ${loading ? 'sp-submit--loading' : ''}`} type="submit" disabled={loading}>
                        {loading ? (
                            <>
                                <span className="sp-spinner">❄</span>
                                Consulting the Atmosphere…
                            </>
                        ) : (
                            <>
                                <span>❄</span> Predict Snow Possibility
                            </>
                        )}
                    </button>
                </form>

                {/* Error */}
                {error && (
                    <div className="sp-error">
                        <span className="sp-error-icon">⚠</span>
                        <span>{error}</span>
                    </div>
                )}

                {/* Result */}
                {result && (
                    <div ref={resultRef} className={`sp-result ${isSnow ? 'sp-result--snow' : 'sp-result--clear'} ${revealed ? 'sp-result--visible' : ''}`}>
                        <div className="sp-result-badge">
                            {isSnow ? (
                                <span className="sp-result-icon sp-result-icon--snow">❄</span>
                            ) : (
                                <span className="sp-result-icon sp-result-icon--sun">☀</span>
                            )}
                            <div className="sp-result-verdict">
                                <h2>{isSnow ? 'Snow Possible' : 'No Snow'}</h2>
                                <p className="sp-result-sub">
                                    {isSnow ? 'Conditions support snowfall' : 'Conditions do not support snowfall'}
                                </p>
                            </div>
                        </div>

                        <div className="sp-result-metrics">
                            <div className="sp-metric">
                                <p className="sp-metric-label">Snow Score</p>
                                <ScoreBar value={result.snow_score} />
                            </div>

                            <div className="sp-metric sp-metric--arc">
                                <ConfidenceArc value={result.confidence} />
                            </div>
                        </div>

                        <div className="sp-result-reason">
                            <span className="sp-result-reason-icon">📋</span>
                            <p>{result.reason}</p>
                        </div>

                        {isSnow && (
                            <div className="sp-result-particles" aria-hidden="true">
                                {Array.from({ length: 12 }).map((_, i) => (
                                    <span key={i} className="sp-result-particle" style={{ '--i': i }}>❄</span>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                <footer className="sp-footer">
                    Powered by atmospheric ML · Real-time snow prediction
                </footer>
            </div>
        </div>
    );
};

export default SnowPredictor;