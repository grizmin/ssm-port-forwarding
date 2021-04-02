from click.testing import CliRunner
from unittest.mock import MagicMock
from ssmpfwd.cli import cli


def test_sync():
  runner = CliRunner()
  result = runner.invoke(cli, ['--debug', 'sync'])
  assert result.exit_code == 0
  assert 'Debug mode is on' in result.output
  assert 'Syncing' in result.output