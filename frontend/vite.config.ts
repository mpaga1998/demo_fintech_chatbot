import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: "127.0.0.1",     // keep IPv4 (important for your setup)
    port: 5173,
    allowedHosts: true,    // ✅ allow *.trycloudflare.com
  },
});
