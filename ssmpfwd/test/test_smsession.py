from ssmpfwd.smsession import ForwardingSMSession, ConsoleSMSession
from unittest.mock import MagicMock, patch
import unittest


class TestConsoleSMSession(unittest.TestCase):
    def setUp(self) -> None:
        self.test_command = 'aws --profile profile_name --region region_name ssm start-session \
--target instance_id'
        self.ConsoleSMSession = ConsoleSMSession('instance_id', 'profile_name', 'region_name')

    def test_prompt(self):
        self.assertTrue(self.ConsoleSMSession.prompt, 'sh.*\$ $')

    def test_build_command(self):
        self.assertEqual(self.ConsoleSMSession.command, self.test_command)

    @patch('ssmpfwd.smsession.pexpect')
    def test_connect(self, spawn_mock):
        spawn_mock.spawn.return_value.pid = '123456'
        spawn_mock.spawn.return_value.expect.return_value = self.ConsoleSMSession.prompt
        with self.assertLogs('ssmpfwd.smsession', level='DEBUG') as cm:
            self.ConsoleSMSession.connect()
            spawn_mock.spawn.assert_called_once()
            self.assertTrue(spawn_mock.spawn.return_value.expect.called)
            self.assertEqual(cm.output[1], 'DEBUG:ssmpfwd.smsession:PID: 123456')

    def test_exit(self):
        self.ConsoleSMSession.child = MagicMock()
        with self.assertLogs('ssmpfwd.smsession', level='DEBUG') as cm:
            self.ConsoleSMSession.exit()
            self.ConsoleSMSession.child.sendcontrol.assert_called_with('c')
            self.ConsoleSMSession.child.sendline.assert_called_with('exit')


class TestForwardingSMSession(unittest.TestCase):

    def setUp(self) -> None:
        self.test_command = 'aws --profile profile_name --region region_name ssm start-session \
--target instance_id --document-name AWS-StartPortForwardingSession \
--parameters {\\"portNumber\\":[\\"2345\\"],\\"localPortNumber\\":[\\"1234\\"]}'
        self.ForwardingSMSession = ForwardingSMSession(
            'instance_id', 'profile_name', 'region_name',
            document_name='AWS-StartPortForwardingSession',
            parameters='{\\"portNumber\\":[\\"2345\\"],\\"localPortNumber\\":[\\"1234\\"]}')

    def test_build_command(self):
        self.assertEqual(self.ForwardingSMSession.command, self.test_command)

    @patch('ssmpfwd.smsession.pexpect')
    def test_connect(self, spawn_mock):
        spawn_mock.spawn.return_value.pid = '123456'
        with self.assertLogs('ssmpfwd.smsession', level='DEBUG') as cm:
            self.ForwardingSMSession.connect()
            spawn_mock.spawn.assert_called_once()
            self.assertEqual(cm.output[1], 'DEBUG:ssmpfwd.smsession:PID: 123456')

    def test_exit(self):
        self.ForwardingSMSession.child = MagicMock()
        with self.assertLogs('ssmpfwd.smsession', level='DEBUG') as cm:
            self.ForwardingSMSession.exit()
            self.ForwardingSMSession.child.sendcontrol.assert_called_once_with('c')
