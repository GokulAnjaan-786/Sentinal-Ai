# ==========================================
# SentinelAI Frontend Dockerfile
# ==========================================
# Multi-stage build for optimized production image

# ---- Stage 1: Build ----
FROM node:20-alpine as builder

WORKDIR /app

# Copy package files first (layer caching)
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm install

# Copy source code
COPY frontend/ .

# Build for production
RUN npm run build


# ---- Stage 2: Production ----
FROM nginx:alpine as production

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
