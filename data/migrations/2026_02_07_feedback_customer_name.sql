-- Safe migration: add customer_name to feature_requests
-- Run this in Supabase SQL editor (does NOT drop tables).

ALTER TABLE feature_requests
  ADD COLUMN IF NOT EXISTS customer_name TEXT;
