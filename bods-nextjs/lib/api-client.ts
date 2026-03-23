import { config } from '@/config';

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
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      headers.set('X-CSRFToken', csrfToken);
    }
  }

  const response = await fetch(`${config.djangoApiUrl}${path}`, {
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
    throw new Error(getErrorMessage(payload, `Request failed with status ${response.status}`));
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