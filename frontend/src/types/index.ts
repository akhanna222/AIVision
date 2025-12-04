// Type definitions for AIVision OCR Frontend

export interface Account {
  id: number;
  name: string;
  email: string;
  plan: 'free' | 'starter' | 'professional' | 'enterprise';
  is_active: boolean;
  api_token: string;
  total_extractions: number;
  monthly_extractions: number;
  monthly_limit: number;
  default_vision_model: string;
}

export interface Country {
  id: number;
  code: string;
  name: string;
  is_active: boolean;
  is_default: boolean;
}

export interface FieldDefinition {
  field_id: string;
  field_name: string;
  field_type: 'text' | 'number' | 'date' | 'currency' | 'boolean' | 'address' | 'phone' | 'email' | 'percentage';
  required: boolean;
  description: string;
  validation_rules?: Record<string, any>;
  examples?: string[];
  extraction_hints?: string;
}

export interface Template {
  id: number;
  template_id: string;
  template_name: string;
  category: string;
  country_id: number;
  description?: string;
  version: string;
  fields: FieldDefinition[];
  page_structure?: Record<string, any>;
  tags?: string[];
  is_custom: boolean;
  is_active: boolean;
  usage_count: number;
  avg_confidence: number;
  avg_completeness: number;
}

export interface ExtractedField {
  field_id: string;
  field_name: string;
  value: string | null;
  confidence: number;
  extracted: boolean;
  page_number?: number;
  bounding_box?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  validation_errors?: string[];
}

export interface ValidationResult {
  is_valid: boolean;
  completeness_score: number;
  average_confidence: number;
  missing_required_fields: string[];
  low_confidence_fields: string[];
  validation_errors: Array<{
    field_id: string;
    error: string;
  }>;
  quality_grade: 'A' | 'B' | 'C' | 'D' | 'F';
}

export interface Extraction {
  extraction_id: string;
  filename: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'partial';
  quality_grade?: 'A' | 'B' | 'C' | 'D' | 'F';
  completeness_score: number;
  average_confidence: number;
  created_at: string;
  template_name: string;
  template_id: string;
  category: string;
  country: string;
  total_pages: number;
  file_size_bytes: number;
  extracted_fields: ExtractedField[];
  validation: ValidationResult;
  processing: {
    vision_model_used: string;
    processing_time_ms: number;
    cost_usd: number;
    pages_processed: number;
    fallback_used: boolean;
    retry_count: number;
  };
  auto_tags?: string[];
  detected_category?: string;
  detected_country?: string;
}

export interface DashboardStats {
  period_days: number;
  overview: {
    total_extractions: number;
    completed: number;
    success_rate: number;
    avg_confidence: number;
    total_cost_usd: number;
  };
  recent_extractions: Array<{
    extraction_id: string;
    filename: string;
    status: string;
    quality_grade?: string;
    created_at: string;
  }>;
  model_usage: Record<string, {
    count: number;
    total_pages: number;
    total_cost: number;
    avg_time_ms: number;
  }>;
  account_usage: {
    monthly_extractions: number;
    monthly_limit: number;
    remaining: number;
    total_all_time: number;
  };
}

export interface BatchExtractionRequest {
  files: File[];
  template_id?: string;
  vision_model: string;
  auto_detect: boolean;
  confidence_threshold: number;
}

export interface BatchExtractionResult {
  batch_id: string;
  total_documents: number;
  completed: number;
  failed: number;
  pending: number;
  extractions: Extraction[];
  total_processing_time_ms: number;
  total_cost_usd?: number;
}

export interface WebhookConfig {
  id: number;
  url: string;
  events: string[];
  is_active: boolean;
  secret?: string;
  created_at: string;
}
