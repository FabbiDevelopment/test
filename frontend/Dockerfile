# THÊM: Multi-stage build — stage build + stage serve static (Level 3B)
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
# SAI (cũ): npm install sau COPY . . — cache layer kém, build chậm
# THÊM: npm ci trước khi copy source
RUN npm ci
COPY . .
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM node:20-alpine AS runtime
WORKDIR /app
RUN npm install -g serve@14
COPY --from=build /app/dist ./dist
EXPOSE 3000
USER node
CMD ["serve", "-s", "dist", "-l", "3000"]
