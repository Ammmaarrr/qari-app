-- Qari App Database Initialization Script
-- Run on first database creation

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Recording sessions table
CREATE TABLE IF NOT EXISTS recording_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    surah INTEGER,
    ayah INTEGER,
    audio_path VARCHAR(500),
    transcription TEXT,
    matched_surah INTEGER,
    matched_ayah INTEGER,
    match_confidence DECIMAL(4, 3),
    overall_score DECIMAL(4, 3),
    processing_time_seconds DECIMAL(6, 3),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Detected errors table
CREATE TABLE IF NOT EXISTS detected_errors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES recording_sessions(id) ON DELETE CASCADE,
    error_type VARCHAR(50) NOT NULL,
    letter VARCHAR(10),
    expected VARCHAR(50),
    detected VARCHAR(50),
    start_time DECIMAL(8, 3),
    end_time DECIMAL(8, 3),
    confidence DECIMAL(4, 3),
    severity VARCHAR(20),
    suggestion TEXT,
    correction_audio_url VARCHAR(500),
    word_index INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Human reviews table
CREATE TABLE IF NOT EXISTS human_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES recording_sessions(id) ON DELETE CASCADE,
    reviewer_id VARCHAR(255) NOT NULL,
    is_correct BOOLEAN,
    overall_assessment VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Error reviews (part of human review)
CREATE TABLE IF NOT EXISTS error_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    review_id UUID REFERENCES human_reviews(id) ON DELETE CASCADE,
    error_id UUID REFERENCES detected_errors(id) ON DELETE CASCADE,
    is_correct BOOLEAN NOT NULL,
    actual_error_type VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Correction audio samples table
CREATE TABLE IF NOT EXISTS correction_audio (
    id VARCHAR(50) PRIMARY KEY,
    letter VARCHAR(10),
    description TEXT,
    audio_path VARCHAR(500),
    duration_seconds DECIMAL(6, 3),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User progress tracking
CREATE TABLE IF NOT EXISTS user_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    sessions_count INTEGER DEFAULT 0,
    total_minutes INTEGER DEFAULT 0,
    average_score DECIMAL(4, 3),
    errors_by_type JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON recording_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON recording_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_errors_session_id ON detected_errors(session_id);
CREATE INDEX IF NOT EXISTS idx_errors_type ON detected_errors(error_type);
CREATE INDEX IF NOT EXISTS idx_reviews_session_id ON human_reviews(session_id);
CREATE INDEX IF NOT EXISTS idx_progress_user_date ON user_progress(user_id, date);

-- Insert default correction audio entries
INSERT INTO correction_audio (id, letter, description, audio_path) VALUES
    ('qa_01', 'ق', 'Letter Qaf pronounced correctly', 'corrections/qaf_correct.mp3'),
    ('madd_natural', 'ا', 'Natural madd (2 counts)', 'corrections/madd_natural.mp3'),
    ('ghunnah_noon', 'ن', 'Noon with ghunnah', 'corrections/ghunnah_noon.mp3'),
    ('qalqalah_qaf', 'ق', 'Qaf with qalqalah', 'corrections/qalqalah_qaf.mp3'),
    ('qalqalah_ba', 'ب', 'Ba with qalqalah', 'corrections/qalqalah_ba.mp3'),
    ('qalqalah_jeem', 'ج', 'Jeem with qalqalah', 'corrections/qalqalah_jeem.mp3'),
    ('qalqalah_dal', 'د', 'Dal with qalqalah', 'corrections/qalqalah_dal.mp3'),
    ('qalqalah_ta', 'ط', 'Ta with qalqalah', 'corrections/qalqalah_ta.mp3')
ON CONFLICT (id) DO NOTHING;

-- Grant permissions (for production, adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO qari_user;
