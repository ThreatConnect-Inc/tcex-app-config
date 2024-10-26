"""TcEx Framework Module"""

# standard library
import json
import logging
import os
from functools import cached_property
from pathlib import Path

# third-party
import yaml

try:
    # third-party
    from yaml import CDumper as Dumper
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Dumper, Loader

from .install_json import InstallJson
from .model.app_spec_yml_model import AppSpecYmlModel
from .tcex_json import TcexJson

# get logger
_logger = logging.getLogger(__name__.split('.', maxsplit=1)[0])


class AppSpecYml:
    """Class object for app_spec.yml configuration file"""

    def __init__(
        self,
        filename: str | None = None,
        path: str | None = None,
        logger: logging.Logger | None = None,
    ):
        """Initialize instance properties."""
        filename = filename or 'app_spec.yml'
        path = path or os.getcwd()
        self.log = logger or _logger

        # properties
        self.fqfn = Path(os.path.join(path, filename))
        self.ij = InstallJson(logger=self.log)
        self.tj = TcexJson(logger=self.log)

    @property
    def _feature_data_advanced_request_inputs(self):
        """Return all inputs for advanced request."""
        return [
            {
                'display': '''tc_action in ('Advanced Request')''',
                'label': 'API Endpoint/Path',
                'name': 'tc_adv_req_path',
                'note': 'The API Path request.',
                'playbookDataType': ['String'],
                'required': True,
                'type': 'String',
                'validValues': ['${TEXT}'],
            },
            {
                'display': '''tc_action in ('Advanced Request')''',
                'default': 'GET',
                'label': 'HTTP Method',
                'name': 'tc_adv_req_http_method',
                'note': 'HTTP method to use.',
                'required': True,
                'type': 'Choice',
                'validValues': ['GET', 'POST', 'DELETE', 'PUT', 'HEAD', 'PATCH', 'OPTIONS'],
            },
            {
                'display': '''tc_action in ('Advanced Request')''',
                'label': 'Query Parameters',
                'name': 'tc_adv_req_params',
                'note': (
                    'Query parameters to append to the URL. For sensitive information like API '
                    'keys, using variables is recommended to ensure that the Playbook will not '
                    'export sensitive data.'
                ),
                'playbookDataType': ['String', 'StringArray'],
                'required': False,
                'type': 'KeyValueList',
                'validValues': ['${KEYCHAIN}', '${TEXT}'],
            },
            {
                'display': '''tc_action in ('Advanced Request')''',
                'label': 'Exclude Empty/Null Parameters',
                'name': 'tc_adv_req_exclude_null_params',
                'note': (
                    '''Some API endpoint don't handle null/empty query parameters properly '''
                    '''(e.g., ?name=&type=String). If selected this options will exclude any '''
                    '''query parameters that has a null/empty value.'''
                ),
                'type': 'Boolean',
            },
            {
                'display': '''tc_action in ('Advanced Request')''',
                'label': 'Headers',
                'name': 'tc_adv_req_headers',
                'note': (
                    'Headers to include in the request. When using Multi-part Form/File data, '
                    'do **not** add a **Content-Type** header. For sensitive information like '
                    'API keys, using variables is recommended to ensure that the Playbook will '
                    'not export sensitive data.'
                ),
                'playbookDataType': ['String'],
                'required': False,
                'type': 'KeyValueList',
                'validValues': ['${KEYCHAIN}', '${TEXT}'],
            },
            {
                'display': (
                    '''tc_action in ('Advanced Request') AND tc_adv_req_http_method '''
                    '''in ('POST', 'PUT', 'DELETE', 'PATCH')'''
                ),
                'label': 'Body',
                'name': 'tc_adv_req_body',
                'note': 'Content of the HTTP request.',
                'playbookDataType': ['String', 'Binary'],
                'required': False,
                'type': 'String',
                'validValues': ['${KEYCHAIN}', '${TEXT}'],
                'viewRows': 4,
            },
            {
                'display': (
                    '''tc_action in ('Advanced Request') AND tc_adv_req_http_method '''
                    '''in ('POST', 'PUT', 'DELETE', 'PATCH')'''
                ),
                'label': 'URL Encode JSON Body',
                'name': 'tc_adv_req_urlencode_body',
                'note': (
                    '''URL encode a JSON-formatted body. Typically used for'''
                    ''' 'x-www-form-urlencoded' data, where the data can be configured in the '''
                    '''body as a JSON string.'''
                ),
                'type': 'Boolean',
            },
            {
                'display': '''tc_action in ('Advanced Request')''',
                'default': True,
                'label': 'Fail for Status',
                'name': 'tc_adv_req_fail_on_error',
                'note': 'Fail if the response status code is 4XX - 5XX.',
                'type': 'Boolean',
            },
        ]

    @staticmethod
    def _feature_data_advanced_request_outputs(prefix: str) -> dict:
        """Return all outputs for advanced request."""
        return {
            'display': 'tc_action in (\'Advanced Request\')',
            'outputVariables': [
                {
                    'name': f'{prefix}.request.content',
                },
                {
                    'name': f'{prefix}.request.content.binary',
                    'type': 'Binary',
                },
                {
                    'name': f'{prefix}.request.headers',
                },
                {
                    'name': f'{prefix}.request.ok',
                },
                {
                    'name': f'{prefix}.request.reason',
                },
                {
                    'name': f'{prefix}.request.status_code',
                },
                {
                    'name': f'{prefix}.request.url',
                },
            ],
        }

    def _migrate_schema_100_to_110(self, contents: dict):
        """Migrate 1.0.0 schema to 1.1.0 schema."""
        # moved app.* to top level
        self._migrate_schema_100_to_110_app(contents)

        # migrate app.feeds to app.organization.feeds
        self._migrate_schema_100_to_110_organization_feeds(contents)

        # migrate app.feeds to app.organization.repeating_minutes
        self._migrate_schema_100_to_110_organization_repeating_minutes(contents)

        # migrate app.feeds to app.organization.publish_out_files
        self._migrate_schema_100_to_110_organization_publish_out_files(contents)

        # migrate app.inputGroup to new schema
        self._migrate_schema_100_to_110_input_groups(contents)

        # migrate app.note to app.notePerAction with new schema
        self._migrate_schema_100_to_110_notes_per_action(contents)

        # migrate app.outputGroups to outputData with new schema
        self._migrate_schema_100_to_110_output_groups(contents)

        # migrate app.playbookType to category
        contents['category'] = contents.pop('playbookType', '')

        # migrate app.jira to internalNotes schema
        self._migrate_schema_100_to_110_jira_notes(contents)

        # migrate app.releaseNotes to new schema
        self._migrate_schema_100_to_110_release_notes(contents)

        # migrate app.retry to playbook.retry
        self._migrate_schema_100_to_110_retry(contents)

        # update the schema version
        contents['schemaVersion'] = contents.get('schemaVersion') or '1.1.0'

    @staticmethod
    def _migrate_schema_100_to_110_app(contents: dict):
        """Migrate 1.0.0 schema to 1.1.0 schema."""
        # remove "app" top level
        for k, v in dict(contents).get('app', {}).items():
            contents[k] = v

        # assure minServerVersion exists
        if contents.get('minServerVersion') is None:
            contents['minServerVersion'] = '6.0.0'

        # remove "app" from "app_spec"
        del contents['app']

    @staticmethod
    def _migrate_schema_100_to_110_organization_feeds(contents: dict):
        """Migrate 1.0.0 schema to 1.1.0 schema."""
        if contents.get('feeds') is not None and contents['runtimeLevel'].lower() == 'organization':
            contents.setdefault('organization', {})
            contents['organization']['feeds'] = contents.pop('feeds', [])

    @staticmethod
    def _migrate_schema_100_to_110_organization_repeating_minutes(contents: dict):
        """Migrate 1.0.0 schema to 1.1.0 schema."""
        if (
            contents.get('repeatingMinutes') is not None
            and contents['runtimeLevel'].lower() == 'organization'
        ):
            contents.setdefault('organization', {})
            contents['organization']['repeatingMinutes'] = contents.pop('repeatingMinutes', [])

    @staticmethod
    def _migrate_schema_100_to_110_organization_publish_out_files(contents: dict):
        """Migrate 1.0.0 schema to 1.1.0 schema."""
        if (
            contents.get('publishOutFiles') is not None
            and contents['runtimeLevel'].lower() == 'organization'
        ):
            contents.setdefault('organization', {})
            contents['organization']['publishOutFiles'] = contents.pop('publishOutFiles', [])

    @staticmethod
    def _migrate_schema_100_to_110_input_groups(contents: dict):
        """Migrate 1.0.0 schema to 1.1.0 schema."""
        contents['sections'] = contents.pop('inputGroups', {})
        for section in contents.get('sections') or []:
            section['sectionName'] = section.pop('group')
            section['params'] = section.pop('inputs')

            # add missing name
            for param in section['params']:
                if param.get('name') is None:
                    param['name'] = param.get('label')

                if 'sequence' in param:
                    del param['sequence']

                if param.get('type') is None:
                    param['type'] = 'String'

    @staticmethod
    def _migrate_schema_100_to_110_notes_per_action(contents: dict):
        """Migrate 1.0.0 schema to 1.1.0 schema."""
        contents['notePerAction'] = contents.pop('notes', {})
        note_per_action = []
        for action, note in contents['notePerAction'].items():
            note_per_action.append({'action': action, 'note': note})
        contents['notePerAction'] = note_per_action

    @staticmethod
    def _migrate_schema_100_to_110_retry(contents: dict):
        """Migrate 1.0.0 schema to 1.1.0 schema."""
        if contents['runtimeLevel'].lower() == 'playbook':
            contents.setdefault('playbook', {})
            if contents.get('playbook', {}).get('retry'):
                contents['playbook']['retry'] = contents.pop('retry', {})

    @staticmethod
    def _migrate_schema_100_to_110_output_groups(contents: dict):
        """Migrate 1.0.0 schema to 1.1.0 schema."""
        outputs = []
        contents['outputData'] = contents.pop('outputGroups', {})
        for display, group in contents.get('outputData', {}).items():
            output_data = {'display': display, 'outputVariables': []}

            # fix schema when output type is assumed
            if isinstance(group, list):
                group = {'String': group}

            for variable_type, variables in group.items():
                for name in variables:
                    disabled = False
                    if name.startswith('~'):
                        name = name.replace('~', '')
                        disabled = True

                    output_data['outputVariables'].append(
                        {
                            'disabled': disabled,
                            'encrypt': False,
                            'intelTypes': [],
                            'name': name,
                            'note': None,
                            'type': variable_type,
                        }
                    )
            outputs.append(output_data)
        contents['outputData'] = outputs

    @staticmethod
    def _migrate_schema_100_to_110_jira_notes(contents: dict):
        """Migrate 1.0.0 schema to 1.1.0 schema."""
        jira_notes = []
        for k, v in contents.get('jira', {}).items():
            # look for the trailer to find our items
            if k == '_TRAILER_':
                for item in v:
                    jira_notes.append(item)
        contents['internalNotes'] = jira_notes

    @staticmethod
    def _migrate_schema_100_to_110_release_notes(contents: dict):
        """Migrate 1.0.0 schema to 1.1.0 schema."""
        release_notes = []
        # need to see if this exist, older apps it might not
        if contents.get('releaseNotes'):
            for k, v in contents.get('releaseNotes', {}).items():
                release_notes.append({'version': k, 'notes': v})
        contents['releaseNotes'] = release_notes

    @cached_property
    def contents(self) -> dict:
        """Return install.json file contents."""

        def _load_contents() -> dict:
            """Load contents from file."""
            contents = {}
            if self.fqfn.is_file():
                try:
                    with self.fqfn.open(encoding='utf-8') as fh:
                        contents = yaml.load(fh, Loader=Loader)  # nosec
                except (OSError, ValueError):  # pragma: no cover
                    self.log.error(
                        f'feature=app-spec-yml, exception=failed-reading-file, filename={self.fqfn}'
                    )
            else:  # pragma: no cover
                self.log.error(
                    f'feature=app-spec-yml, exception=file-not-found, filename={self.fqfn}'
                )

            return contents

        contents = _load_contents()

        # migrate schema from 1.0.0 to 1.1.0
        if contents.get('schemaVersion', '1.0.0') == '1.0.0':
            self._migrate_schema_100_to_110(contents)

        # reformat file
        self.rewrite_contents(contents)

        # migrate schema
        return _load_contents()

    @staticmethod
    def dict_to_yaml(data: dict) -> str:
        """Convert dict to yaml."""
        return yaml.dump(
            data,
            Dumper=Dumper,
            default_flow_style=False,
            sort_keys=False,
        )

    @property
    def has_spec(self):
        """Return True if App has app_spec.yml file."""
        return self.fqfn.is_file()

    @cached_property
    def model(self) -> AppSpecYmlModel:
        """Return the Install JSON model.

        If writing app_spec.yml file after the method then the model will include
        advancedRequest inputs/outputs, etc.
        """
        _contents = self.contents
        # special case for dynamic handling of advancedRequest feature
        if 'advancedRequest' in _contents.get('features', []):
            # look for a Configure section which required for Advanced Request
            if 'Configure' not in [
                section.get('sectionName') for section in _contents.get('sections', [])
            ]:
                raise RuntimeError('The advancedRequest feature requires a Configure section.')

            # Add "Advanced Request" action to Valid Values
            # when "advancedRequest" feature is enabled
            for section in _contents.get('sections', []):
                for param in section.get('params', []):
                    if param.get('name') == 'tc_action' and 'Advanced Request' not in param.get(
                        'validValues', []
                    ):
                        param['validValues'].append('Advanced Request')

                if section.get('sectionName') == 'Configure':
                    section['params'].extend(self._feature_data_advanced_request_inputs)

            # add outputs
            prefix = _contents.get('outputPrefix', '')
            _contents['outputData'].append(self._feature_data_advanced_request_outputs(prefix))

        return AppSpecYmlModel(**self.contents)

    def fix_contents(self, contents: dict):
        """Fix missing data"""
        # fix for null appId value
        if 'appId' in contents and contents.get('appId') is None:
            del contents['appId']

        # update features
        contents['features'] = AppSpecYmlModel(**contents).updated_features

        # fix missing packageName
        if contents.get('packageName') is None:
            contents['packageName'] = self.tj.model.package.app_name

        # fix programMain to always be run.py
        if contents.get('programMain') in [None, 'run']:
            contents['programMain'] = 'run.py'

        # fix missing outputPrefix
        if contents.get('outputPrefix') is None and 'advancedRequest' in contents.get(
            'features', []
        ):
            if self.ij.model.playbook is not None:
                contents['outputPrefix'] = self.ij.model.playbook.output_prefix

        # ensure displayPath is set for API Service Apps
        if contents.get('displayPath') is None and contents['runtimeLevel'].lower() in [
            'apiservice',
            'feedapiservice',
        ]:
            contents['displayPath'] = contents['displayName'].replace(' ', '-').lower()

    def rewrite_contents(self, contents: dict):
        """Rewrite app_spec.yml file."""
        self.fix_contents(contents)

        # exclude_defaults - if False then all unused fields are added in - not good.
        # exclude_none - this should be safe to leave as True.
        # exclude_unset - this should be False to ensure that all fields are included.
        contents = json.loads(
            AppSpecYmlModel(**contents).json(
                by_alias=True,
                exclude_defaults=True,
                exclude_none=True,
                exclude_unset=False,
                sort_keys=True,
            )
        )

        # write the new contents to the file
        self.write(contents)

        return contents

    def write(self, contents: dict):
        """Write yaml to file."""
        with self.fqfn.open(mode='w', encoding='utf-8') as fh:
            fh.write(self.dict_to_yaml(contents))
