# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim AS base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

RUN apt update && apt upgrade -y && apt install wget build-essential cmake ffmpeg libsm6 libxext6 libxrender-dev libglib2.0-0 git -y && apt clean && rm -rf /var/cache/apt/*

# install PDM
RUN pip install -U pip setuptools wheel
RUN pip install pdm

WORKDIR /app

# copy files
COPY pyproject.toml pdm.lock README.md /app/

FROM base AS deps

RUN mkdir __pypackages__ && pdm sync --prod --no-editable

COPY . .

FROM deps AS build

RUN pdm sync

# RUN pdm build

FROM base AS final
# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    appuser

# Give ownership of the app to the non-privileged user.
RUN chown -R appuser:appuser /app && mkdir -p /shared && chown -R appuser:appuser /shared
RUN pip install git+https://github.com/ageitgey/face_recognition_models && pip install celery
# Switch to the non-privileged user to run the application.
# USER appuser

# retrieve packages from build stage
COPY --from=deps /app/__pypackages__ /app/__pypackages__

# Copy the source code into the container.
COPY --from=build /app/src /app/src

# Copy alemibc project files
# COPY --from=build /app/migrations /app/migrations
COPY --from=build /app/alembic.ini /app/alembic.ini
COPY --from=build /app/face_encodings.pkl /app/face_encodings.pkl
COPY --from=build /app/migrations.sql /app/migrations.sql
COPY --from=build /app/devops/startup.sh /app/startup.sh

RUN chmod +x /app/startup.sh

# Expose the port that the application listens on.
EXPOSE 8000

# ENV vars
ENV BASE_URL=http://localhost:8000
ENV ROOT_PATH=/
ENV PORT=8000
# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=5 CMD wget --quiet --tries=1 --spider http://localhost:${PORT}/healthcheck || exit 1

# Run the application.
CMD [ "/app/startup.sh"]
# CMD [ "sleep", "infinity" ]
