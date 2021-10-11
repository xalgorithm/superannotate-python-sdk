import sys
from io import StringIO
import json
from contextlib import contextmanager
import pkg_resources
from unittest import TestCase
from unittest.mock import mock_open
from unittest.mock import patch

from src.superannotate.lib.app.interface.cli_interface import CLIFacade
from src.superannotate.lib.core import CONFIG_FILE_LOCATION


try:
    CLI_VERSION = pkg_resources.get_distribution("superannotate").version
except Exception:
    CLI_VERSION = None


@contextmanager
def catch_prints():
    out = StringIO()
    sys.stdout = out
    yield out


class CLITest(TestCase):

    @patch('builtins.input')
    def test_init_update(self, input_mock):
        input_mock.side_effect = ["y", "token"]
        with open(CONFIG_FILE_LOCATION) as f:
            config_data = f.read()
        with patch('builtins.open', mock_open(read_data=config_data)) as config_file:
            try:
                with catch_prints() as out:
                    cli = CLIFacade()
                    cli.init()
            except SystemExit:
                input_args = [i[0][0] for i in input_mock.call_args_list]
                self.assertIn(f"File {CONFIG_FILE_LOCATION} exists. Do you want to overwrite? [y/n] : ", input_args)
                input_mock.assert_called_with("Input the team SDK token from https://app.superannotate.com/team : ")
                config_file().write.assert_called_once_with(
                    json.dumps(
                        {"main_endpoint": "https://api.devsuperannotate.com", "ssl_verify": False, "token": "token"},
                        indent=4
                    )
                )
                self.assertEqual(out.getvalue().strip(), "Configuration file successfully updated.")

    @patch('builtins.input')
    def test_init_create(self, input_mock):
        input_mock.side_effect = ["token"]
        with patch('builtins.open', mock_open(read_data="{}")) as config_file:
            try:
                with catch_prints() as out:
                    cli = CLIFacade()
                    cli.init()
            except SystemExit:
                input_mock.assert_called_with("Input the team SDK token from https://app.superannotate.com/team : ")
                config_file().write.assert_called_once_with(
                    json.dumps(
                        {"token": "token"},
                        indent=4
                    )
                )
                self.assertEqual(out.getvalue().strip(), "Configuration file successfully created.")