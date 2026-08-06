FROM node:22-bookworm-slim

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Baked into the client JS bundle at build time by Next.js, so it must be
# declared as a build ARG (and promoted to ENV so `next build` can see it)
# rather than read at container-start time. Portway passes this in as a
# --build-arg automatically because of the NEXT_PUBLIC_ prefix, but a
# custom Dockerfile still has to explicitly declare it to receive it,
# an auto-generated one does this for you, this one doesn't get that
# for free.
ARG NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL

RUN npm run build
RUN npm prune --omit=dev

EXPOSE 3000
CMD ["npm", "start"]
