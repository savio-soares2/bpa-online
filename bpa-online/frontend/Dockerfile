FROM node:18-alpine

WORKDIR /app

# Copia package files
COPY package*.json ./

# Instala dependências
RUN npm install

# Copia código fonte
COPY . .

# Expõe porta
EXPOSE 3000

# Comando padrão
CMD ["npm", "start"]
