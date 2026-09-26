import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  getPullRequestReview,
} from "../services/api";

import type {
  PullRequestReview,
  PullRequestIssue,
} from "../types/review";

function GitHubPRReviewDetail() {
  const { reviewId } = useParams();
  const navigate = useNavigate();

  const [review, setReview] =
    useState<PullRequestReview | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    async function loadReview() {
      if (!reviewId) {
        setError("Review ID is missing.");
        setLoading(false);
        return;
      }

      try {
        const data =
          await getPullRequestReview(reviewId);

        setReview(data);
      } catch (err) {
        console.error(err);

        setError(
          "Failed to load pull request review.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadReview();
  }, [reviewId]);

  if (loading) {
    return (
      <div className="page">
        <div className="card">
          Loading pull request review...
        </div>
      </div>
    );
  }

  if (error || !review) {
    return (
      <div className="page">
        <button
          className="secondary-button"
          onClick={() => navigate("/")}
        >
          ← Back to Dashboard
        </button>

        <div className="card error-card">
          {error ?? "Review not found."}
        </div>
      </div>
    );
  }

  const allIssues: PullRequestIssue[] =
    review.files.flatMap(
      (file) => file.issues,
    );

  const criticalCount = allIssues.filter(
    (issue) => issue.severity === "CRITICAL",
  ).length;

  const highCount = allIssues.filter(
    (issue) => issue.severity === "HIGH",
  ).length;

  const mediumCount = allIssues.filter(
    (issue) => issue.severity === "MEDIUM",
  ).length;

  const lowCount = allIssues.filter(
    (issue) => issue.severity === "LOW",
  ).length;

  return (
    <div className="page">
      <div className="detail-header">
        <div>
          <button
            className="back-button"
            onClick={() => navigate("/")}
          >
            ← Back to Dashboard
          </button>

          <p className="eyebrow">
            GitHub Pull Request
          </p>

          <h1>
            {review.repository_owner}/
            {review.repository_name}
            {" "}#{review.pull_number}
          </h1>

          <p className="page-subtitle">
            Review ID: {review.id}
          </p>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <span>Critical</span>
          <strong>{criticalCount}</strong>
        </div>

        <div className="stat-card">
          <span>High</span>
          <strong>{highCount}</strong>
        </div>

        <div className="stat-card">
          <span>Medium</span>
          <strong>{mediumCount}</strong>
        </div>

        <div className="stat-card">
          <span>Low</span>
          <strong>{lowCount}</strong>
        </div>
      </div>

      <div className="card pr-meta-card">
        <div className="meta-grid">
          <div>
            <span className="meta-label">
              Repository
            </span>

            <strong>
              {review.repository_owner}/
              {review.repository_name}
            </strong>
          </div>

          <div>
            <span className="meta-label">
              Pull Request
            </span>

            <strong>
              #{review.pull_number}
            </strong>
          </div>

          <div>
            <span className="meta-label">
              Head SHA
            </span>

            <strong className="sha-text">
              {review.head_sha}
            </strong>
          </div>

          <div>
            <span className="meta-label">
              Created
            </span>

            <strong>
              {new Date(
                review.created_at,
              ).toLocaleString()}
            </strong>
          </div>
        </div>
      </div>

      <div className="section-heading">
        <div>
          <p className="eyebrow">
            Analysis Results
          </p>

          <h2>
            {allIssues.length} finding
            {allIssues.length !== 1
              ? "s"
              : ""}
          </h2>
        </div>
      </div>

      {review.files.map((file) => (
        <div
          className="card pr-file-card"
          key={file.id}
        >
          <div className="file-header">
            <div>
              <h3>{file.filename}</h3>

              <span className="file-language">
                {file.language}
              </span>
            </div>

            <span className="file-changes">
              Changed lines: {file.changed_lines}
            </span>
          </div>

          {file.issues.length === 0 ? (
            <div className="no-issues">
              ✓ No issues detected in this file.
            </div>
          ) : (
            <div className="issues-list">
              {file.issues.map((issue) => (
                <div
                  className="issue-card"
                  key={issue.id}
                >
                  <div className="issue-top">
                    <div>
                      <span
                        className={`severity-badge severity-${issue.severity.toLowerCase()}`}
                      >
                        {issue.severity}
                      </span>

                      <span className="category-badge">
                        {issue.category}
                      </span>

                      {issue.pr_status && (
                        <span className="status-badge">
                          {issue.pr_status}
                        </span>
                      )}
                    </div>

                    {issue.line_start !== null && (
                      <span className="line-location">
                        Line {issue.line_start}
                        {issue.line_end !== null &&
                        issue.line_end !==
                          issue.line_start
                          ? `-${issue.line_end}`
                          : ""}
                      </span>
                    )}
                  </div>

                  <h4>{issue.title}</h4>

                  <p className="issue-description">
                    {issue.description}
                  </p>

                  <div className="suggestion">
                    <strong>Suggestion</strong>
                    <p>
                      {issue.suggestion}
                    </p>
                  </div>

                  <div className="issue-meta">
                    <span>
                      Confidence:{" "}
                      {Math.round(
                        issue.confidence * 100,
                      )}
                      %
                    </span>

                    {issue.source && (
                      <span>
                        Source: {issue.source}
                      </span>
                    )}

                    {issue.rule_id && (
                      <span>
                        Rule: {issue.rule_id}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export default GitHubPRReviewDetail;