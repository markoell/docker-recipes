# set alpine as the base image of the Dockerfile
FROM alpine:3.17

EXPOSE 9050

# update the package repository and install Tor
RUN apk update && \
    apk upgrade && \
    apk add tor

# << Enable this section when tor is accessed from host >>
# Copy over the torrc created above and set the owner to `tor`
COPY torrc /etc/tor/torrc
RUN chown -R tor /etc/tor

# Set `tor` as the default user during the container runtime
USER tor

# Set `tor` as the entrypoint for the image
ENTRYPOINT [ "tor" ]