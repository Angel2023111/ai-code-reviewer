import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { getReview } from "../services/api";
import type { ReviewResponse } from "../types/review";

function ReviewDetail() {
  const { reviewId } = useParams<{ reviewId: string }>();
  const navigate = useNavigate();

  const [review, setReview] = useState<ReviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadReview() {
      if (!reviewId) {
        setError("Review ID is missing");
        setLoading(false);
        return;
      }

      try {
        const data = await getReview(reviewId);
        setReview(data);
      } catch (err) {
        console.error(err);
        setError("Failed to load review");
      } finally {
        setLoading(false);
      }
    }

    loadReview();
  }, [reviewId]);

  if (loading) {
    return (
      <div className="detail-page">
        <p>Loading review...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="detail-page">
        <button
          className="back-button"
          onClick={() => navigate("/")}
        >
          ← Back to Dashboard
        </button>

        <p>{error}</p>
      </div>
    );
  }

  if (!review) {
    return (
      <div className="detail-page">
        <p>Review not found.</p>
      </div>
    );
  }

  return (
    <div className="detail-page">
      <div className="detail-header">
        <div>
          <button
            className="back-button"
            onClick={() => navigate("/")}
          >
            ← Back to Dashboard
          </button>

          <h1>Code Review</h1>

          <p>
            Review ID:{" "}
            <code>{review.id}</code>
          </p>

          <p>
            Created:{" "}
            {new Date(
              review.created_at,
            ).toLocaleString()}
          </p>
        </div>
      </div>

      {/* Summary */}
      <section className="detail-summary">
        <div className="detail-stat critical">
          <span>Critical</span>
          <strong>{review.critical}</strong>
        </div>

        <div className="detail-stat high">
          <span>High</span>
          <strong>{review.high}</strong>
        </div>

        <div className="detail-stat medium">
          <span>Medium</span>
          <strong>{review.medium}</strong>
        </div>

        <div className="detail-stat low">
          <span>Low</span>
          <strong>{review.low}</strong>
        </div>
      </section>

      {/* Findings */}
      <section className="detail-findings">
        <div className="section-header">
          <div>
            <h2>Findings</h2>

            <p>
              {review.issues.length} issue
              {review.issues.length !== 1
                ? "s"
                : ""}{" "}
              detected
            </p>
          </div>
        </div>

        {review.issues.length === 0 ? (
          <div className="empty-state">
            <h3>No issues detected</h3>
            <p>
              The code review did not identify any
              problems.
            </p>
          </div>
        ) : (
          <div className="finding-list">
            {review.issues.map((issue, index) => (
              <article
                className="finding-card"
                key={`${issue.rule_id ?? "issue"}-${index}`}
              >
                <div className="finding-header">
                  <div>
                    <span
                      className={`severity ${issue.severity.toLowerCase()}`}
                    >
                      {issue.severity}
                    </span>

                    <span className="category-badge">
                      {issue.category}
                    </span>
                  </div>

                  {issue.pr_status && (
                    <span className="pr-status">
                      {issue.pr_status}
                    </span>
                  )}
                </div>

                <h3>{issue.title}</h3>

                {issue.file && (
                  <div className="finding-location">
                    <span>📄</span>

                    <code>
                      {issue.file}

                      {issue.line_start !== null &&
                        `:${issue.line_start}`}

                      {issue.line_end !== null &&
                        issue.line_end !==
                          issue.line_start &&
                        `-${issue.line_end}`}
                    </code>
                  </div>
                )}

                <div className="finding-section">
                  <h4>Description</h4>
                  <p>{issue.description}</p>
                </div>

                <div className="finding-section">
                  <h4>Suggestion</h4>
                  <p>{issue.suggestion}</p>
                </div>

                <div className="finding-meta">
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
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default ReviewDetail;
