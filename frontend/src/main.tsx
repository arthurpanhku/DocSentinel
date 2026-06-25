import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import App from "./App";
import { AppProviders } from "./app/providers";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AppProviders>
      <BrowserRouter basename="/console">
        <App />
      </BrowserRouter>
    </AppProviders>
  </React.StrictMode>
);
