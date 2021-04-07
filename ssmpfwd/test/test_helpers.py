from ssmpfwd.helpers import verify_plugin_version, verbose_debug_quiet, time_decorator
from unittest.mock import MagicMock, patch
import unittest


class TestVerifyPluginVersion(unittest.TestCase):
    @patch("ssmpfwd.helpers.subprocess")
    def test_verify_plugin_version_success(self, mock_subprocess):
        result = mock_subprocess.run()
        result.stdout = b"9.8.3"
        self.assertTrue(verify_plugin_version("9.8.3"))

    @patch("ssmpfwd.helpers.subprocess")
    def test_verify_plugin_version_fail(self, mock_subprocess):
        with self.assertLogs("ssmpfwd.helpers", level="INFO") as cm:
            result = mock_subprocess.run()
            result.stdout = b"1.8.1"
            self.assertFalse(verify_plugin_version("9.2.3"))
            self.assertEqual(cm.output[0], "ERROR:ssmpfwd.helpers:session-manager-plugin version 1.8.1 is installed, 9.2.3 is required")


class TestVerboseDebugQuiet(unittest.TestCase):
    import logging

    def setUp(self):
        @verbose_debug_quiet
        def test_func():
            pass

        self.vdq = test_func
        self.vdq()

    def test_quiet(self):
        option_name = "quiet"
        self.assertTrue(any([p.name == option_name for p in self.vdq.__click_params__]), msg=f"Can not find {option_name} in option parameters")

    def test_debug(self):
        flag_value = self.logging.DEBUG
        self.assertTrue(any([p.flag_value == flag_value for p in self.vdq.__click_params__]), msg=f"Can not find {flag_value} in option flag values")

    def test_verbose(self):
        flag_value = self.logging.INFO
        self.assertTrue(any([p.flag_value == flag_value for p in self.vdq.__click_params__]), msg=f"Can not find {flag_value} in option flag values")

    def test_default_loglevel(self):
        flag_value = self.logging.WARN
        self.assertTrue(any([p.flag_value == flag_value for p in self.vdq.__click_params__]), msg=f"Can not find {flag_value} in option flag values")


class TestTimeDecorator(unittest.TestCase):
    from time import sleep

    def setUp(self):
        @time_decorator
        def test_func():
            self.sleep(0.5)

        self.time_decorated_method = test_func

    def test_time_decorartor(self):
        with self.assertLogs("ssmpfwd.helpers", level="INFO") as cm:
            self.time_decorated_method()
            self.assertEqual(cm.output[0], "INFO:ssmpfwd.helpers:[*] starting test_func")
