FROM nginx:1.19-alpine

COPY ./conf/ /etc/nginx
COPY ./conf.d/ /etc/nginx/conf.d

CMD ["nginx", "-g", "daemon off;"]
