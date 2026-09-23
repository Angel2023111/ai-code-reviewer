import axios from "axios";
import type { ReviewResponse } from "../types/review";

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

export default api;