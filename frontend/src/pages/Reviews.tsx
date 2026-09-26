import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { getReviews } from "../services/api";
import type { ReviewHistoryItem } from "../types/review";

function Reviews() {
  const navigate = useNavigate();

  const [reviews, setReviews] = useState<ReviewHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadReviews() {
      try {
        setLoading(true);
        const data = await getReviews();
        setReviews(data.reviews);
      } catch (err) {
        console.error(err);
        setError("Failed to load reviews.");
      } finally {
        setLoading(false);
      }
    }

    loadReviews();
  }, []);

  return (
    <div className="dashboard">
      <aside className="sidebar">
        <div className="logo">
          <div className="logo-icon">AI</div>
          <span>Code Reviewer</span>
        </div>

        <nav className="nav">
          <div
            className="nav-item"
            onClick={() => navigate("/")}
            style={{ cursor: "pointer" }}
          >
            <span>▦</span>
            Dashboard
          </div>

          <div className="nav-item active">
            <span>◫</span>
            Reviews
          </div>

          <div
            className="nav-item"
            onClick={() => navigate("/github-pr")}
            style={{ cursor: "pointer" }}
          >
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

      <main className="main-content">
        <header className="topbar">
          <div>
            <h1>Reviews</h1>
            <p>
              Browse all code reviews processed by the system.
            </p>
          </div>

          <button
            className="primary-button"
            onClick={() => navigate("/reviews/new")}
          >
            New Code Review
          </button>
        </header>

        <section className="reviews-section">
          {loading && <p>Loading reviews...</p>}

          {error && <p>{error}</p>}

          {!loading && !error && reviews.length === 0 && (
            <p>No reviews found.</p>
          )}

          {!loading && !error && reviews.length > 0 && (
            <div className="review-list">
              {reviews.map((review) => (
                <div
                  className="review-row"
                  key={review.id}
                  onClick={() =>
                    navigate(`/reviews/${review.id}`)
                  }
                  style={{ cursor: "pointer" }}
                >
                  <div>
                    <strong>
                      Review {review.id.slice(0, 8)}
                    </strong>

                    <p>
                      {review.issue_count} issue
                      {review.issue_count !== 1
                        ? "s"
                        : ""}{" "}
                      detected
                    </p>

                    <small>
                      {new Date(
                        review.created_at,
                      ).toLocaleString()}
                    </small>
                  </div>

                  <div>
                    <span className="severity critical">
                      {review.critical} Critical
                    </span>

                    <span className="severity high">
                      {review.high} High
                    </span>

                    <span className="severity medium">
                      {review.medium} Medium
                    </span>

                    <span className="severity low">
                      {review.low} Low
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

export default Reviews;