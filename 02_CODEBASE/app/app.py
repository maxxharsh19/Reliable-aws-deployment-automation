
import json
import logging
import os
import re
import time
import uuid

from datetime import datetime, timezone

from flask import (
    Flask,
    jsonify,
    render_template_string,
    request,
    g,
)


# --------------------------------------------------
# APPLICATION CONFIGURATION
# --------------------------------------------------

APP_NAME = os.getenv(
    "APP_NAME",
    "Deployment Health & Status API"
)

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

APP_ENV = os.getenv("APP_ENV", "production")

APP_COMMIT = os.getenv("APP_COMMIT", "local-build")

PORT = int(os.getenv("PORT", "5000"))

STARTED_AT = datetime.now(timezone.utc)
STARTED_MONOTONIC = time.monotonic()


app = Flask(__name__)


# --------------------------------------------------
# STRUCTURED JSON LOGGING
# --------------------------------------------------

class JSONFormatter(logging.Formatter):

    def format(self, record):

        log_entry = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "service": APP_NAME,
            "message": record.getMessage(),
        }

        for field in (
            "request_id",
            "method",
            "path",
            "status_code",
            "duration_ms",
        ):
            value = getattr(record, field, None)

            if value is not None:
                log_entry[field] = value

        if record.exc_info:
            log_entry["exception"] = (
                self.formatException(record.exc_info)
            )

        return json.dumps(log_entry)


logger = logging.getLogger("deployment_api")

logger.setLevel(
    os.getenv("LOG_LEVEL", "INFO").upper()
)

if not logger.handlers:

    handler = logging.StreamHandler()

    handler.setFormatter(JSONFormatter())

    logger.addHandler(handler)

    logger.propagate = False


# --------------------------------------------------
# REQUEST TRACKING AND SECURITY HEADERS
# --------------------------------------------------

@app.before_request
def before_request():

    incoming_id = request.headers.get(
        "X-Request-ID", ""
    )

    if (
        incoming_id
        and len(incoming_id) <= 64
        and re.fullmatch(
            r"[A-Za-z0-9._-]+",
            incoming_id
        )
    ):
        g.request_id = incoming_id

    else:
        g.request_id = uuid.uuid4().hex

    g.request_started = time.perf_counter()


@app.after_request
def after_request(response):

    duration = (
        time.perf_counter()
        - getattr(g, "request_started", time.perf_counter())
    ) * 1000

    response.headers["X-Request-ID"] = getattr(
        g, "request_id", uuid.uuid4().hex
    )

    response.headers["X-Content-Type-Options"] = "nosniff"

    response.headers["X-Frame-Options"] = "DENY"

    response.headers["Referrer-Policy"] = (
        "strict-origin-when-cross-origin"
    )

    response.headers["Cache-Control"] = "no-store"

    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=()"
    )

    logger.info(
        "HTTP request completed",
        extra={
            "request_id": getattr(g, "request_id", None),
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "duration_ms": round(duration, 2),
        }
    )

    return response


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def utc_timestamp():

    return datetime.now(timezone.utc).isoformat()


def get_uptime():

    return max(
        0,
        int(time.monotonic() - STARTED_MONOTONIC)
    )


def format_uptime(seconds):

    days, remainder = divmod(seconds, 86400)

    hours, remainder = divmod(remainder, 3600)

    minutes, secs = divmod(remainder, 60)

    return (
        f"{days}d {hours}h {minutes}m {secs}s"
    )


