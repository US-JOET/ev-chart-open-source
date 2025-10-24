import globals from "globals";
import pluginJs from "@eslint/js";
import tseslint from "typescript-eslint";
import pluginReact from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import prettier from "eslint-plugin-prettier";
import eslintimport from "eslint-plugin-import";

const { configs: reactConfigs } = pluginReact;
const { configs: prettierConfigs } = prettier;
const { configs: importConfigs } = eslintimport;

export default [
  { files: ["**/*.{js,mjs,cjs,ts,jsx,tsx}"] },
  { files: ["**/*.js"], languageOptions: { sourceType: "script" } },
  { languageOptions: { globals: globals.browser } },
  pluginJs.configs.recommended,
  ...tseslint.configs.recommended,
  pluginReact.configs.flat.recommended,
  {
    plugins: {
      react: pluginReact,
      "react-hooks": reactHooks,
      prettier: prettier,
      import: eslintimport,
    },
    rules: {
      // react recommended rules
      ...reactConfigs.recommended.rules,
      // import recommended import/export rules
      ...importConfigs.errors.rules,
      ...importConfigs.warnings.rules,

      // import the prettier recommended rules
      ...prettierConfigs.recommended.rules,

      //Custom Rules
      "react/react-in-jsx-scope": "off", // React 17 doesn't require React in scope
      "prettier/prettier": "error", //ensure prettier formatting
      // "react/prop-types": "off" //Disable PropTypes if not in use
      "import/no-unresolved": "off",
    },
    settings: {
      react: {
        version: "detect",
      },
    },
  },
];
