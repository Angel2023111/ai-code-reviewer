
import { useEffect, useState } from "react";


import { getReview } from "../services/api";
import type { ReviewResponse } from "../types/review";

function Dashboard() {
  const [review, setReview] = useState<ReviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Replace this with the review_id you got from Swagger
  const reviewId = "8771f965-ff05-4594-8d78-a1303d99eb1b";

  useEffect(() => {
    async function loadReview() {
      try {
        const data = await getReview(reviewId);

        console.log("REVIEW FROM BACKEND:", data);

        setReview(data);
      } catch (err) {
        console.error(err);
        setError("Failed to load review");
      } finally {
        setLoading(false);
      }
    }

    loadReview();
  }, []);

  return (
    <div className="dashboard">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="logo">
          <div className="logo-icon">AI</div>
          <span>Code Reviewer</span>
        </div>

        <nav className="nav">
          <div className="nav-item active">
            <span>▦</span>
            Dashboard
          </div>

          <div className="nav-item">
            <span>◫</span>
            Reviews
          </div>

          <div className="nav-item">
            <span>⑂</span>
            GitHub PRs
          </div>
        </nav>

        <div className="sidebar-footer">
          <div className="backend-status">
            <span className="status-dot"></span>
            Backend connected
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="main-content">
        {/* Top bar */}
        <header className="topbar">
          <div>
            <h1>Dashboard</h1>
            <p>Monitor your code reviews and findings.</p>
          </div>

          <button className="new-review-btn">
            + New Review
          </button>
        </header>

        {/* Stats */}
        <section className="stats-grid">
          {loading ? (
            <p>Loading...</p>
          ) : error ? (
            <p>{error}</p>
          ) : review ? (
            <>
              <div className="stat-card">
                <span className="stat-label">
                  Critical Issues
                </span>
                <strong>{review.critical}</strong>
              </div>

              <div className="stat-card">
                <span className="stat-label">
                  High Severity
                </span>
                <strong>{review.high}</strong>
              </div>

              <div className="stat-card">
                <span className="stat-label">
                  Total Issues
                </span>
                <strong>{review.issues.length}</strong>
              </div>

              <div className="stat-card">
                <span className="stat-label">
                  Review ID
                </span>
                <strong>
                  {review.id.slice(0, 8)}
                </strong>
              </div>
            </>
          ) : null}
        </section>

        {/* Review Findings */}
        <section className="reviews-section">
          <div className="section-header">
            <div>
              <h2>Review Findings</h2>
              <p>
                Issues detected by the code review system
              </p>
            </div>
          </div>

          {loading && <p>Loading review...</p>}

          {error && <p>{error}</p>}

          {!loading &&
            !error &&
            review &&
            review.issues.length === 0 && (
              <p>No issues were detected.</p>
            )}

          {!loading &&
            !error &&
            review &&
            review.issues.length > 0 && (
              <div className="review-list">
                {review.issues.map((issue, index) => (
                  <div
                    className="review-row"
                    key={index}
                  >
                    <div>
                      <strong>{issue.title}</strong>

                      <p>{issue.description}</p>

                      <small>
                        {issue.file ?? "Unknown file"}

                        {issue.line_start !== null &&
                          `:${issue.line_start}`}
                      </small>
                    </div>

                    <div>
                      <span
                        className={`severity ${issue.severity.toLowerCase()}`}
                      >
                        {issue.severity}
                      </span>

                      <span>{issue.category}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
        </section>
      </main>
    </div>
  );
}

export default Dashboard;
