FROM php:8.2-cli

# Instalar dependências necessárias para PostgreSQL e zip
RUN apt-get update && apt-get install -y \
    libpq-dev \
    unzip \
    git \
    && docker-php-ext-install pdo pdo_pgsql

# Instalar Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

WORKDIR /app

# Expor porta 8080
EXPOSE 8080

CMD ["php", "-S", "0.0.0.0:8080", "-t", "/app"]
