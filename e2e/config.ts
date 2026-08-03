import * as dotenv from 'dotenv';
import * as path from 'path';

dotenv.config({ path: path.resolve(__dirname, '.env') });

export interface E2EConfig {
  baseUrl: string;
  organisationId: string;
  defaultTimeoutMs: number;
  navigationTimeoutMs: number;
  testUser: {
    username: string;
    password: string;
  };
  avlFeed: {
    url: string;
  };
}

export const config: E2EConfig = {
  baseUrl: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000',
  organisationId: '1',
  defaultTimeoutMs: Number(process.env.DEFAULT_TIMEOUT_MS || '30000'),
  navigationTimeoutMs: Number(process.env.NAVIGATION_TIMEOUT_MS || '30000'),
  testUser: {
    username: process.env.TEST_USERNAME || '',
    password: process.env.TEST_PASSWORD || '',
  },
  avlFeed: {
    url: process.env.TEST_AVL_FEED_URL || 'https://example.com/avl.xml',
  },
};