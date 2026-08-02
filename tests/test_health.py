import unittest
from runtime import health

class TestHealth(unittest.TestCase):
    def test_check_environment_returns_dict(self):
        env = health.check_environment()
        self.assertIsInstance(env, dict)
        # Basic keys present
        self.assertIn("ffmpeg", env)
        self.assertIn("ffprobe", env)
        self.assertIn("python_version", env)

    def test_check_capabilities_safe_without_registry(self):
        # Pass an object with minimal shape
        class DummyRegistry:
            def capability_catalog(self):
                return {"image_generation": {"configured": True}, "video_generation": {"configured": False}}
        r = DummyRegistry()
        cap_report = health.check_capabilities(r)
        self.assertIsInstance(cap_report, dict)
        self.assertIn("environment", cap_report)
        self.assertIn("capabilities", cap_report)
        self.assertIn("image_generation", cap_report["capabilities"])

if __name__ == "__main__":
    unittest.main()
