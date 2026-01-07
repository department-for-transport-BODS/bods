import * as dotenv from 'dotenv';
import * as path from 'path';

dotenv.config({ path: path.resolve(__dirname, '.env') });

export interface TestConfig {
  baseUrl: string;
  dataUrl: string;
  publishUrl: string;
  testUser: {
    email: string;
    password: string;
  };
  testOrganisation: {
    name: string;
  };
  defaultTimeout: number;
  navigationTimeout: number;
}

export const config: TestConfig = {
  baseUrl: process.env.TEST_BASE_URL || 'http://localhost:8000',
  dataUrl: process.env.TEST_DATA_URL || 'https://data.bus-data.dft.gov.uk',
  publishUrl: process.env.TEST_PUBLISH_URL || 'https://publish.bus-data.dft.gov.uk',

  testUser: {
    email: process.env.TEST_USER_EMAIL || 'test@example.com',
    password: process.env.TEST_USER_PASSWORD || 'testpass123',
  },

  testOrganisation: {
    name: process.env.TEST_ORGANISATION_NAME || 'Test Organisation',
  },

  // Timeouts in milliseconds
  defaultTimeout: parseInt(process.env.DEFAULT_TIMEOUT || '30000', 10),
  navigationTimeout: parseInt(process.env.NAVIGATION_TIMEOUT || '30000', 10),
};
