import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const prefixedHostPathMessage =
  "Use dataPath() or publishPath() from @/config/client. /data and /publish are App Router internals, not public URLs.";

const prefixedHostPathSelectors = [
  "JSXAttribute[name.name='href'] > Literal[value=/^\\/(publish|data)(\\/|$|\\?|#)/]",
  "JSXAttribute[name.name='href'] > TemplateLiteral > TemplateElement:first-child[value.raw=/^\\/(publish|data)(\\/|$|\\?|#)/]",
  "Property[key.name='href'] > Literal[value=/^\\/(publish|data)(\\/|$|\\?|#)/]",
  "Property[key.name='href'] > TemplateLiteral > TemplateElement:first-child[value.raw=/^\\/(publish|data)(\\/|$|\\?|#)/]",
];

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
      'no-restricted-syntax': [
        'error',
        ...prefixedHostPathSelectors.map((selector) => ({
          selector,
          message: prefixedHostPathMessage,
        })),
      ],
    },
  },
  {
    files: ["jest.config.js", "scripts/copy-gds-assets.js"],
    rules: {
      "@typescript-eslint/no-require-imports": "off",
      "@typescript-eslint/no-unused-expressions": "off",
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
    ]
  },
  globalIgnores([
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
