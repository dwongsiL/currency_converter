FROM python:3.12-alpine

WORKDIR /app

RUN apk update && apk add --no-cache postgresql-dev gcc python3-dev musl-dev

COPY . /app

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

RUN chown -R appuser:appgroup /app

USER appuser

RUN pip install --no-cache-dir -r requirements.txt --break-system-packages

EXPOSE 3007

CMD ["gunicorn", "-b", "0.0.0.0:3007", "main:app"]
