import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000,
    proxy: {
      // Career Skill Demand API (explore page) — must be before `/api` so it is not swallowed
      "/career-api": {
        target: "https://career-backend-702721595408.us-central1.run.app",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/career-api/, ""),
      },
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
