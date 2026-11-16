# syntax=docker/dockerfile:1
#
# Multi-stage build for screenuploader (Django 5.2 on Python 3.13, Alpine).
#   builder: resolves/installs locked deps with uv into /app/.venv.
#   runtime: small image, non-root user, venv + code + ffmpeg only.
#
# Base tags verified 2026-11-16 via `docker manifest inspect`:
#   python:3.13-alpine, ghcr.io/astral-sh/uv:0.13.7.

ARG PYTHON_TAG=3.13-alpine
ARG UV_VERSION=0.13.7

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

FROM python:${PYTHON_TAG} AS builder

COPY --from=uv /uv /uvx /bin/

ENV UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# musl build toolchain for the packages that ship only sdists
# (autobahn, django-admin-actions, zope-interface C extension).
# Everything else installs from musllinux/abi3/py3 wheels. Builder only —
# none of this reaches the runtime stage.
RUN apk add --no-cache build-base

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project --python 3.13


FROM python:${PYTHON_TAG} AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Non-root runtime user. Fixed uid so volume ownership is predictable.
# BusyBox tools: Alpine has no useradd/groupadd.
RUN addgroup -S -g 10001 app \
  && adduser -S -u 10001 -G app -h /home/app -s /sbin/nologin app

# System ffmpeg provides the ffprobe/ffmpeg binaries used by app/video.py.
RUN apk add --no-cache ffmpeg

# Interpreter + locked third-party deps. No build tools, no pip, no git.
COPY --from=builder /app/.venv /app/.venv

COPY . .

# Writable dirs for collectstatic (public/static), user uploads
# (public/uploads) and app logs; entrypoint scripts executable.
# No package manager calls and no system writes: docker-entrypoint.sh only
# waits on the DB via Django, then runs migrate + collectstatic + exec "$@".
RUN mkdir -p public/static public/uploads logs \
  && chmod +x docker-entrypoint.sh manage.py \
  && chown -R app:app /app /home/app

USER app

EXPOSE 8000

# `/` is an unauthenticated TemplateView (config/urls.py) with no DB or
# side effects, so it is safe to probe without auth.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/')"

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["hypercorn", "--bind", "0.0.0.0:8000", "config.asgi:application"]
