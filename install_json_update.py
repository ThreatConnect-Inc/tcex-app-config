"""TcEx Framework Module"""

# standard library
from importlib.metadata import version
from typing import TYPE_CHECKING

# third-party
from semantic_version import Version

if TYPE_CHECKING:
    from .install_json import InstallJson  # CIRCULAR-IMPORT


class InstallJsonUpdate:
    """Config object for install.json file (update)"""

    def __init__(self, ij: 'InstallJson'):  # pylint: disable=E0601
        """Initialize instance properties"""
        self.ij = ij

    def multiple(
        self,
        features: bool = True,
        sequence: bool = True,
        valid_values: bool = True,
        playbook_data_types: bool = True,
        sdk_version: bool = True,
    ):
        """Update the profile with all required changes.

        Args:
            features: If True, features will be updated.
            language_version: If True, the language version will be updated.
            migrate: If True, programMain will be set to "run".
            sequence: If True, sequence numbers will be updated.
            valid_values: If True, validValues will be updated.
            playbook_data_types:  If True, pbDataTypes will be updated.
            sdk_version: If True, the sdk version will be updated.
        """
        # update features array
        if features is True:
            self.ij.model.features = self.ij.model.updated_features

        # update sequence numbers
        if sequence is True:
            self.update_sequence_numbers()

        # update valid values
        if valid_values is True:
            self.update_valid_values()

        # update playbook data types
        if playbook_data_types is True:
            self.update_playbook_data_types()

        if sdk_version is True:
            # update language version to the current version of Python
            self.update_sdk_version()

        # write updated profile
        self.ij.write()

    def update_sequence_numbers(self):
        """Update program sequence numbers."""
        for sequence, param in enumerate(self.ij.model.params, start=1):
            param.sequence = sequence

    def update_valid_values(self):
        """Update program main on App type."""
        for param in self.ij.model.params:
            if param.type not in ['String', 'KeyValueList']:
                continue

            store = 'TEXT'
            if param.encrypt is True:
                store = 'KEYCHAIN'

            if self.ij.model.is_organization_app or param.service_config is True:
                if f'${{USER:{store}}}' not in param.valid_values:
                    param.valid_values.append(f'${{USER:{store}}}')

                if f'${{ORGANIZATION:{store}}}' not in param.valid_values:
                    param.valid_values.append(f'${{ORGANIZATION:{store}}}')

                # remove entry that's specifically for playbooks Apps
                if f'${{{store}}}' in param.valid_values:
                    param.valid_values.remove(f'${{{store}}}')

            elif self.ij.model.is_playbook_app:
                if f'${{{store}}}' not in param.valid_values:
                    param.valid_values.append(f'${{{store}}}')

                # remove entry that's specifically for organization (job) Apps
                if f'${{USER:{store}}}' in param.valid_values:
                    param.valid_values.remove(f'${{USER:{store}}}')

                # remove entry that's specifically for organization (job) Apps
                if f'${{ORGANIZATION:{store}}}' in param.valid_values:
                    param.valid_values.remove(f'${{ORGANIZATION:{store}}}')

    def update_playbook_data_types(self):
        """Update program main on App type."""
        if not self.ij.model.is_playbook_app:
            return

        for param in self.ij.model.params:
            if param.type != 'String':
                continue
            if not param.playbook_data_type:
                param.playbook_data_type.append('String')

    def update_sdk_version(self):
        """Update sdk version."""
        try:
            # best effort to get the version of the tcex package
            self.ij.model.sdk_version = Version(version('tcex'))
        except (ImportError, ValueError):
            pass
