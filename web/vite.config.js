import { defineConfig } from "vite";

export default defineConfig({
  server: {
    host: "127.0.0.1",
    proxy: {
      "/langgraph/": {
        target: "http://127.0.0.1:2024",
        changeOrigin: true,
        rewrite: (path) => path.slice("/langgraph".length),
      },
    },
  },
});
