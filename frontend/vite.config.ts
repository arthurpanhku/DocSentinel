import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  base: "/console/",
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
      "/health": "http://localhost:8000",
      "/config": "http://localhost:8000"
    }
  }
});
