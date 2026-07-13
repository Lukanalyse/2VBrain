FROM node:22-alpine AS build

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./

ARG VITE_API_BASE_URL=http://localhost:8000/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

FROM node:22-alpine

ENV NODE_ENV=production

WORKDIR /app/frontend

COPY --from=build /app/frontend/package.json /app/frontend/package-lock.json ./
COPY --from=build /app/frontend/node_modules ./node_modules
COPY --from=build /app/frontend/.svelte-kit ./.svelte-kit
COPY --from=build /app/frontend/src ./src
COPY --from=build /app/frontend/svelte.config.js ./svelte.config.js
COPY --from=build /app/frontend/vite.config.ts ./vite.config.ts
COPY --from=build /app/frontend/tsconfig.json ./tsconfig.json

EXPOSE 5173

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5173"]
