FROM alpine:3.18 

RUN apk add --no-cache curl jq

COPY run_ogc_process_entrypoint.sh /usr/share/ogc/run_ogc_process_entrypoint.sh
WORKDIR /usr/share/ogc
RUN chmod +x /usr/share/ogc/run_ogc_process_entrypoint.sh
ENTRYPOINT ["/usr/share/ogc/run_ogc_process_entrypoint.sh"]
