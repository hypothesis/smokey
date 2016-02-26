FROM gliderlabs/alpine:3.3

# Update the base image and install runtime dependencies.
RUN apk add --no-cache ca-certificates python3 curl && \
    curl -sSL https://bootstrap.pypa.io/get-pip.py | python3

# Create the smokey user, group, home directory and package directory.
RUN addgroup -S smokey && adduser -S -G smokey -h /var/lib/smokey smokey
WORKDIR /var/lib/smokey

# Install python dependencies.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the test files.
COPY features ./features/

# Change ownership of all the files and switch to the smokey user.
RUN chown -R smokey:smokey .
USER smokey

# Set the Python IO encoding to UTF-8.
ENV PYTHONIOENCODING utf_8

# Default command: run the tests.
CMD ["/usr/bin/behave"]
