interface ApiRequestOptions extends Omit<RequestInit, 'body' | 'method'> {
  body?: BodyInit | Record<string, unknown> | null;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export function getCsrfToken(): string {
  if (typeof document === 'undefined') return '';
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : '';
}

/**
 * Django's CSRF cookie is only set once a page has called an API, so requests
 * made before that (for example confirming an email straight from a link) have
 * to ask for a token first.
 */
export async function ensureCsrfToken(): Promise<string> {
  const existingToken = getCsrfToken();
  if (existingToken) {
    return existingToken;
  }

  const response = await fetch('/api/auth/csrf/', {
    method: 'GET',
    credentials: 'include',
    cache: 'no-store',
  });
  const payload = (await response.json().catch(() => null)) as { csrfToken?: string } | null;

  return payload?.csrfToken || '';
}

/**
 * Thrown for any non-2xx response. Carries the field errors Django's forms
 * return so pages can drive a GOV.UK error summary without their own fetch.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly fieldErrors: Record<string, string[]>;

  constructor(message: string, status: number, fieldErrors: Record<string, string[]>) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.fieldErrors = fieldErrors;
  }

  get hasFieldErrors(): boolean {
    return Object.keys(this.fieldErrors).length > 0;
  }

  /** The first message per field, which is all the form templates render. */
  firstFieldErrors(): Record<string, string> {
    return Object.fromEntries(
      Object.entries(this.fieldErrors)
        .map(([field, messages]) => [field, messages[0]])
        .filter(([, message]) => Boolean(message)),
    );
  }
}

function extractFieldErrors(payload: unknown): Record<string, string[]> {
  if (!payload || typeof payload !== 'object' || !('field_errors' in payload)) {
    return {};
  }

  const raw = (payload as { field_errors?: unknown }).field_errors;
  if (!raw || typeof raw !== 'object') {
    return {};
  }

  const fieldErrors: Record<string, string[]> = {};
  for (const [field, messages] of Object.entries(raw)) {
    if (Array.isArray(messages)) {
      const strings = messages.filter((message): message is string => typeof message === 'string');
      if (strings.length > 0) {
        fieldErrors[field] = strings;
      }
    } else if (typeof messages === 'string') {
      fieldErrors[field] = [messages];
    }
  }

  return fieldErrors;
}

function isFormData(body: ApiRequestOptions['body']): body is FormData {
  return typeof FormData !== 'undefined' && body instanceof FormData;
}

function isBodyInit(body: ApiRequestOptions['body']): body is BodyInit {
  return (
    typeof body === 'string' ||
    body instanceof URLSearchParams ||
    body instanceof Blob ||
    body instanceof ArrayBuffer ||
    ArrayBuffer.isView(body) ||
    (typeof ReadableStream !== 'undefined' && body instanceof ReadableStream) ||
    isFormData(body)
  );
}

function getErrorMessage(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== 'object') {
    return fallback;
  }

  if ('detail' in payload && typeof payload.detail === 'string') {
    return payload.detail;
  }

  if ('message' in payload && typeof payload.message === 'string') {
    return payload.message;
  }

  if ('error' in payload && typeof payload.error === 'string') {
    return payload.error;
  }

  if (
    'non_field_errors' in payload &&
    Array.isArray(payload.non_field_errors) &&
    typeof payload.non_field_errors[0] === 'string'
  ) {
    return payload.non_field_errors[0];
  }

  return fallback;
}

function buildRequestBody(body: ApiRequestOptions['body'], headers: Headers): BodyInit | undefined {
  if (body == null) {
    return undefined;
  }

  if (isFormData(body) || isBodyInit(body)) {
    return body;
  }

  headers.set('Content-Type', 'application/json');
  return JSON.stringify(body);
}

async function request<T>(method: string, path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { body, headers: initHeaders, ...init } = options;
  const headers = new Headers(initHeaders ?? undefined);

  if (!headers.has('Accept')) {
    headers.set('Accept', 'application/json');
  }

  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method) && !headers.has('X-CSRFToken')) {
    const csrfToken = await ensureCsrfToken();
    if (csrfToken) {
      headers.set('X-CSRFToken', csrfToken);
    }
  }

  const response = await fetch(path, {
    ...init,
    method,
    headers,
    credentials: 'include',
    body: buildRequestBody(body, headers),
  });

  const contentType = response.headers.get('content-type') || '';
  const isJson = contentType.includes('application/json');
  const payload = isJson
    ? ((await response.json().catch(() => null)) as T | null)
    : ((await response.text().catch(() => '')) as T | string);

  if (!response.ok) {
    throw new ApiError(
      getErrorMessage(payload, `Request failed with status ${response.status}`),
      response.status,
      extractFieldErrors(payload),
    );
  }

  return payload as T;
}

export const api = {
  get<T>(path: string, options?: Omit<ApiRequestOptions, 'body'>): Promise<T> {
    return request<T>('GET', path, options);
  },

  post<T>(path: string, body?: ApiRequestOptions['body'], options?: Omit<ApiRequestOptions, 'body'>): Promise<T> {
    return request<T>('POST', path, { ...options, body });
  },
};

export function getPaginated<T>(path: string, options?: Omit<ApiRequestOptions, 'body'>): Promise<PaginatedResponse<T>> {
  return api.get<PaginatedResponse<T>>(path, options);
}