# --- Stage 1: Builder ---
# Use a lightweight Linux distribution (Alpine) to install the tools.
# Naming this stage "builder" allows us to reference it later.
FROM alpine:3.18 as builder

# Install curl and jq using the Alpine package manager (apk).
# --no-cache avoids writing the package index to disk, keeping the layer small.
RUN apk add --no-cache curl jq


# --- Stage 2: Final Image ---
# Use the same base image for the final product. This ensures compatibility
# of the copied binaries and their libraries.
FROM alpine:3.18

# Copy only the necessary executable files from the "builder" stage.
# This is the key to a small final image. We are not copying the package
# manager or any other unnecessary files.
COPY --from=builder /usr/bin/curl /usr/bin/curl
COPY --from=builder /usr/bin/jq /usr/bin/jq

# Although Airflow will override this with its own commands,
# setting a default command is good practice. It can be used for testing.
# This command simply shows that the tools are available.
CMD ["/bin/sh", "-c", "echo 'curl and jq are installed.'; curl --version; jq --version"]

COPY run_ogc_process_entrypoint.sh /usr/share/ogc/run_ogc_process_entrypoint.sh
WORKDIR /usr/share/ogc
RUN chmod +x /usr/share/ogc/run_ogc_process_entrypoint.sh
ENTRYPOINT ["/usr/share/ogc/run_ogc_process_entrypoint.sh"]