def error_response(code, message, status_code):

    return jsonify({
        "error": {
            "code": code,
            "message": message,
            "request_id": getattr(
                g, "request_id", None
            ),
            "timestamp": utc_timestamp(),
        }
    }), status_code


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1">

    <meta name="theme-color" content="#0b1220">

    <title>{{ app_name }} | Operations Console</title>

    <style>
        :root {
            color-scheme: dark;
            --bg: #0b1220;
            --panel: #121d30;
            --border: #26364e;
            --text: #eef4ff;
            --muted: #94a3b8;
            --green: #30d69a;
            --blue: #65a8ff;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            background:
                radial-gradient(
                    circle at top right,
                    #172d4c 0,
                    transparent 38%
                ),
                var(--bg);
            color: var(--text);
            font-family:
                Inter, system-ui, -apple-system,
                BlinkMacSystemFont, "Segoe UI", sans-serif;
            min-height: 100vh;
        }

        .container {
            width: min(1080px, 92%);
            margin: auto;
            padding: 34px 0 50px;
        }

        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 42px;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            font-weight: 700;
            font-size: 16px;
        }

        .logo {
            width: 42px;
            height: 42px;
            border-radius: 12px;
            display: grid;
            place-items: center;
            color: var(--green);
            background: #163a37;
            font-size: 21px;
            font-weight: 800;
        }

        .badge {
            border: 1px solid #236c55;
            color: var(--green);
            padding: 7px 12px;
            border-radius: 30px;
            font-size: 12px;
            background: #102d29;
        }

        .eyebrow {
            color: var(--blue);
            font-size: 12px;
            letter-spacing: 2px;
            font-weight: 700;
            text-transform: uppercase;
        }

        h1 {
            margin: 12px 0;
            font-size: clamp(30px, 5vw, 48px);
            letter-spacing: -1.5px;
        }

        .subtitle {
            color: var(--muted);
            max-width: 680px;
            line-height: 1.7;
            font-size: 15px;
        }

        .grid {
            display: grid;
            grid-template-columns:
                repeat(2, minmax(0, 1fr));
            gap: 18px;
            margin-top: 32px;
        }

        .card {
            background: rgba(18, 29, 48, 0.92);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 23px;
            min-height: 145px;
        }

        .card-label {
            color: var(--muted);
            font-size: 13px;
        }

        .card-value {
            font-size: 25px;
            font-weight: 700;
            margin: 18px 0 8px;
        }

        .card-meta {
            color: var(--muted);
            font-size: 12px;
        }

        .green {
            color: var(--green);
        }

        .blue {
            color: var(--blue);
        }

        .section-title {
            margin: 38px 0 15px;
            font-size: 17px;
        }

        .endpoints {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 18px;
            overflow: hidden;
        }

        .endpoint {
            padding: 16px 20px;
            display: flex;
            align-items: center;
            gap: 18px;
            border-bottom: 1px solid var(--border);
        }

        .endpoint:last-child {
            border-bottom: 0;
        }

        .method {
            min-width: 48px;
            color: var(--green);
            font-size: 11px;
            font-weight: 800;
        }

        code {
            color: #b5d5ff;
            font-size: 13px;
        }

        .endpoint-desc {
            margin-left: auto;
            color: var(--muted);
            font-size: 12px;
            text-align: right;
        }

        .footer {
            margin-top: 35px;
            border-top: 1px solid var(--border);
            padding-top: 20px;
            color: var(--muted);
            display: flex;
            justify-content: space-between;
            gap: 12px;
            flex-wrap: wrap;
            font-size: 12px;
        }

        button {
            border: 1px solid var(--border);
            color: var(--text);
            background: var(--panel);
            padding: 10px 15px;
            border-radius: 10px;
            cursor: pointer;
        }

        button:hover {
            border-color: var(--blue);
        }

        @media (max-width: 650px) {
            .grid {
                grid-template-columns: 1fr;
            }

            .topbar {
                align-items: flex-start;
            }

            .endpoint {
                flex-wrap: wrap;
            }

            .endpoint-desc {
                margin-left: 0;
                width: 100%;
                text-align: left;
            }
        }
    </style>
</head>

<body>

<div class="container">

    <header class="topbar">

        <div class="brand">
            <div class="logo">D</div>
            <div>
                Deployment Operations
                <div class="card-label">Platform Console</div>
            </div>
        </div>

        <div class="badge" id="health-badge">
            ● Checking service
        </div>

    </header>

    <main>

        <div class="eyebrow">
            Infrastructure & Deployment
        </div>

        <h1>Application Operations Console</h1>

        <p class="subtitle">
            A deployment observability dashboard providing
            application health, release information and
            runtime status through lightweight API endpoints.
        </p>

        <div class="grid">

            <section class="card">
                <div class="card-label">
                    SERVICE HEALTH
                </div>

                <div class="card-value green"
                     id="service-health">
                    Checking...
                </div>

                <div class="card-meta">
                    Liveness endpoint: /health
                </div>
            </section>

            <section class="card">
                <div class="card-label">
                    APPLICATION VERSION
                </div>

                <div class="card-value blue"
                     id="app-version">
                    {{ app_version }}
                </div>

                <div class="card-meta">
                    Current release identifier
                </div>
            </section>

            <section class="card">
                <div class="card-label">
                    RUNTIME UPTIME
                </div>

                <div class="card-value"
                     id="app-uptime">
                    Loading...
                </div>

                <div class="card-meta">
                    Current application process
                </div>
            </section>

            <section class="card">
                <div class="card-label">
                    DEPLOYMENT ENVIRONMENT
                </div>

                <div class="card-value"
                     id="app-environment">
                    Loading...
                </div>

                <div class="card-meta">
                    Application runtime configuration
                </div>
            </section>

        </div>

        <h2 class="section-title">
            Available API Endpoints
        </h2>

        <div class="endpoints">

            <div class="endpoint">
                <span class="method">GET</span>
                <code>/health</code>
                <span class="endpoint-desc">
                    Liveness check
                </span>
            </div>

            <div class="endpoint">
                <span class="method">GET</span>
                <code>/ready</code>
                <span class="endpoint-desc">
                    Readiness check
                </span>
            </div>

            <div class="endpoint">
                <span class="method">GET</span>
                <code>/version</code>
                <span class="endpoint-desc">
                    Release information
                </span>
            </div>

            <div class="endpoint">
                <span class="method">GET</span>
                <code>/status</code>
                <span class="endpoint-desc">
                    Runtime status
                </span>
            </div>

        </div>

    </main>

    <footer class="footer">
        <span>{{ app_name }}</span>
        <span id="last-checked">Waiting for status check</span>
        <button onclick="refreshStatus()">
            Refresh status
        </button>
    </footer>

