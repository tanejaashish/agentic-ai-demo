# Frontend Dockerfile for Agentic AI Demo

FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps
#RUN npm ci --only=production

# Copy application files
COPY . .

# Build the application (if needed)
# RUN npm run build

# Expose port
EXPOSE 3000

# Set environment variables for build
ENV REACT_APP_API_URL=http://localhost:8000
ENV REACT_APP_WS_URL=ws://localhost:8000
ENV NODE_ENV=development
ENV CI=false
ENV SKIP_PREFLIGHT_CHECK=true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000', (res) => { process.exit(res.statusCode === 200 ? 0 : 1); })"

# Start the application
CMD ["npm", "start"]
