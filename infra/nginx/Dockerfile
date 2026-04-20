FROM node:22-alpine AS frontend-builder

ARG VITE_API_BASE_URL=/api/v1

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend ./
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM nginx:1.27-alpine

COPY infra/nginx/default.prod.conf.template /etc/nginx/templates/default.conf.template
COPY --from=frontend-builder /frontend/dist /usr/share/nginx/html

