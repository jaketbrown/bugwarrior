import configparser
import os
import textwrap
from unittest import TestCase

from bugwarrior.config import load

from ..base import ConfigTest


class LoadTest(ConfigTest):
    def create(self, path):
        """
        Create an empty file in the temporary directory, return the full path.
        """
        fpath = os.path.join(self.tempdir, path)
        if not os.path.exists(os.path.dirname(fpath)):
            os.makedirs(os.path.dirname(fpath))
        open(fpath, 'a').close()
        return fpath


class TestGetConfigPath(LoadTest):
    def test_default(self):
        """
        If it exists, use the file at $XDG_CONFIG_HOME/bugwarrior/bugwarriorrc
        """
        rc = self.create('.config/bugwarrior/bugwarriorrc')
        self.assertEqual(load.get_config_path(), rc)

    def test_legacy(self):
        """
        Falls back on .bugwarriorrc if it exists
        """
        rc = self.create('.bugwarriorrc')
        self.assertEqual(load.get_config_path(), rc)

    def test_xdg_first(self):
        """
        If both files above exist, the one in $XDG_CONFIG_HOME takes precedence
        """
        self.create('.bugwarriorrc')
        rc = self.create('.config/bugwarrior/bugwarriorrc')
        self.assertEqual(load.get_config_path(), rc)

    def test_no_file(self):
        """
        If no bugwarriorrc exist anywhere, the path to the prefered one is
        returned.
        """
        self.assertEqual(
            load.get_config_path(),
            os.path.join(self.tempdir, '.config/bugwarrior/bugwarriorrc'))

    def test_BUGWARRIORRC(self):
        """
        If $BUGWARRIORRC is set, it takes precedence over everything else (even
        if the file doesn't exist).
        """
        rc = os.path.join(self.tempdir, 'my-bugwarriorc')
        os.environ['BUGWARRIORRC'] = rc
        self.create('.bugwarriorrc')
        self.create('.config/bugwarrior/bugwarriorrc')
        self.assertEqual(load.get_config_path(), rc)

    def test_BUGWARRIORRC_empty(self):
        """
        If $BUGWARRIORRC is set but empty, it is not used and the default file
        is used instead.
        """
        os.environ['BUGWARRIORRC'] = ''
        rc = self.create('.config/bugwarrior/bugwarriorrc')
        self.assertEqual(load.get_config_path(), rc)


class TestBugwarriorConfigParser(TestCase):
    def setUp(self):
        self.config = load.BugwarriorConfigParser()
        self.config['general'] = {
            'someint': '4',
            'somenone': '',
            'somechar': 'somestring',
        }

    def test_getint(self):
        self.assertEqual(self.config.getint('general', 'someint'), 4)

    def test_getint_none(self):
        self.assertEqual(self.config.getint('general', 'somenone'), None)

    def test_getint_valueerror(self):
        with self.assertRaises(ValueError):
            self.config.getint('general', 'somechar')


class TestParseFile(LoadTest):
    def test_ini(self):
        config_path = self.create('.bugwarriorrc')
        with open(config_path, 'w') as fout:
            fout.write(textwrap.dedent("""
                [general]
                foo = bar
            """))
        config = load.parse_file(config_path)

        self.assertEqual(config, {'general': {'foo': 'bar'}})

    def test_ini_invalid(self):
        config_path = self.create('.bugwarriorrc')
        with open(config_path, 'w') as fout:
            fout.write(textwrap.dedent("""
                [general
                foo = bar
            """))

        with self.assertRaises(configparser.MissingSectionHeaderError):
            load.parse_file(config_path)

    def test_ini_prefix_removal(self):
        config_path = self.create('.bugwarriorrc')
        with open(config_path, 'w') as fout:
            fout.write(textwrap.dedent("""
                [general]
                foo = bar
                [baz]
                service = qux
                qux.optionname
            """))
        config = load.parse_file(config_path)

        self.assertIn('optionname', config['baz'])
        self.assertNotIn('prefix.optionname', config['baz'])

    def test_ini_missing_prefix(self):
        config_path = self.create('.bugwarriorrc')
        with open(config_path, 'w') as fout:
            fout.write(textwrap.dedent("""
                [general]
                foo = bar
                [baz]
                service = qux
                optionname
            """))

        with self.assertRaises(SystemExit):
            load.parse_file(config_path)

    def test_ini_wrong_prefix(self):
        config_path = self.create('.bugwarriorrc')
        with open(config_path, 'w') as fout:
            fout.write(textwrap.dedent("""
                [general]
                foo = bar
                [baz]
                service = qux
                wrong.optionname
            """))

        with self.assertRaises(SystemExit):
            load.parse_file(config_path)
