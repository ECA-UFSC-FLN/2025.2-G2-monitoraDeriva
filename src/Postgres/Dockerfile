FROM postgres:latest

ENV POSTGRES_USER=derivaiot
ENV POSTGRES_PASSWORD=3vKRgfXP
ENV POSTGRES_DB=derivaiot

COPY schema.sql /docker-entrypoint-initdb.d/

EXPOSE 5432