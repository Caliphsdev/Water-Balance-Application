# Supabase Email Setup for Feedback Notifications

This document explains how to set up email notifications for feedback submissions.

## Option 1: Supabase Edge Function (Recommended)

### Step 1: Create Edge Function in Supabase Dashboard

1. Go to your Supabase project
2. Navigate to **Database** → **Functions**
3. Click **Create a new function**
4. Name it: `send_feedback_email`
5. Use this SQL:

```sql
CREATE OR REPLACE FUNCTION send_feedback_email(
  email_data jsonb
)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  result json;
BEGIN
  -- This uses Supabase's built-in email service
  -- Configure your email settings in Supabase Dashboard → Settings → Auth → Email Templates
  
  -- For now, just log the email (you can extend this with actual email service)
  INSERT INTO feedback_email_log (
    recipient,
    subject,
    body,
    sent_at
  ) VALUES (
    email_data->>'to',
    email_data->>'subject',
    email_data->>'body',
    NOW()
  );
  
  RETURN json_build_object('success', true, 'message', 'Email queued');
END;
$$;
```

### Step 2: Create Email Log Table

```sql
CREATE TABLE IF NOT EXISTS feedback_email_log (
  id bigserial PRIMARY KEY,
  recipient text NOT NULL,
  subject text NOT NULL,
  body text NOT NULL,
  sent_at timestamptz DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE feedback_email_log ENABLE ROW LEVEL SECURITY;

-- Policy: Only service role can insert
CREATE POLICY "Service role can insert email logs"
  ON feedback_email_log
  FOR INSERT
  TO service_role
  WITH CHECK (true);
```

## Option 2: Direct Email Integration

If you want actual email sending, integrate with a service:

### A. Using Resend (Recommended - Free tier: 3,000 emails/month)

1. Sign up at https://resend.com
2. Get your API key
3. Update the Edge Function:

```sql
CREATE OR REPLACE FUNCTION send_feedback_email(
  email_data jsonb
)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  result json;
  resend_api_key text := 're_YOUR_API_KEY_HERE';
BEGIN
  -- Call Resend API via HTTP extension
  SELECT content::json INTO result
  FROM http((
    'POST',
    'https://api.resend.com/emails',
    ARRAY[
      http_header('Authorization', 'Bearer ' || resend_api_key),
      http_header('Content-Type', 'application/json')
    ],
    'application/json',
    json_build_object(
      'from', 'Water Balance <noreply@yourdomain.com>',
      'to', ARRAY[email_data->>'to'],
      'subject', email_data->>'subject',
      'text', email_data->>'body'
    )::text
  )::http_request);
  
  RETURN result;
END;
$$;
```

**Note:** You need to enable the `http` extension first:
```sql
CREATE EXTENSION IF NOT EXISTS http;
```

### B. Using SMTP (Gmail, Outlook, etc.)

For SMTP, you'll need to use a Supabase Edge Function (Deno) instead of SQL:

1. In Supabase Dashboard → Edge Functions
2. Create new function `send-feedback-email`
3. Use this code:

```typescript
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { SMTPClient } from 'https://deno.land/x/denomailer@1.6.0/mod.ts'

serve(async (req) => {
  try {
    const { to, subject, body } = await req.json()
    
    const client = new SMTPClient({
      connection: {
        hostname: 'smtp.gmail.com',
        port: 465,
        tls: true,
        auth: {
          username: 'your-email@gmail.com',
          password: 'your-app-password', // Use App Password, not regular password
        },
      },
    })
    
    await client.send({
      from: 'Water Balance <your-email@gmail.com>',
      to: to,
      subject: subject,
      content: body,
    })
    
    await client.close()
    
    return new Response(
      JSON.stringify({ success: true }),
      { headers: { 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    )
  }
})
```

## Option 3: Disable Email (Use Supabase Dashboard Only)

If you prefer to just check feedback in Supabase Dashboard:

1. Open `src/services/feedback_service.py`
2. Comment out the email notification call:

```python
# 2. Send email notification
# self._send_email_notification(...)
```

You can then view feedback in:
- Supabase Dashboard → Table Editor → `feature_requests`

## Recommended Setup

**For Production:**
1. Use **Resend** for reliable email delivery (easiest setup)
2. Keep Supabase storage for tracking/analytics
3. Check feedback in Supabase Dashboard regularly

**For Testing:**
- Use Option 3 (disable email) and just check Supabase Dashboard

## Update Company Email

In `src/services/feedback_service.py`, line 26, change:

```python
FEEDBACK_EMAIL = "feedback@tworiversplatinum.com"  # Update with your actual email
```

To your actual company email address.
