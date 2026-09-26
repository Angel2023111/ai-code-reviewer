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

export interface ReviewHistoryItem {
  id: string;
  created_at: string;
  critical: number;
  high: number;
  medium: number;
  low: number;
  issue_count: number;
}

export interface ReviewHistoryResponse {
  reviews: ReviewHistoryItem[];
}

export interface ReviewJobResponse {
  job_id: string;
  status: string;
  review_id: string | null;
  error_message: string | null;
}

export interface PullRequestIssue {
  id: number;
  category: string;
  severity: string;
  line_start: number | null;
  line_end: number | null;
  title: string;
  description: string;
  suggestion: string;
  confidence: number;
  source: string | null;
  rule_id: string | null;
  pr_status: string | null;
}

export interface PullRequestFile {
  id: number;
  filename: string;
  language: string;
  changed_lines: string;
  issues: PullRequestIssue[];
}

export interface PullRequestReview {
  id: string;
  repository_owner: string;
  repository_name: string;
  pull_number: number;
  head_sha: string;
  created_at: string;
  files: PullRequestFile[];
}