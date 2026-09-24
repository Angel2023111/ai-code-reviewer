import { useState } from "react";
import { useNavigate } from "react-router-dom";

import api from "../services/api";

function NewReview() {
  const navigate = useNavigate();

  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();

    if (!code.trim()) {
      setError("Please enter some code to review.");
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const response = await api.post("/reviews/", {
        code,
        language,
      });

      const reviewId = response.data.review_id;

      navigate(`/reviews/${reviewId}`);
    } catch (err) {
      console.error(err);
      setError("Failed to create review. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="new-review-page">
      <div className="new-review-header">
        <button
          className="back-button"
          onClick={() => navigate("/")}
        >
          ← Back to Dashboard
        </button>

        <h1>New Code Review</h1>

        <p>
          Submit your code and let the review engine analyze it
          for bugs, security issues, design problems, and code
          quality issues.
        </p>
      </div>

      <form
        className="review-form"
        onSubmit={handleSubmit}
      >
        <div className="form-group">
          <label htmlFor="language">
            Programming Language
          </label>

          <select
            id="language"
            value={language}
            onChange={(event) =>
              setLanguage(event.target.value)
            }
          >
            <option value="python">Python</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="code">
            Source Code
          </label>

          <textarea
            id="code"
            value={code}
            onChange={(event) =>
              setCode(event.target.value)
            }
            placeholder={`Paste your code here...

Example:

def divide(a, b):
    return a / b`}
            rows={24}
            spellCheck={false}
          />
        </div>

        {error && (
          <div className="form-error">
            {error}
          </div>
        )}

        <div className="form-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={() => navigate("/")}
            disabled={submitting}
          >
            Cancel
          </button>

          <button
            type="submit"
            className="primary-button"
            disabled={submitting}
          >
            {submitting
              ? "Analyzing Code..."
              : "Review Code"}
          </button>
        </div>
      </form>
    </div>
  );
}

export default NewReview;