FROM node:24-slim AS dependencies

WORKDIR /app

COPY bods-nextjs/package.json bods-nextjs/package-lock.json ./

RUN npm ci --ignore-scripts

FROM dependencies AS builder

COPY bods-nextjs ./

ARG NEXT_PUBLIC_BODS_BASE_DOMAIN

RUN npm run build

FROM node:24-slim AS runner

ENV NODE_ENV=production \
    PORT=5000 \
    HOSTNAME=0.0.0.0

WORKDIR /app

RUN groupadd --system nextjs && useradd --system --gid nextjs nextjs

COPY --from=builder --chown=nextjs:nextjs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nextjs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nextjs /app/public ./public

USER nextjs

EXPOSE 5000

CMD ["node", "server.js"]