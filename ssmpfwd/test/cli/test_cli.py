from click.testing import CliRunner
from unittest.mock import MagicMock, patch, Mock
from ssmpfwd.cli.cli import spawn_socat, spawn_port_forwarding_ssm_session
import pexpect


from ssmpfwd.cli import cli
import unittest


class TestCli(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_cli_version_ssmpfwd(self):
        result = self.runner.invoke(cli.cli, ["--version"])
        assert result.exit_code == 0
        self.assertRegex(result.output, r"^ssmpfwd/\d+.\d+.\d+", "version should be semver")

    def test_cli_version_python(self):
        result = self.runner.invoke(cli.cli, ["--version"])
        assert result.exit_code == 0
        self.assertRegex(result.output, "python/", "python/ not found in version string")

    def test_cli_version_boto3(self):
        result = self.runner.invoke(cli.cli, ["--version"])
        assert result.exit_code == 0
        self.assertRegex(result.output, "boto3/", "boto3/ not found in version string")

    @patch("ssmpfwd.cli.cli.ConsoleSMSession")
    def test_cli_spawn_socat(self, ConsoleSMSession_mock):
        params = ("profile_name", "region_name", "instance_id", 1234, 2345)
        socat_mock = spawn_socat(*params)
        ConsoleSMSession_mock.assert_called_once_with("instance_id", "profile_name", "region_name", source_port=1234)
        socat_mock.connect.assert_called_once()
        socat_mock.child.sendline.assert_called_once_with("socat TCP-LISTEN:1234,fork TCP:2345")

    @patch("ssmpfwd.cli.cli.ForwardingSMSession")
    def test_cli_spawn_port_forwarding_ssm_session(self, ForwardingSMSession_mock):
        params = ("profile_name", "region_name", "instance_id", 1234, 2345)
        pfwsession_mock = spawn_port_forwarding_ssm_session(*params)
        ForwardingSMSession_mock.assert_called_once_with(
            "instance_id",
            "profile_name",
            "region_name",
            document_name="AWS-StartPortForwardingSession",
            parameters='{\\"portNumber\\":[\\"2345\\"],\\"localPortNumber\\":[\\"1234\\"]}',
        )
        pfwsession_mock.connect.assert_called_once()

    @patch("ssmpfwd.cli.cli.spawn_port_forwarding_ssm_session")
    @patch("ssmpfwd.cli.cli.spawn_socat")
    def test_cli_command_forward_exceptions(self, spawn_socat, spawn_port_forwarding_ssm_session):
        e = pexpect.exceptions.EOF("Some exception")
        spawn_port_forwarding_ssm_session.return_value.child.interact.side_effect = e
        result = self.runner.invoke(cli.cli, "forward --region us-east-1 i-0616ea1bf6338cce6 10.243.9.78:22")

        spawn_port_forwarding_ssm_session.return_value.exit.assert_called_once()
        spawn_socat.return_value.exit.assert_called_once()
        self.assertFalse(result.exit_code)

    @patch("ssmpfwd.cli.cli.spawn_port_forwarding_ssm_session", autospec=True)
    @patch("ssmpfwd.cli.cli.spawn_socat", autospec=True)
    def test_cli_forward(self, spawn_socat, spawn_port_forwarding_ssm_session):
        result = self.runner.invoke(cli.cli, "forward --region us-east-1 i-0616ea1bf6338cce6 10.243.9.78:22")
        source_port = spawn_port_forwarding_ssm_session.call_args[0][-1]
        local_port = spawn_port_forwarding_ssm_session.call_args[0][-2]
        spawn_socat.assert_called_once_with("default", "us-east-1", "i-0616ea1bf6338cce6", source_port, "10.243.9.78:22")
        spawn_port_forwarding_ssm_session.assert_called_once_with("default", "us-east-1", "i-0616ea1bf6338cce6", unittest.mock.ANY, unittest.mock.ANY)
        self.assertFalse(result.exit_code)

    def test_cli_command_mocked(self):
        mock_command_forward = MagicMock()
        result = self.runner.invoke(mock_command_forward, "forward --region us-east-1  i-0616ea1bf6338cce6 10.243.9.78:22")
        assert mock_command_forward.main.mock_calls[0][2]["args"] == ["forward", "--region", "us-east-1", "i-0616ea1bf6338cce6", "10.243.9.78:22"]

    @patch("ssmpfwd.cli.cli.spawn_port_forwarding_ssm_session", autospec=True)
    @patch("ssmpfwd.cli.cli.spawn_socat", autospec=True)
    @patch("logging.Logger.info")
    def test_cli_forward_debug(self, mock, _1, _2):
        self.runner.invoke(cli.cli, "forward --region us-east-1 i-0616ea1bf6338cce6 10.243.9.78:22 --debug")
        mock.assert_any_call("Logger set to DEBUG")

    @patch("ssmpfwd.cli.cli.spawn_port_forwarding_ssm_session", autospec=True)
    @patch("ssmpfwd.cli.cli.spawn_socat", autospec=True)
    @patch("logging.Logger.info")
    def test_cli_forward_verbose(self, mock, _1, _2):

        self.runner.invoke(cli.cli, "forward --region us-east-1 i-0616ea1bf6338cce6 10.243.9.78:22 --verbose")
        mock.assert_any_call("Logger set to INFO")
