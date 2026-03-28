/** TypeScript interfaces matching backend Pydantic models. */

export interface IntakeResult {
  situation_type: 'medical' | 'accident' | 'disaster' | 'general';
  severity: 'critical' | 'high' | 'medium' | 'low';
  entities: string[];
  symptoms_or_damage: string[];
  location_cues: string[];
  time_sensitivity: string;
  raw_summary: string;
}

export interface ActionItem {
  priority: number;
  action: string;
  reasoning: string;
  confidence: number;
  source: string;
  do_not: string;
}

export interface ActionPlan {
  situation_summary: string;
  triage_level: 'RED' | 'YELLOW' | 'GREEN' | 'BLACK';
  verified_actions: ActionItem[];
  what_not_to_do: string[];
  call_emergency: boolean;
  emergency_number: string;
  verification_sources: string[];
  confidence_overall: number;
}

export interface AnalysisResponse {
  session_id: string;
  intake?: IntakeResult;
  action_plan: ActionPlan;
}

export interface AnalysisError {
  detail: string;
}
