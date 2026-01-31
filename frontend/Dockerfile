# Build stage
FROM node:20-alpine AS build

WORKDIR /app

# Install dependencies - use npm install instead of npm ci for flexibility
COPY package.json ./
RUN npm install

# Copy source code
COPY . .

# Build the application (output to /app/dist)
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files from dist directory
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
