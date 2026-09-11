import Link from 'next/link';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { dataPath } from '@/config/client';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';
import type { ApiDocumentationConfig } from './config';
import { SwaggerEmbed } from './SwaggerEmbed';

export function ApiDocumentationPage({ config }: { config: ApiDocumentationConfig }) {
  const schemaUrl = `/openapi/${config.schemaFile}`;
  const breadcrumbs = hostBreadcrumbs(
    'data',
    { label: 'API services', href: dataPath('/api/') },
  );

  if (config.overview) {
    breadcrumbs.push({
      label: config.overview.title,
      href: dataPath(config.overview.href),
    });
  }

  breadcrumbs.push({ label: config.title, current: true });

  return (
    <ProtectedRoute>
      <div className="govuk-width-container">
        <Breadcrumbs items={breadcrumbs} />
        <div className="govuk-main-wrapper">
          <h1 className="govuk-heading-xl">{config.title}</h1>
          <p className="govuk-body">
            You can use the interactive documentation to customise your API response using the
            available query parameters. If you are registered and logged in, you will be given a full response. Otherwise you will be given an example response.
          </p>
          <p className="govuk-body">
            You can also{' '}
            <a className="govuk-link" href={schemaUrl} download>
              download the {config.schemaLabel} OpenAPI specification
            </a>
            .
          </p>
          <h2 className="govuk-heading-m">Ready to use the API?</h2>
          <p className="govuk-body">
            <Link className="govuk-link" href={dataPath('/guidance/requirements?section=api')}>
              View developer documentation
            </Link>
          </p>
          <h2 className="govuk-heading-m">First time API user?</h2>
          <p className="govuk-body">
            <Link className="govuk-link" href={dataPath('/guide-me')}>
              Guide me
            </Link>
          </p>
          <SwaggerEmbed schemaFile={config.schemaFile} />
        </div>
      </div>
    </ProtectedRoute>
  );
}