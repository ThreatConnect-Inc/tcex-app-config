"""Class for tcex.json configuration file"""
# standard library
import json
import logging
from collections import OrderedDict
from functools import cached_property
from pathlib import Path

from .install_json import InstallJson
from .model.tcex_json_model import TcexJsonModel
from .tcex_json_update import TcexJsonUpdate

# get tcex logger
_logger = logging.getLogger(__name__.split('.', maxsplit=1)[0])


class TcexJson:
    """Class for tcex.json configuration file"""

    def __init__(
        self,
        filename: str | None = None,
        path: Path | str | None = None,
        logger: logging.Logger | None = None,
    ):
        """Initialize class properties."""
        filename = filename or 'tcex.json'
        path = Path(path or Path.cwd())
        self.log = logger or _logger

        # properties
        self.fqfn = path / filename
        self.ij = InstallJson(logger=self.log)

    @cached_property
    def contents(self) -> dict:
        """Return tcex.json file contents."""
        _contents = {}

        if self.fqfn.is_file():
            try:
                with self.fqfn.open() as fh:
                    _contents = json.load(fh, object_pairs_hook=OrderedDict)
            except OSError:  # pragma: no cover
                self.log.error(
                    f'feature=tcex-json, exception=failed-reading-file, filename={self.fqfn}'
                )
        else:  # pragma: no cover
            self.log.error(f'feature=tcex-json, exception=file-not-found, filename={self.fqfn}')

        return _contents

    @cached_property
    def model(self) -> TcexJsonModel:
        """Return the Install JSON model."""
        return TcexJsonModel(**self.contents)

    def print_warnings(self):
        """Print warning messages for tcex.json file."""

        # raise error if tcex.json is missing app_name field
        if self.model.package.app_name is None:  # pragma: no cover
            raise RuntimeError('The tcex.json file is missing the package.app_name field.')

        # log warning for old Apps
        if self.model.package.app_version is not None:
            print(
                'WARNING: The tcex.json file defines "app_version" which should only be '
                'defined in legacy Apps. Removing the value can cause the App to be treated '
                'as a new App by TcExchange. Please remove "app_version" when appropriate.'
            )

    @property
    def update(self) -> TcexJsonUpdate:
        """Return InstallJsonUpdate instance."""
        return TcexJsonUpdate(tj=self)

    def write(self):
        """Write current data file."""
        data = self.model.json(exclude_defaults=True, exclude_none=True, indent=2, sort_keys=True)
        with self.fqfn.open(mode='w') as fh:
            fh.write(f'{data}\n')
