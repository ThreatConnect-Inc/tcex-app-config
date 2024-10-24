"""TcEx Framework Module"""

# standard library
import json
import logging
from collections import OrderedDict
from functools import cached_property
from pathlib import Path

from ...pleb.singleton import Singleton
from .model.job_json_model import JobJsonModel

# get logger
_logger = logging.getLogger(__name__.split('.', maxsplit=1)[0])


class JobJson(metaclass=Singleton):
    """Config object for job.json file"""

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

    @cached_property
    def contents(self) -> dict:
        """Return job.json file contents."""
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
    def model(self) -> JobJsonModel:
        """Return the Install JSON model."""
        return JobJsonModel(**self.contents)
