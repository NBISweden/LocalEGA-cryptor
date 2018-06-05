import unittest
import sys
import os
from legacryptor.cli import parse_args, __doc__
from legacryptor.__main__ import main, run
from pgpy.errors import PGPError
from . import logger_data, gpg_data
from testfixtures import TempDirectory, tempdir
from unittest import mock
from getpass import getpass


class TestCommandLineARGS(unittest.TestCase):
    """CLI args

    Testing command line argument calls."""

    def setUp(self):
        """Setting things up."""
        self._dir = TempDirectory()
        self._path = self._dir.write('pubring.bin', gpg_data.PGP_PUBKEY.encode('utf-8'))
        self._pk = self._dir.write('pub_key.asc', gpg_data.PGP_PUBKEY.encode('utf-8'))
        self._sk = self._dir.write('sec_key.asc', gpg_data.PGP_PRIVKEY.encode('utf-8'))

    def tearDown(self):
        """Remove files."""
        self._dir.cleanup_all()

    def test_cmdline_no_args(self):
        """User passes no args, should fail with SystemExit."""
        with self.assertRaises(SystemExit):
            parse_args()

    def test_cmdline_help(self):
        """User passes help, should return help."""
        with self.assertRaises(SystemExit):
            parse_args(['--help'])
            self.assertEquals(__doc__, sys.stdout)

    def test_cmdline_load_logger(self):
        """Should be able to load a custom logger."""
        with TempDirectory() as filedir:
            filedir.write('logger.yml', logger_data.TEST_LOGGER.encode('utf-8'))
            parse_args(['--log', os.path.join(filedir.path, 'logger.yml'), 'list'])

    def test_cmdline_parse_list(self):
        """User should get an args list when asking for keys list."""
        expected = {'--input': None,
                    '--keyid': None,
                    '--output': None,
                    '--pk': None,
                    '--pubring': self._path,
                    '--server': None,
                    '--sk': None,
                    '-r': 'ega@crg.eu',
                    'decrypt': False,
                    'encrypt': False,
                    'list': True,
                    'reencrypt': False}
        result = parse_args(['list', '--pubring', self._path])
        self.assertEquals(expected, dict(result))

    def test_cmdline_main_fail(self):
        """Run without commandline args, should exit."""
        with self.assertRaises(SystemExit):
            main()

    @mock.patch('legacryptor.__main__.Pubring')
    def test_cmdline_run_list_pubring(self, mock_ring):
        """Listing with specific pubring should call the Pubring."""
        run(['list', '--pubring', self._path])
        mock_ring.assert_called()

    @mock.patch('legacryptor.__main__.encrypt')
    def test_cmdline_run_encrypt_pubring(self, mock_encrypt):
        """Encrypt from the command line should call the encrypt function."""
        run(['encrypt', '--pk', self._pk])
        mock_encrypt.assert_called()

    @mock.patch('getpass.getpass')
    @mock.patch('legacryptor.__main__.decrypt')
    def test_cmdline_run_decrypt_pubring(self, mock_decrypt, mock_pass):
        """Decrypt from the command line should call the decrypt function."""
        mock_pass.return_value = gpg_data.PGP_PASSPHRASE
        run(['decrypt', '--sk', self._sk])
        mock_decrypt.assert_called()

    @mock.patch('getpass.getpass')
    @mock.patch('legacryptor.__main__.reencrypt')
    def test_cmdline_run_reencrypt_pubring(self, mock_reencrypt, mock_pass):
        """Reencrypt from the command line should call the reencrypt function."""
        mock_pass.return_value = gpg_data.PGP_PASSPHRASE
        run(['reencrypt', '--sk', self._sk, '--pk', self._pk])
        mock_reencrypt.assert_called()

    def test_cmdline_server_notimplemented(self):
        """Trying to access server keys should raise NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            run(['list', '--server', 'someserver.com'])

    @tempdir()
    def test_cmdline_encrypt_key_notfound(self, filedir):
        """Raise error if key not found in default pubring."""
        with self.assertRaises(PGPError):
            run(['encrypt', '-r', 'Denmark', '--pubring', self._path])