FROM python:3.12-alpine

WORKDIR /app

RUN apk update && apk add --no-cache postgresql-dev gcc python3-dev musl-dev

COPY ./frontend /app/frontend
COPY ./templates /app/templates
COPY ./requirements.txt /app/requirements.txt


RUN addgroup -S appgroup && adduser -S appuser -G appgroup

RUN chown -R appuser:appgroup /app



RUN pip install --no-cache-dir -r requirements.txt --break-system-packages

EXPOSE 3007

WORKDIR /app/frontend

USER appuser

CMD ["gunicorn", "--timeout", "120","-w", "4", "-b", "0.0.0.0:3007", "main:app"]

