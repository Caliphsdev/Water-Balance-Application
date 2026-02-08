-- ============================================================================
-- Water Balance Dashboard - Supabase Schema
-- 
-- Run this SQL in your Supabase SQL Editor to create all required tables.
-- This creates tables for: licenses, updates, notifications, feedback
-- 
-- Prerequisites:
--   1. Create a Supabase project at https://supabase.com
--   2. Go to SQL Editor in your dashboard
--   3. Paste this entire file and click "Run"
-- ============================================================================

-- Enable UUID extension (usually already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- DROP EXISTING OBJECTS (for clean re-run)
-- Run in reverse dependency order with CASCADE to handle policies
-- ============================================================================

-- Drop triggers first
DROP TRIGGER IF EXISTS update_feature_requests_updated_at ON feature_requests;
DROP TRIGGER IF EXISTS update_licenses_updated_at ON licenses;

-- Drop function
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- Drop all tables with CASCADE (this also drops policies, indexes, etc.)
DROP TABLE IF EXISTS notification_reads CASCADE;
DROP TABLE IF EXISTS feature_requests CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS app_updates CASCADE;
DROP TABLE IF EXISTS licenses CASCADE;

-- ============================================================================
-- 1. LICENSES TABLE
-- Stores license keys with HWID binding and tier information
-- ============================================================================
CREATE TABLE licenses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    license_key TEXT NOT NULL UNIQUE,
    hwid TEXT,
    tier TEXT NOT NULL DEFAULT 'standard' CHECK (tier IN ('developer', 'premium', 'standard', 'free_trial')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'expired', 'revoked')),
    expires_at TIMESTAMPTZ,
    last_validated TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for fast lookups
CREATE INDEX idx_licenses_key ON licenses(license_key);
CREATE INDEX idx_licenses_hwid ON licenses(hwid);
CREATE INDEX idx_licenses_status ON licenses(status);

-- Row Level Security
ALTER TABLE licenses ENABLE ROW LEVEL SECURITY;

-- Policy: Anyone can read their own license (by key)
CREATE POLICY "Users can read own license" ON licenses
    FOR SELECT USING (true);  -- App validates with license_key

-- Policy: Only service role can insert/update
CREATE POLICY "Service role manages licenses" ON licenses
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- 2. APP_UPDATES TABLE
-- Stores update releases with tier restrictions
-- ============================================================================
CREATE TABLE app_updates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version TEXT NOT NULL UNIQUE,
    min_tiers TEXT[] NOT NULL DEFAULT ARRAY['developer', 'premium', 'standard', 'free_trial'],
    download_url TEXT NOT NULL,
    release_notes TEXT,
    file_hash TEXT,  -- SHA256 for integrity verification
    file_size BIGINT,
    is_mandatory BOOLEAN NOT NULL DEFAULT false,
    published_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_updates_version ON app_updates(version);
CREATE INDEX idx_updates_published ON app_updates(published_at DESC);

-- Row Level Security
ALTER TABLE app_updates ENABLE ROW LEVEL SECURITY;

-- Policy: Anyone can read updates
CREATE POLICY "Public read updates" ON app_updates
    FOR SELECT USING (true);

-- Policy: Only service role can manage updates
CREATE POLICY "Service role manages updates" ON app_updates
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- 3. NOTIFICATIONS TABLE
-- In-app notifications with tier targeting
-- ============================================================================
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type TEXT NOT NULL CHECK (type IN ('update', 'announcement', 'alert', 'maintenance')),
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    target_tiers TEXT[] NOT NULL DEFAULT ARRAY['developer', 'premium', 'standard', 'free_trial'],
    action_url TEXT,  -- Optional URL to open on click
    published_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,  -- NULL means never expires
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_notifications_type ON notifications(type);
CREATE INDEX idx_notifications_published ON notifications(published_at DESC);

-- Row Level Security
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- Policy: Anyone can read notifications
CREATE POLICY "Public read notifications" ON notifications
    FOR SELECT USING (true);

-- Policy: Only service role can manage
CREATE POLICY "Service role manages notifications" ON notifications
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- 4. NOTIFICATION_READS TABLE
-- Tracks which notifications have been read by which HWID
-- ============================================================================
CREATE TABLE notification_reads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    notification_id UUID NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    hwid TEXT NOT NULL,
    read_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(notification_id, hwid)
);

-- Indexes
CREATE INDEX idx_reads_hwid ON notification_reads(hwid);
CREATE INDEX idx_reads_notification ON notification_reads(notification_id);

-- Row Level Security
ALTER TABLE notification_reads ENABLE ROW LEVEL SECURITY;

-- Policy: Anyone can read/insert their own read status
CREATE POLICY "Users manage own reads" ON notification_reads
    FOR ALL USING (true);

-- ============================================================================
-- 5. FEATURE_REQUESTS TABLE
-- Bug reports and feature requests from users
-- ============================================================================
CREATE TABLE feature_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type TEXT NOT NULL CHECK (type IN ('bug', 'feature', 'general')),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    email TEXT,  -- Optional contact email
    hwid TEXT,
    license_key TEXT,
    app_version TEXT,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed', 'wont_fix')),
    admin_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_requests_type ON feature_requests(type);
CREATE INDEX idx_requests_status ON feature_requests(status);
CREATE INDEX idx_requests_created ON feature_requests(created_at DESC);

-- Row Level Security
ALTER TABLE feature_requests ENABLE ROW LEVEL SECURITY;

-- Policy: Anyone can insert feedback
CREATE POLICY "Users can submit feedback" ON feature_requests
    FOR INSERT WITH CHECK (true);

-- Policy: Service role can read all
CREATE POLICY "Service role reads feedback" ON feature_requests
    FOR SELECT USING (auth.role() = 'service_role');

-- Policy: Service role can update
CREATE POLICY "Service role updates feedback" ON feature_requests
    FOR UPDATE USING (auth.role() = 'service_role');

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for auto-updating updated_at
CREATE TRIGGER update_licenses_updated_at
    BEFORE UPDATE ON licenses
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_feature_requests_updated_at
    BEFORE UPDATE ON feature_requests
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- SAMPLE DATA (for testing)
-- ============================================================================

-- Sample developer license (never expires)
INSERT INTO licenses (license_key, tier, status, notes)
VALUES ('DEV-TEST-2026-0001', 'developer', 'active', 'Development testing license');

-- Sample notification
INSERT INTO notifications (type, title, body, target_tiers)
VALUES (
    'announcement',
    'Welcome to Water Balance Dashboard',
    'Thank you for using our application. Check the Help page for tutorials.',
    ARRAY['developer', 'premium', 'standard', 'free_trial']
);

-- ============================================================================
-- VERIFICATION QUERIES (run after setup to verify)
-- ============================================================================
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
-- SELECT * FROM licenses LIMIT 5;
-- SELECT * FROM notifications LIMIT 5;
