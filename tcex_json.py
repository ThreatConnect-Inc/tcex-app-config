"""TcEx Framework Module"""

# standard library
import json
import logging
from collections import OrderedDict
from functools import cached_property
from pathlib import Path

from .install_json import InstallJson
from .model.tcex_json_model import TcexJsonModel
from .tcex_json_update import TcexJsonUpdate

# get logger
_logger = logging.getLogger(__name__.split('.', maxsplit=1)[0])


class TcexJson:
    """Config object for tcex.json configuration file"""

    def __init__(
        self,
        filename: str | None = None,
        path: Path | str | None = None,
        logger: logging.Logger | None = None,
    ):
        """Initialize instance properties."""
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

    @property
    def update(self) -> TcexJsonUpdate:
        """Return InstallJsonUpdate instance."""
        return TcexJsonUpdate(tj=self)

    def write(self):
        """Write current data file."""
        data = self.model.json(exclude_defaults=True, exclude_none=True, indent=2, sort_keys=True)
        with self.fqfn.open(mode='w') as fh:
            fh.write(f'{data}\n')
