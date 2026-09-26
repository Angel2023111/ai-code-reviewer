
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { getReview, getReviews } from "../services/api";
import type { 
  ReviewResponse,
  ReviewHistoryItem,
 } from "../types/review";

function Dashboard() {

  const navigate = useNavigate();
  const [review, setReview] = useState<ReviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reviews, setReviews] = useState<
    ReviewHistoryItem[]
  >([]);

  // Replace this with the review_id you got from Swagger
  const reviewId = "8771f965-ff05-4594-8d78-a1303d99eb1b";

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [reviewData, historyData] = await Promise.all([
          getReview(reviewId),
          getReviews(),
        ]);

        console.log("REVIEW FROM BACKEND:", reviewData);
        console.log("REVIEW HISTORY FROM BACKEND:", historyData);

        setReview(reviewData);
        setReviews(historyData.reviews);
      } catch (err) {
        console.error(err);
        setError("Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
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

          <div className="dashboard-actions">
            <button
              className="secondary-button"
              onClick={() =>
                navigate("/reviews/new")
              }
            >
              New Code Review
            </button>

            <button
              className="primary-button"
              onClick={() =>
                navigate("/github-pr")
              }
            >
              Review GitHub PR
            </button>
          </div>
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
        {/* Recent Reviews */}
        <section className="reviews-section">
          <div className="section-header">
            <div>
              <h2>Recent Reviews</h2>
              <p>
                Latest code reviews processed by the system
              </p>
            </div>
          </div>

          {loading && <p>Loading reviews...</p>}

          {!loading && !error && reviews.length === 0 && (
            <p>No reviews found.</p>
          )}

          {!loading && !error && reviews.length > 0 && (
            <div className="review-list">
              {reviews.map((item) => (
                <div
                  className="review-row"
                  key={item.id}
                  onClick={() => navigate(`/reviews/${item.id}`)}
                  style={{ cursor: "pointer" }}
                >
                  <div>
                    <strong>
                      Review {item.id.slice(0, 8)}
                    </strong>

                    <p>
                      {item.issue_count} issue
                      {item.issue_count !== 1 ? "s" : ""} detected
                    </p>

                    <small>
                      {new Date(
                        item.created_at,
                      ).toLocaleString()}
                    </small>
                  </div>

                  <div>
                    <span className="severity critical">
                      {item.critical} Critical
                    </span>

                    <span className="severity high">
                      {item.high} High
                    </span>

                    <span className="severity medium">
                      {item.medium} Medium
                    </span>
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
