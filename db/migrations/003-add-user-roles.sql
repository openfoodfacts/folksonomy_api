-- Add user role columns to auth table
-- depends: 002-remove-trailing-spaces-in-values

ALTER TABLE auth ADD COLUMN admin BOOLEAN DEFAULT FALSE;
ALTER TABLE auth ADD COLUMN moderator BOOLEAN DEFAULT FALSE;
ALTER TABLE auth ADD COLUMN "user" BOOLEAN DEFAULT TRUE;
