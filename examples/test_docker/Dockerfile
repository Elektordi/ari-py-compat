FROM christoofar/asterisk as source

FROM scratch
COPY --from=source / /

RUN tar -C /etc/asterisk -xvzf /root/configs.tar.gz
COPY *.conf /etc/asterisk/

ENTRYPOINT [ "/root/start.sh" ]
