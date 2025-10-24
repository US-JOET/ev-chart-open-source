import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "/",
  plugins: [react()],
  build: {
    outDir: "build",
    assetsDir: "static",
    rollupOptions: {
      output: {
        entryFileNames: "static/js/[name]-[hash].js",
        chunkFileNames: "static/js/[name]-[hash].js",
        assetFileNames: ({ name }) => {
          if (/\.css$/.test(name ?? "")) {
            return "static/css/[name]-[hash][extname]";
          }
          return "static/media/[name]-[hash][extname]";
        },
      },
    },
  },
});
