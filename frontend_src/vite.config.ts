import { defineConfig } from "vite";
import { readFileSync } from "fs";
import { resolve } from "path";

const manifest = JSON.parse(
  readFileSync(
    resolve(__dirname, "../custom_components/babybuddy/manifest.json"),
    "utf-8",
  ),
);

export default defineConfig({
  build: {
    lib: {
      entry: resolve(__dirname, "src/babybuddy-card.ts"),
      formats: ["es"],
      fileName: () => "babybuddy-card.js",
    },
    outDir: resolve(
      __dirname,
      "../custom_components/babybuddy/frontend",
    ),
    emptyOutDir: false,
    sourcemap: false,
    minify: "esbuild",
  },
  define: {
    CARD_VERSION: JSON.stringify(manifest.version),
  },
});
