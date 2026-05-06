FROM node:20-alpine

WORKDIR /app

# Instala deps
COPY package.json package-lock.json* ./
RUN npm install

# Copia código
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
