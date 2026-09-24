import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import Dashboard from "./pages/Dashboard";
import ReviewDetail from "./pages/ReviewDetail";
import NewReview from "./pages/NewReview";

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
          path="*"
          element={<Navigate to="/" replace />}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;