# Monitoring and Observability Guide

This guide details how to monitor the health and performance of the PromptCraft Hybrid System.

## 1. Prometheus Metrics

The system exposes Prometheus metrics that can be used to monitor the health and performance of the services. The metrics are available at the following endpoints:

* **FastAPI Backend:** `http://localhost:8000/metrics`

## 2. Structured Logging

The system uses structured logging to make it easier to query and analyze logs. Logs are written to standard output in JSON format.

## 3. Sentry Integration

The system is integrated with Sentry for error tracking. To enable Sentry, set the `SENTRY_DSN` environment variable in your `.env` file:

```
SENTRY_DSN=<your_sentry_dsn>
```
