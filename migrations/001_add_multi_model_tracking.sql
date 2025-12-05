-- Migration: Add multi-model extraction tracking fields
-- Date: 2025-12-05
-- Description: Adds columns to track multi-model extraction attempts and results

-- Add multi-model extraction tracking columns to extractions table
ALTER TABLE extractions
ADD COLUMN IF NOT EXISTS extraction_strategy VARCHAR(20),
ADD COLUMN IF NOT EXISTS field_model_map JSON,
ADD COLUMN IF NOT EXISTS extraction_attempts JSON,
ADD COLUMN IF NOT EXISTS models_tried JSON DEFAULT '[]'::json,
ADD COLUMN IF NOT EXISTS extraction_summary TEXT;

-- Add comment for documentation
COMMENT ON COLUMN extractions.extraction_strategy IS 'Strategy used: sequential, parallel, or hybrid';
COMMENT ON COLUMN extractions.field_model_map IS 'Maps field names to the model that extracted them';
COMMENT ON COLUMN extractions.extraction_attempts IS 'All model extraction attempts with details';
COMMENT ON COLUMN extractions.models_tried IS 'List of all models tried during extraction';
COMMENT ON COLUMN extractions.extraction_summary IS 'User-friendly summary of extraction attempts';
