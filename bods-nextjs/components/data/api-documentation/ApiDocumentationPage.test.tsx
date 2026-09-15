import { render, screen } from '@testing-library/react';
import { ApiDocumentationPage } from './ApiDocumentationPage';
import { API_DOCUMENTATION } from './config';

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => children,
}));

jest.mock('./SwaggerEmbed', () => ({
  SwaggerEmbed: ({ schemaFile }: { schemaFile: string }) => (
    <div data-testid="swagger-ui" data-schema={schemaFile} />
  ),
}));

describe('ApiDocumentationPage', () => {
  it.each(Object.values(API_DOCUMENTATION))(
    'renders the $title documentation from $schemaFile',
    (config) => {
      render(<ApiDocumentationPage config={config} />);

      expect(screen.getByRole('heading', { level: 1, name: config.title })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: new RegExp(config.schemaLabel) })).toHaveAttribute(
        'href',
        `/openapi/${config.schemaFile}`,
      );
      expect(screen.getByTestId('swagger-ui')).toHaveAttribute('data-schema', config.schemaFile);

      if ('overview' in config) {
        expect(screen.getByRole('link', { name: config.overview.title })).toHaveAttribute(
          'href',
          expect.stringContaining(config.overview.href),
        );
      }
    },
  );

});