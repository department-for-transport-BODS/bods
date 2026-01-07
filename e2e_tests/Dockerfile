# Dockerfile for running E2E tests in CI/CD or AWS
FROM mcr.microsoft.com/playwright:v1.57.0-jammy

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install Node.js dependencies
RUN npm ci

# Copy test files
COPY . ./

# Set environment variables
ENV CI=true
ENV TEST_BASE_URL=${TEST_BASE_URL}
ENV TEST_DATA_URL=${TEST_DATA_URL}
ENV TEST_PUBLISH_URL=${TEST_PUBLISH_URL}
ENV TEST_USER_EMAIL=${TEST_USER_EMAIL}
ENV TEST_USER_PASSWORD=${TEST_USER_PASSWORD}
ENV TEST_ORGANISATION_NAME=${TEST_ORGANISATION_NAME}
ENV DEFAULT_TIMEOUT=${DEFAULT_TIMEOUT}
ENV NAVIGATION_TIMEOUT=${NAVIGATION_TIMEOUT}

# Playwright browsers are already included in base image

# Default command runs the tests
CMD ["npm", "test"]
