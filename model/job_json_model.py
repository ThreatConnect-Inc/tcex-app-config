"""TcEx Framework Module"""

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel
from semantic_version import Version

__all__ = ['JobJsonModel']


class ParamsModel(BaseModel):
    """Model definition for job.json.params"""

    model_config = ConfigDict(alias_generator=to_camel, validate_assignment=True)

    default: bool | str | None = None
    encrypt: bool = False
    name: str
    prevent_updates: bool = False


class JobJsonCommonModel(BaseModel):
    """Model definition for common field in job.json."""

    model_config = ConfigDict(
        alias_generator=to_camel, arbitrary_types_allowed=True, validate_assignment=True
    )

    allow_on_demand: bool = Field(
        ...,
        description='If true, the job can be run on demand.',
    )
    enable_notifications: bool = Field(
        ..., description='Enables pass/fail notification for this job.'
    )
    job_name: str
    notify_email: str = Field(
        ...,
        description='Email address to send notification to.',
    )
    notify_include_log_files: bool = Field(
        ...,
        description='If true, the job log files will be included in the notification email.',
    )
    notify_on_complete: bool = Field(
        ...,
        description='If true, a notification will be sent when the job completes.',
    )
    notify_on_failure: bool = Field(
        ...,
        description='If true, a notification will be sent when the job fails.',
    )
    notify_on_partial_failure: bool = Field(
        ...,
        description=(
            'If true, a notification will be sent when the job completes with partial success.'
        ),
    )
    params: list[ParamsModel]
    publish_auth: bool = Field(
        ...,
        description='If true, the job will publish the authentication token.',
    )
    schedule_cron_format: str
    schedule_start_date: int
    schedule_type: str


class JobJsonModel(JobJsonCommonModel):
    """Model definition for job.json configuration file"""

    model_config = ConfigDict(
        alias_generator=to_camel, arbitrary_types_allowed=True, validate_assignment=True
    )

    program_name: str
    program_version: str

    @field_validator('program_version')
    @classmethod
    def version(cls, v):
        """Return a version object for "version" fields."""
        if v is not None:
            return Version(v)
        return v  # pragma: no cover
