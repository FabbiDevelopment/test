FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# VITE_API_URL must be present at *build* time - Vite inlines
# import.meta.env.VITE_API_URL into the static bundle when it runs
# `npm run build`. Setting it as a runtime container env var on the
# `frontend` service (as opposed to a build arg) has no effect once the
# bundle already exists.
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM node:20-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=build /app/dist ./dist
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
