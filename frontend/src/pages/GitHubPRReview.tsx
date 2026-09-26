import { useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  createPRReviewJob,
  getReviewJob,
} from "../services/api";

function GitHubPRReview() {
  const navigate = useNavigate();

  const [owner, setOwner] = useState("");
  const [repo, setRepo] = useState("");
  const [pullNumber, setPullNumber] = useState("");
  const [headSha, setHeadSha] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function pollJob(jobId: string) {
    const maxAttempts = 120;

    for (
      let attempt = 0;
      attempt < maxAttempts;
      attempt++
    ) {
      const job = await getReviewJob(jobId);

      console.log("PR REVIEW JOB:", job);

      if (
        job.status === "COMPLETED" &&
        job.review_id
      ) {
        navigate(
          `/github-pr/reviews/${job.review_id}`,
        );
        return;
      }

      if (job.status === "FAILED") {
        throw new Error(
          job.error_message ??
            "GitHub PR review failed.",
        );
      }

      await new Promise((resolve) =>
        setTimeout(resolve, 1000),
      );
    }

    throw new Error(
      "GitHub PR review timed out.",
    );
  }

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (!owner.trim()) {
      setError("Please enter the repository owner.");
      return;
    }

    if (!repo.trim()) {
      setError("Please enter the repository name.");
      return;
    }

    if (!pullNumber.trim()) {
      setError("Please enter the pull request number.");
      return;
    }

    if (!headSha.trim()) {
      setError("Please enter the PR head SHA.");
      return;
    }

    const parsedPullNumber = Number(pullNumber);

    if (
      !Number.isInteger(parsedPullNumber) ||
      parsedPullNumber < 1
    ) {
      setError(
        "Pull request number must be a positive integer.",
      );
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const job = await createPRReviewJob(
        owner.trim(),
        repo.trim(),
        parsedPullNumber,
        headSha.trim(),
      );

      await pollJob(job.job_id);
    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : "Failed to start GitHub PR review.",
      );

      setSubmitting(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">
            GitHub Integration
          </p>

          <h1>Review a Pull Request</h1>

          <p className="page-subtitle">
            Analyze a GitHub pull request using
            static analysis, AST analysis, and AI.
          </p>
        </div>
      </div>

      <div className="card review-form-card">
        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="owner">
                Repository Owner
              </label>

              <input
                id="owner"
                type="text"
                value={owner}
                onChange={(event) =>
                  setOwner(event.target.value)
                }
                placeholder="e.g. octocat"
                disabled={submitting}
              />
            </div>

            <div className="form-group">
              <label htmlFor="repo">
                Repository
              </label>

              <input
                id="repo"
                type="text"
                value={repo}
                onChange={(event) =>
                  setRepo(event.target.value)
                }
                placeholder="e.g. Hello-World"
                disabled={submitting}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="pullNumber">
                Pull Request Number
              </label>

              <input
                id="pullNumber"
                type="number"
                min="1"
                value={pullNumber}
                onChange={(event) =>
                  setPullNumber(event.target.value)
                }
                placeholder="e.g. 42"
                disabled={submitting}
              />
            </div>

            <div className="form-group">
              <label htmlFor="headSha">
                Head SHA
              </label>

              <input
                id="headSha"
                type="text"
                value={headSha}
                onChange={(event) =>
                  setHeadSha(event.target.value)
                }
                placeholder="e.g. abc123..."
                disabled={submitting}
              />
            </div>
          </div>

          <div className="form-help">
            <strong>Tip:</strong> You can find the head
            SHA in the GitHub pull request's commit
            information.
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
              ? "Reviewing Pull Request..."
              : "Review Pull Request"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default GitHubPRReview;