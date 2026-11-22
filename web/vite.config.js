import { fileURLToPath } from "node:url";
import { defineConfig, searchForWorkspaceRoot } from "vite";

export default defineConfig({
  server: {
    host: "127.0.0.1",
    fs: {
      allow: [
        searchForWorkspaceRoot(import.meta.dirname),
        fileURLToPath(new URL("../src/templates/vin_scully.webp", import.meta.url)),
      ],
    },
    proxy: {
      "/langgraph/": {
        target: "http://127.0.0.1:2024",
        changeOrigin: true,
        rewrite: (path) => path.slice("/langgraph".length),
      },
    },
  },
});
