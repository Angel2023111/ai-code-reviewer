import { useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  createReviewJob,
  getReviewJob,
} from "../services/api";

function NewReview() {
  const navigate = useNavigate();

  const [code, setCode] = useState("");
  const [language, setLanguage] = useState("python");

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function pollJob(jobId: string) {
    const maxAttempts = 60;

    for (
      let attempt = 0;
      attempt < maxAttempts;
      attempt++
    ) {
      const job = await getReviewJob(jobId);

      console.log("REVIEW JOB:", job);

      if (
        job.status === "COMPLETED" &&
        job.review_id
      ) {
        navigate(`/reviews/${job.review_id}`);
        return;
      }

      if (job.status === "FAILED") {
        throw new Error(
          job.error_message ??
            "Review job failed",
        );
      }

      await new Promise((resolve) =>
        setTimeout(resolve, 1000),
      );
    }

    throw new Error(
      "Review job timed out",
    );
  }

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (!code.trim()) {
      setError(
        "Please enter some code to review.",
      );
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const job = await createReviewJob(
        code,
        language,
      );

      await pollJob(job.job_id);
    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : "Failed to create review. Please try again.",
      );

      setSubmitting(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">
            Code Analysis
          </p>

          <h1>New Review</h1>

          <p className="page-subtitle">
            Submit source code for AI-powered
            code review.
          </p>
        </div>
      </div>

      <div className="card review-form-card">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="language">
              Language
            </label>

            <select
              id="language"
              value={language}
              onChange={(event) =>
                setLanguage(event.target.value)
              }
              disabled={submitting}
            >
              <option value="python">
                Python
              </option>
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
              placeholder="Paste your code here..."
              rows={20}
              disabled={submitting}
            />
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="primary-button"
            disabled={submitting}
          >
            {submitting
              ? "Reviewing..."
              : "Review Code"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default NewReview;