FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
# Check https://github.com/nodejs/docker-node/tree/b4117f9333da4138b03a546ec926ef50a31506c3#nodealpine to understand why libc6-compat might be needed.
RUN apk add --no-cache libc6-compat
WORKDIR /

# Copy package.json and other necessary files
COPY nextjs-client /nextjs-client

# Copy react-xrx-client
COPY xrx-core/react-xrx-client /xrx-core/react-xrx-client

# Return to app directory and install dependencies
WORKDIR /nextjs-client
RUN npm ci

# Build stage
FROM deps AS builder
WORKDIR /nextjs-client
# Build the application
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /nextjs-client

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Now these COPY instructions will work correctly
COPY --from=builder /nextjs-client/public ./public

# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=builder /nextjs-client/.next/standalone ./
COPY --from=builder /nextjs-client/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000

CMD ["node", "server.js"]