</div>

<script>
async function refreshStatus() {

    const badge = document.getElementById(
        "health-badge"
    );

    try {

        const results = await Promise.all([
            fetch("/health", {cache: "no-store"}),
            fetch("/status", {cache: "no-store"})
        ]);

        if (!results[0].ok || !results[1].ok) {
            throw new Error("Service check failed");
        }

        const health = await results[0].json();
        const status = await results[1].json();

        badge.textContent = "● " + health.status;
        badge.style.color = "#30d69a";

        document.getElementById(
            "service-health"
        ).textContent = health.status.toUpperCase();

        document.getElementById(
            "app-version"
        ).textContent = status.version;

        document.getElementById(
            "app-uptime"
        ).textContent = status.uptime;

        document.getElementById(
            "app-environment"
        ).textContent = status.environment;

        document.getElementById(
            "last-checked"
        ).textContent =
            "Last checked: " +
            new Date().toLocaleTimeString();

    } catch (error) {

        badge.textContent = "● Service unavailable";
        badge.style.color = "#ff7070";

        document.getElementById(
            "service-health"
        ).textContent = "Unavailable";
    }
}

refreshStatus();

setInterval(refreshStatus, 15000);
</script>

</body>
</html>
"""


# --------------------------------------------------
# DASHBOARD ROUTE
# --------------------------------------------------

@app.get("/")
def dashboard():

    return render_template_string(
        DASHBOARD_HTML,
        app_name=APP_NAME,
        app_version=APP_VERSION
    )


# --------------------------------------------------
# HEALTH ENDPOINT
# --------------------------------------------------

@app.get("/health")
def health():

    return jsonify({
        "status": "ok",
        "service": APP_NAME,
        "timestamp": utc_timestamp()
    }), 200


# --------------------------------------------------
# READINESS ENDPOINT
# --------------------------------------------------

@app.get("/ready")
def readiness():

    return jsonify({
        "status": "ready",
        "checks": {
            "application": "ok"
        },
        "timestamp": utc_timestamp()
    }), 200


# --------------------------------------------------
# VERSION ENDPOINT
# --------------------------------------------------

@app.get("/version")
def version():

    return jsonify({
        "service": APP_NAME,
        "version": APP_VERSION,
        "environment": APP_ENV,
        "build": APP_COMMIT,
        "timestamp": utc_timestamp()
    }), 200


# --------------------------------------------------
# RUNTIME STATUS ENDPOINT
# --------------------------------------------------

@app.get("/status")
def status():

    uptime_seconds = get_uptime()

    return jsonify({
        "status": "operational",
        "service": APP_NAME,
        "version": APP_VERSION,
        "environment": APP_ENV,
        "uptime_seconds": uptime_seconds,
        "uptime": format_uptime(uptime_seconds),
        "started_at": STARTED_AT.isoformat(),
        "timestamp": utc_timestamp()
    }), 200


# --------------------------------------------------
# ERROR HANDLING
# --------------------------------------------------

@app.errorhandler(404)
def not_found(error):

    return error_response(
        "NOT_FOUND",
        "The requested endpoint was not found.",
        404
    )


@app.errorhandler(405)
def method_not_allowed(error):

    return error_response(
        "METHOD_NOT_ALLOWED",
        "The HTTP method is not supported for this endpoint.",
        405
    )


@app.errorhandler(Exception)
def handle_unexpected_error(error):

    logger.exception(
        "Unhandled application exception",
        extra={
            "request_id": getattr(
                g, "request_id", None
            ),
            "method": request.method,
            "path": request.path,
        }
    )

    return error_response(
        "INTERNAL_SERVER_ERROR",
        "An unexpected server error occurred.",
        500
    )


# --------------------------------------------------
# LOCAL DEVELOPMENT ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False
    )
