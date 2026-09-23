export type Severity =
  | "CRITICAL"
  | "HIGH"
  | "MEDIUM"
  | "LOW";

export type IssueCategory =
  | "BUG"
  | "SECURITY"
  | "DESIGN"
  | "PERFORMANCE"
  | "CODE_QUALITY";

export type FindingStatus =
  | "INTRODUCED"
  | "MODIFIED"
  | "PRE_EXISTING";

export interface ReviewIssue {
  category: IssueCategory;
  severity: Severity;

  file: string | null;
  line_start: number | null;
  line_end: number | null;

  title: string;
  description: string;
  suggestion: string;

  confidence: number;

  source: string | null;
  rule_id: string | null;
  pr_status: FindingStatus | null;
}

export interface ReviewSummary {
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface ReviewResponse {
  id: string;
  created_at: string;

  critical: number;
  high: number;
  medium: number;
  low: number;

  issues: ReviewIssue[];
}