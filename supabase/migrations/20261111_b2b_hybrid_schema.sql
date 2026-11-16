-- ============================================================================
-- Supabase / PostgreSQL Migration: Hybrid B2C & B2B Luxury Rosaries Architecture
-- Date: 2026-11-11
-- Description: Unifies backend inventory while strictly isolating wholesale vs
--              retail catalogs, MOQ validation, and B2B corporate verification.
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Create Enums for Roles and Sales Channels
DO $$ BEGIN
  CREATE TYPE user_role AS ENUM ('b2c_user', 'b2b_pending', 'b2b_approved', 'admin');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE TYPE sales_channel_type AS ENUM ('b2c', 'b2b', 'both');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

-- 2. Create / Extend Public Profiles Table (Linked to auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name TEXT NOT NULL,
  phone TEXT,
  role user_role NOT NULL DEFAULT 'b2c_user',
  
  -- Corporate B2B Verification Data
  company_name TEXT,
  commercial_register TEXT,
  tax_id TEXT,
  b2b_notes TEXT,
  approved_at TIMESTAMPTZ,
  approved_by UUID REFERENCES auth.users(id),
  
  created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 3. Extend Products Table for B2B / B2C Dual Partitioning
ALTER TABLE public.products 
  ADD COLUMN IF NOT EXISTS sales_channel sales_channel_type NOT NULL DEFAULT 'both',
  ADD COLUMN IF NOT EXISTS price_b2c NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
  ADD COLUMN IF NOT EXISTS price_b2b NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
  ADD COLUMN IF NOT EXISTS b2b_moq INTEGER NOT NULL DEFAULT 1,
  ADD COLUMN IF NOT EXISTS stock_quantity INTEGER NOT NULL DEFAULT 1,
  ADD COLUMN IF NOT EXISTS sku TEXT UNIQUE;

-- Enforce Valid Constraints
ALTER TABLE public.products
  DROP CONSTRAINT IF EXISTS chk_positive_prices,
  DROP CONSTRAINT IF EXISTS chk_b2b_moq_min;

ALTER TABLE public.products
  ADD CONSTRAINT chk_positive_prices CHECK (price_b2c >= 0 AND price_b2b >= 0),
  ADD CONSTRAINT chk_b2b_moq_min CHECK (b2b_moq >= 1);

CREATE INDEX IF NOT EXISTS idx_products_sales_channel ON public.products(sales_channel);
CREATE INDEX IF NOT EXISTS idx_products_sku ON public.products(sku);

-- 4. Enable Row Level Security (RLS)
ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Helper to safely extract user role from profile in RLS context
CREATE OR REPLACE FUNCTION public.current_user_role()
RETURNS user_role AS $$
  SELECT COALESCE(
    (SELECT role FROM public.profiles WHERE id = auth.uid()),
    'b2c_user'::user_role
  );
$$ LANGUAGE sql STABLE SECURITY DEFINER;

-- ----------------------------------------------------------------------------
-- RLS Policy A: Retail / B2C Product Access (Anonymous + b2c_user)
-- Can ONLY read products flagged as 'b2c' or 'both'
-- ----------------------------------------------------------------------------
DROP POLICY IF EXISTS "b2c_product_read_policy" ON public.products;
CREATE POLICY "b2c_product_read_policy"
ON public.products
FOR SELECT
USING (
  (auth.role() = 'anon' OR public.current_user_role() IN ('b2c_user', 'b2b_pending'))
  AND sales_channel IN ('b2c', 'both')
);

-- ----------------------------------------------------------------------------
-- RLS Policy B: Approved Wholesale Access (b2b_approved)
-- Can ONLY read products flagged as 'b2b' or 'both'
-- ----------------------------------------------------------------------------
DROP POLICY IF EXISTS "b2b_approved_product_read_policy" ON public.products;
CREATE POLICY "b2b_approved_product_read_policy"
ON public.products
FOR SELECT
USING (
  public.current_user_role() = 'b2b_approved'
  AND sales_channel IN ('b2b', 'both')
);

-- ----------------------------------------------------------------------------
-- RLS Policy C: Admin Access (Full CRUD)
-- ----------------------------------------------------------------------------
DROP POLICY IF EXISTS "admin_all_products_policy" ON public.products;
CREATE POLICY "admin_all_products_policy"
ON public.products
FOR ALL
USING (public.current_user_role() = 'admin');

-- ----------------------------------------------------------------------------
-- Profile Security Policies
-- ----------------------------------------------------------------------------
DROP POLICY IF EXISTS "users_read_own_profile" ON public.profiles;
CREATE POLICY "users_read_own_profile"
ON public.profiles
FOR SELECT
USING (auth.uid() = id OR public.current_user_role() = 'admin');

DROP POLICY IF EXISTS "users_update_own_profile" ON public.profiles;
CREATE POLICY "users_update_own_profile"
ON public.profiles
FOR UPDATE
USING (auth.uid() = id AND public.current_user_role() != 'admin')
WITH CHECK (
  role = (SELECT role FROM public.profiles WHERE id = auth.uid())
);
