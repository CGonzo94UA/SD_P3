# syntax=docker/dockerfile:1
FROM nginx:latest

COPY ./index.html /usr/share/nginx/html
COPY ./estilos.css /usr/share/nginx/html
COPY ./index.js /usr/share/nginx/html

# Create a configuration file for NGINX
RUN echo "server { listen 9090; root /usr/share/nginx/html; index index.html; }" > /etc/nginx/conf.d/default.conf

# Expose port 9090 and start NGINX
EXPOSE 9090
CMD ["nginx", "-g", "daemon off;"]
