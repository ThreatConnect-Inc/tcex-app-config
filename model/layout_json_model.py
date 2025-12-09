"""TcEx Framework Module"""

from collections import OrderedDict
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from pydantic.alias_generators import to_camel

from ....pleb.none_model import NoneModel

__all__ = ['LayoutJsonModel']


class ParametersModel(BaseModel):
    """Model definition for layout_json.inputs.{}"""

    model_config = ConfigDict(alias_generator=to_camel, validate_assignment=True)

    display: str | None = None
    name: str


class InputsModel(BaseModel):
    """Model definition for layout_json.inputs"""

    model_config = ConfigDict(alias_generator=to_camel, validate_assignment=True)

    parameters: list[ParametersModel]
    sequence: int
    title: Annotated[str, StringConstraints(min_length=3, max_length=100)]  # type: ignore


class OutputsModel(BaseModel):
    """Model definition for layout_json.outputs"""

    model_config = ConfigDict(alias_generator=to_camel, validate_assignment=True)

    display: str | None = None
    name: str


class LayoutJsonModel(BaseModel):
    """Model definition for layout.json configuration file"""

    model_config = ConfigDict(alias_generator=to_camel, validate_assignment=True)

    inputs: list[InputsModel]
    outputs: list[OutputsModel] = Field([], description='Layout output variable definitions.')

    def get_param(self, name: str) -> NoneModel | ParametersModel:
        """Return the param or a None Model."""
        return self.params.get(name) or NoneModel()

    def get_output(self, name: str) -> NoneModel | OutputsModel:
        """Return layout.json outputs in a flattened dict with name param as key."""
        return self.outputs_.get(name) or NoneModel()

    @property
    def outputs_(self) -> dict[str, OutputsModel]:
        """Return layout.json outputs in a flattened dict with name param as key."""
        return {o.name: o for o in self.outputs}

    @property
    def param_names(self) -> list:
        """Return all param names in a single list."""
        return list(self.params.keys())

    @property
    def params(self) -> dict[str, ParametersModel]:
        """Return layout.json params in a flattened dict with name param as key."""
        # return {p.name: p for i in self.inputs for p in i.parameters}

        # order is required for display clauses to be evaluated correctly
        parameters = OrderedDict()  # remove after python 3.7
        for i in self.inputs:
            for p in i.parameters:
                parameters.setdefault(p.name, p)
        return parameters


# OutputsModel.update_forward_refs()
