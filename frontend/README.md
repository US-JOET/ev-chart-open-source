# Electric Vehicle Charging Analytics and Reporting Tool (EV-ChART) Frontend

This is a React + Typescript project using Vite. For additional information about setting up with Vite, see [React + TypeScript + Vite](#react--typescript--vite).

## IMPORTANT ##

Environment settings will need to be updated in order to deploy the application.  The file `.env.TEMPLATE` serves as the template for specific environment settings which are required.  Replace the values surrounded by angle braces (`<`, `>`) with values determined by the legend below.

`<APP URL>` - The full HTTPS URL to the application environment.
`<API URL>` - The full HTTPS URL to the application API.  This will likely be the same as `<APP URL>`.
`<APP HOSTNAME>` - Format is `evchart-<ENVIRONMENT>`, replacing `<ENVIRONMENT>` with the relevant environment designation.
`<COGNITO USERPOOL ID>` - The Cognito User Pool ID.
`<COGNITO USERPOOL APP CLIENT ID>` - The Cognito User Pool Client ID.
`<AWS REGION>` - The AWS region where the application is being deployed.

## Available Scripts

In the project directory, you can run:

### `npm run dev`

Runs the app in the development mode.\
Open [http://localhost:5173](http://localhost:5173) to view it in the browser.

Dev server that serves your source files over [native ES modules](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules), with rich [built-in features](https://vite.dev/guide/features.html) and fast [Hot Module Replacement (HMR)](https://vite.dev/guide/features.html#hot-module-replacement).

The page will reload if you make edits.\

### `npm test`

Launches the tests.\
See the section about [tests](https://vitest.dev/guide/) for more information.

#### `npm test path/to/file`

Launches the tests for the specified file.

### `npm eslint src`

Launches the static code analysis tool per the rules in the [config file](./eslint.config.mjs).\
Reed more about [eslint](https://eslint.org/) here.

### `npm run coverage`

Launches the code coverage tool.\
See the section about [coverage](https://vitest.dev/guide/coverage.html) for more information.

### `npm run build`

Builds the app for production to the `build` folder.

Custom build config can be viewed in the [rollupOptions](./vite.config.ts) section of the vite config.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [build](https://vite.dev/guide/build) for more information.

## Learn More

To learn React, check out the [React documentation](https://reactjs.org/).

## For local development:

All API calls require a valid/ current jwt token to properly execute. In the local environment, you can accomplish this by supplying a username and password in the .env.local file.

&nbsp;

# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react/README.md) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type aware lint rules:

- Configure the top-level `parserOptions` property like this:

```js
export default tseslint.config({
  languageOptions: {
    // other options...
    parserOptions: {
      project: ["./tsconfig.node.json", "./tsconfig.app.json"],
      tsconfigRootDir: import.meta.dirname,
    },
  },
});
```

- Replace `tseslint.configs.recommended` to `tseslint.configs.recommendedTypeChecked` or `tseslint.configs.strictTypeChecked`
- Optionally add `...tseslint.configs.stylisticTypeChecked`
- Install [eslint-plugin-react](https://github.com/jsx-eslint/eslint-plugin-react) and update the config:

```js
// eslint.config.js
import react from "eslint-plugin-react";

export default tseslint.config({
  // Set the react version
  settings: { react: { version: "18.3" } },
  plugins: {
    // Add the react plugin
    react,
  },
  rules: {
    // other rules...
    // Enable its recommended rules
    ...react.configs.recommended.rules,
    ...react.configs["jsx-runtime"].rules,
  },
});
```

## Learn More

Check out the [Vite documentation](https://vite.dev/guide/).
