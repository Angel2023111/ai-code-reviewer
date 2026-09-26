import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import Dashboard from "./pages/Dashboard";
import ReviewDetail from "./pages/ReviewDetail";
import NewReview from "./pages/NewReview";

import GitHubPRReview from "./pages/GitHubPRReview";
import GitHubPRReviewDetail from "./pages/GitHubPRReviewDetail";

import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={<Dashboard />}
        />

        <Route
          path="/reviews/new"
          element={<NewReview />}
        />

        <Route
          path="/reviews/:reviewId"
          element={<ReviewDetail />}
        />
        <Route
          path="/github-pr"
          element={<GitHubPRReview />}
        />

        <Route
          path="/github-pr/reviews/:reviewId"
          element={<GitHubPRReviewDetail />}
        />
        <Route
          path="*"
          element={<Navigate to="/" replace />}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;