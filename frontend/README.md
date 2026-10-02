# React + TypeScript + Vite

## Playwright tests (assessment Tier 2B)

The `backend-e2e` project calls the real backend, PostgreSQL and Redis. It covers:

1. Register, logout/login, create a todo, mark it completed and active, verify
   persisted state after reload, and logout.
2. User A creates a private todo. User B registers/logs in in an independent
   browser context and cannot see A's title or description. Both users retain
   access to their own todos after reload.

Start the backend services from the repository root:

```bash
docker compose up -d --build backend
```

Then install the test dependencies and run from `frontend/`:

```bash
npm ci
npx playwright install chromium
npm run test:e2e
```

Run only the two required real-backend scenarios, headless or headed:

```bash
npm run test:e2e:real
npm run test:e2e:real -- --headed
```

On Windows, an installed Microsoft Edge can be used without downloading Chromium:

```powershell
$env:PLAYWRIGHT_CHANNEL = "msedge"
npm run test:e2e
```

Playwright starts the frontend on port 5179. For a visible browser, run
`npm run test:e2e -- --headed`.

The API defaults to `http://localhost:8000`. Set `VITE_API_URL` before running
tests if your backend uses a different address. Stop any existing frontend on
port 5179 before changing this value so Playwright starts it with the same API
address as the tests.

Each real-backend test registers unique accounts and cleans up its created todos
after completion, including failures. Test accounts remain because the app has
no account deletion endpoint; run against a development/test database.

The separate `session-cache` project mocks account-specific API responses to
check frontend cache isolation, failed logout and late responses. Run it without
backend services using `npm run test:e2e:mock`. `npm run test:e2e` (or
`npx playwright test`) runs both projects, eight tests in total.

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
