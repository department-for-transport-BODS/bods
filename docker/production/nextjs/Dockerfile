FROM node:24-slim AS dependencies

WORKDIR /app

COPY bods-nextjs/package.json bods-nextjs/package-lock.json ./

RUN npm ci --ignore-scripts

FROM dependencies AS builder

COPY bods-nextjs ./

ARG NEXT_PUBLIC_DJANGO_API_URL
ARG NEXT_PUBLIC_BODS_BASE_DOMAIN
ARG DJANGO_INTERNAL_ORIGIN

ENV NEXT_PUBLIC_DJANGO_API_URL=$NEXT_PUBLIC_DJANGO_API_URL \
    NEXT_PUBLIC_BODS_BASE_DOMAIN=$NEXT_PUBLIC_BODS_BASE_DOMAIN \
    DJANGO_INTERNAL_ORIGIN=$DJANGO_INTERNAL_ORIGIN

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