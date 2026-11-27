import { Page } from '@playwright/test';

export async function login(page: Page, baseUrl: string, username: string, password: string): Promise<void> {
  const csrfResponse = await page.request.get(`${baseUrl}/api/auth/csrf/`);
  const csrfBody = (await csrfResponse.text().catch(() => '')).trim();

  if (!csrfResponse.ok()) {
    const details = csrfBody || '<empty response body>';
    throw new Error(`CSRF bootstrap failed: ${csrfResponse.status()} ${details}`);
  }

  let csrfToken = '';
  try {
    const parsed = JSON.parse(csrfBody) as { csrfToken?: string };
    csrfToken = parsed.csrfToken || '';
  } catch {
    csrfToken = '';
  }

  if (!csrfToken) {
    throw new Error(`CSRF bootstrap returned no token: ${csrfBody || '<empty response body>'}`);
  }

  const loginResponse = await page.request.post(`${baseUrl}/api/auth/login/`, {
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    },
    data: {
      email: username,
      password,
    },
  });

  const loginBody = (await loginResponse.text().catch(() => '')).trim();
  if (!loginResponse.ok()) {
    const details = loginBody || '<empty response body>';
    throw new Error(`Login API failed: ${loginResponse.status()} ${details}`);
  }

  const currentUserResponse = await page.request.get(`${baseUrl}/api/auth/user/`);
  const currentUserBody = (await currentUserResponse.text().catch(() => '')).trim();

  if (!currentUserResponse.ok()) {
    const details = currentUserBody || '<empty response body>';
    throw new Error(`Session verification failed: ${currentUserResponse.status()} ${details}`);
  }
}