# Simple production image
FROM node:20-alpine
WORKDIR /app
COPY package.json ./
# no deps to install; keep layer for future
RUN true
COPY src ./src
COPY public ./public
ENV PORT=3000 NODE_ENV=production
EXPOSE 3000
CMD ["node", "src/server.js"]
