FROM ghcr.io/astral-sh/uv:python3.14-alpine

WORKDIR /code

ADD pyproject.toml .
ADD uv.lock .

# Install the compilers and libraries required to build NumPy (and OpenCV) on Alpine,
# and also install `protoc` (protobuf compiler) which is needed by prost‑wkt‑types.
RUN apk add --no-cache build-base openblas-dev protobuf

RUN uv sync --locked

ADD main.py .
ADD app .

