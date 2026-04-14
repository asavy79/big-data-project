FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.d/99-listen-port.sh /docker-entrypoint.d/99-listen-port.sh
RUN chmod +x /docker-entrypoint.d/99-listen-port.sh
EXPOSE 8080
ENV PORT=8080
