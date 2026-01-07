# E2E Testing Framework - Playwright (Node.js/TypeScript)

## Quick Start

```bash
# Install dependencies
npm install
npx playwright install chromium

# Configure
cp .env.example .env
# Edit .env with appropratie details

# Run tests
npm test                    # Headless
npm run test:headed         # See browser

# Development Usage
npm run test:ui             # Interactive mode
npm run test:debug          # Step through
```

## Structure

```
pages/
  ├── BasePage.ts              # Framework class
  ├── HomePage.ts              # App-specific pages
  ├── OrganisationProfilePage.ts
  └── ... Further Page Classes
tests/
  ├── authenticated.spec.ts    # Authenticated tests
  └── fixtures.ts              # Reusable test setup
helpers/
  └── auth.ts                  # Authentication logic
config.ts                      # Environment Import
.env                           # Environment Config
```

The BasePage is extended into every page.

## Development
### Writing Tests

```typescript
import { test, expect } from './fixtures';

test('my test', async ({ authenticatedPage }) => {
  // Already logged in
  await authenticatedPage.click('text=My Link'); 
  await expect(authenticatedPage.locator('h1')).toContainText('Expected');

});
```

### Key Patterns

**Page Objects** - Extend `BasePage`, override `navigate()`, `verifyOnPage()`, `hasLoaded()`

**Fixtures** - Use `authenticatedPage` for logged-in tests

**Config** - All URLs, credentials, selectors in `.env`

## Common Commands

```bash
npm test                        # Run all tests
npm test tests/basic.spec.ts    # Run specific file
npm run test:chrome             # Specific browser
npm run show-report             # View results
npm run codegen                 # Generate test code
```

## CI/CD


## Docs

- [Playwright Docs](https://playwright.dev/docs/intro)
- [Best Practices](https://playwright.dev/docs/best-practices)
