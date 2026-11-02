import unittest

from app import app


class DeploymentAPITests(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_dashboard_loads(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            b"Application Operations Console",
            response.data
        )

    def test_health_endpoint(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(data["status"], "ok")
        self.assertIn("timestamp", data)

    def test_readiness_endpoint(self):
        response = self.client.get("/ready")

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(data["status"], "ready")
        self.assertEqual(
            data["checks"]["application"],
            "ok"
        )

    def test_version_endpoint(self):
        response = self.client.get("/version")

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertIn("version", data)
        self.assertIn("environment", data)
        self.assertIn("build", data)

    def test_status_endpoint(self):
        response = self.client.get("/status")

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(data["status"], "operational")
        self.assertGreaterEqual(
            data["uptime_seconds"],
            0
        )

    def test_request_id_is_generated(self):
        response = self.client.get("/health")

        self.assertTrue(
            response.headers.get("X-Request-ID")
        )

    def test_custom_request_id_is_preserved(self):
        response = self.client.get(
            "/health",
            headers={"X-Request-ID": "test-run-123"}
        )

        self.assertEqual(
            response.headers["X-Request-ID"],
            "test-run-123"
        )

    def test_invalid_request_id_is_replaced(self):
        response = self.client.get(
            "/health",
            headers={"X-Request-ID": "invalid id!"}
        )

        self.assertNotEqual(
            response.headers["X-Request-ID"],
            "invalid id!"
        )

    def test_security_headers(self):
        response = self.client.get("/health")

        self.assertEqual(
            response.headers["X-Content-Type-Options"],
            "nosniff"
        )

        self.assertEqual(
            response.headers["X-Frame-Options"],
            "DENY"
        )

    def test_invalid_endpoint_returns_404(self):
        response = self.client.get("/unknown-endpoint")

        self.assertEqual(response.status_code, 404)

        data = response.get_json()

        self.assertEqual(
            data["error"]["code"],
            "NOT_FOUND"
        )

    def test_unsupported_method_returns_405(self):
        response = self.client.post("/health")

        self.assertEqual(response.status_code, 405)

        data = response.get_json()

        self.assertEqual(
            data["error"]["code"],
            "METHOD_NOT_ALLOWED"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
