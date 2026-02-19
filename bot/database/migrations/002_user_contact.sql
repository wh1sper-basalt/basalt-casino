-- Add contact fields for deposit: one-time send contact, store phone for admin notifications
ALTER TABLE users ADD COLUMN has_contact_sent INTEGER NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN contact_phone TEXT;
