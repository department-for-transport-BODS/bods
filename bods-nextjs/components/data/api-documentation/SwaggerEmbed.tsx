'use client';

import dynamic from 'next/dynamic';
import type { ComponentType } from 'react';
import { ensureCsrfToken } from '@/lib/api-client';

interface SwaggerRequest {
  method?: string;
  headers: Record<string, string>;
}

interface SwaggerComponentProps {
  url: string;
  deepLinking?: boolean;
  validatorUrl?: string | null;
  syntaxHighlight?: boolean;
  withCredentials?: boolean;
  requestInterceptor?: (
    request: SwaggerRequest,
  ) => SwaggerRequest | Promise<SwaggerRequest>;
}

const SwaggerUI = dynamic(
  () =>
    import('swagger-ui-react').then(
      (module) => module.default as unknown as ComponentType<SwaggerComponentProps>,
    ),
  { ssr: false },
);

const MUTATION_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

export function SwaggerEmbed({ schemaFile }: { schemaFile: string }) {
  return (
    <div id="swagger-ui">
      <SwaggerUI
        url={`/openapi/${schemaFile}`}
        deepLinking
        validatorUrl={null}
        syntaxHighlight={false}
        withCredentials
        requestInterceptor={async (request) => {
          if (MUTATION_METHODS.has(String(request.method).toUpperCase())) {
            const csrfToken = await ensureCsrfToken();
            if (csrfToken) {
              request.headers['X-CSRFToken'] = csrfToken;
            }
          }

          return request;
        }}
      />
    </div>
  );
}