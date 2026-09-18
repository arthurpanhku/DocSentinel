export default {
  plugins: {
    // Tailwind v4 ships its PostCSS plugin separately and handles vendor
    // prefixing itself, so autoprefixer is no longer part of the pipeline.
    "@tailwindcss/postcss": {}
  }
};
