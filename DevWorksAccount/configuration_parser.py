import json
import logging
import os

import yaml

log = logging.getLogger(__name__)


class Configs:
    """
    All gets (str, bool, etc), name is case specific
    first we check the overrides then the environment.
    If neither exist we return None
    """

    def __init__(self, override_file=None):
        self.overrides = {}
        if override_file:
            self._read_overrides(override_file)

    def _read_overrides(self, override_file):
        try:
            with open(override_file, 'r') as stream:
                self.overrides = yaml.safe_load(stream)
        except FileNotFoundError:
            print("NOTICE: No override_file found will only use environment variables")
            log.info("No override_file found will only use environment variables")

    def str(self, name):
        """
        Check the config file first if none, then, os.env value
        """
        value = None
        try:
            return "{}".format(self.overrides[name])
        except KeyError:
            try:
                return os.environ[name]
            except KeyError:
                pass
        return value

    def num(self, name):
        value = self.str(name)
        if value.isnumeric():
            try:
                return int(value, 10)
            except ValueError:
                try:
                    return float(value)
                except Exception:
                    log.warning("Value {} should be numeric but got non number".format(name))
        return None

    def bool(self, name):
        value = None
        try:
            value = self.overrides[name]
        except KeyError:
            try:
                value = os.environ[name]
            except KeyError:
                pass
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() == 'true'
        return None

    def json(self, name, default=None):
        value = None
        try:
            value = self.overrides[name]
        except KeyError:
            pass
        try:
            value = json.loads(os.environ[name])
        except Exception as exc:
            log.debug("failed json load: {}".format(str(exc)))
        if value is None and default is not None:
            return default
        return value

    def json_file(self, name, base_dir):
        base_dir = base_dir if base_dir else '.'
        filename = self.str(name)
        if not filename:
            log.warning("Could not open {} ({}) got no config value".format(name, str(filename)))
            return None
        filepath = os.path.join(base_dir, filename)
        try:
            with open(filepath, 'rb') as fh:
                try:
                    data = json.load(fh)
                except TypeError as exc:
                    log.warning("Could not open {} got '{}'".format(name, str(exc)))
                    return None
                return data
        except IOError as exc:
            log.warning("Could not open {} got '{}'".format(name, str(exc)))
            return None
