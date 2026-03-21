# ==========================================
# STAGE 1: BUILDER
# ==========================================
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim@sha256:4f5d923c9dcea037f57bda425dd209f3ec643da2f0b74227f68d09dab0b3bb36 AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app

# Install BUILD dependencies 
RUN apt-get update && apt-get install -y --no-install-recommends \
    git gcc libmariadb-dev-compat libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN uv venv /app/.venv
ENV UV_PYTHON_DOWNLOADS=0
ENV UV_NO_CACHE=1

# Install dependencies into the virtual environment using uv
RUN --mount=type=bind,source=requirements.txt,target=requirements.txt \
    uv pip install -r requirements.txt


# ==========================================
# STAGE 2: RUNTIME (Final Image)
# ==========================================
FROM python:3.11-slim-bookworm@sha256:420310dd2ff7895895f0f1f9d15cae5a95dabceb8f1d6b9a23ef33c2c1c542c3

LABEL org.opencontainers.image.maintainer="Giuseppe De Marco <giuseppe.demarco@unical.it>"
LABEL org.opencontainers.image.source=https://github.com/UniversitaDellaCalabria/uniTicket
LABEL org.opencontainers.image.description="uniTicket"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LANG=it_IT.UTF-8 \
    LANGUAGE=it_IT \
    LC_ALL=it_IT.UTF-8 \
    PATH="/app/.venv/bin:$PATH"

# Install RUNTIME dependencies only (no dev tools or compilers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales poppler-utils xmlsec1 libmagic1 \
    libmariadb3 libgtk2.0-0 libpango-1.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    # Generate Italian locales for Django
    && sed -i 's/# it_IT.UTF-8 UTF-8/it_IT.UTF-8 UTF-8/' /etc/locale.gen \
    && locale-gen it_IT.UTF-8

WORKDIR /app

# Copy the fully built virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy the rest of your application code
COPY . /app


# use bootstrap_italia as default template
# RUN ls ./templates
# RUN curl https://raw.githubusercontent.com/italia/design-django-theme/master/bootstrap_italia_template/templates/bootstrap-italia-base.html --output templates/base-setup.html