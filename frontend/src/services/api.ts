import axios from "axios";
import type { 
  ReviewResponse,
  ReviewHistoryResponse,
  ReviewJobResponse,
} from "../types/review";

const api = axios.create({
  baseURL: "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

export async function getReview(
  reviewId: string,
): Promise<ReviewResponse> {
  const response = await api.get<ReviewResponse>(
    `/reviews/${reviewId}`,
  );

  return response.data;
}

export async function getReviews(): Promise<ReviewHistoryResponse> {
  const response = await api.get<ReviewHistoryResponse>(
    "/reviews/",
  );

  return response.data;
}

export async function createReviewJob(
  code: string,
  language: string,
): Promise<ReviewJobResponse> {
  const response = await api.post<ReviewJobResponse>(
    "/reviews/jobs",
    {
      code,
      language,
    },
  );

  return response.data;
}
export async function getReviewJob(
  jobId: string,
): Promise<ReviewJobResponse> {
  const response = await api.get<ReviewJobResponse>(
    `/reviews/jobs/${jobId}`,
  );

  return response.data;
}

export default api;