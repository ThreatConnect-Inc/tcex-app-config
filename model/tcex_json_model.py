"""TcEx Framework Module"""

# standard library

# third-party
from pydantic import BaseModel, ConfigDict, field_validator

__all__ = ['TcexJsonModel']


class PackageModel(BaseModel):
    """Model definition for tcex_json.package"""

    model_config = ConfigDict(validate_assignment=True)

    app_name: str
    app_version: str | None = None
    excludes: list
    output_dir: str = 'target'

    @field_validator('excludes')
    @classmethod
    def sorted(cls, v) -> list:
        """Change value for excludes field."""
        # the requirements.txt file is required for App Builder
        v = [e for e in v if e != 'requirements.txt']
        return sorted(set(v))


class TcexJsonModel(BaseModel):
    """Model definition for tcex.json configuration file"""

    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)

    package: PackageModel
    template_name: str | None = None
    template_repo_hash: str | None = None
    template_type: str | None = None
