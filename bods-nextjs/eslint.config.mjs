import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    settings: {
      react: {
        version: '19',
      },
    },
    rules: {
      'react/no-unescaped-entities': [
        'error',
        {
          forbid: ['>', '}'],
        },
      ],
    },
  },
  {
    files: [
      "app/**/*.{js,jsx,ts,tsx}",
      "components/**/*.{js,jsx,ts,tsx}",
      "hooks/**/*.{js,jsx,ts,tsx}",
      "lib/**/*.{js,jsx,ts,tsx}",
      "middleware.ts",
      "config.ts",
    ],
    rules: {
      "max-lines": [
        "error",
        {
          max: 300,
          skipBlankLines: true,
          skipComments: true,
        },
      ],
    },
  },
  globalIgnores([
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
