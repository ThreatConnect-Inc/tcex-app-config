"""TcEx Framework Module"""

# standard library
from collections import OrderedDict

# third-party
from pydantic import BaseModel, Field
from pydantic.types import constr

from ....pleb.none_model import NoneModel

__all__ = ['LayoutJsonModel']


def snake_to_camel(snake_string: str) -> str:
    """Convert snake_case to camelCase"""
    components = snake_string.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


class ParametersModel(BaseModel):
    """Model definition for layout_json.inputs.{}"""

    display: str | None
    name: str

    class Config:
        """DataModel Config"""

        alias_generator = snake_to_camel
        validate_assignment = True


class InputsModel(BaseModel):
    """Model definition for layout_json.inputs"""

    parameters: list[ParametersModel]
    sequence: int
    title: constr(min_length=3, max_length=100)  # type: ignore

    class Config:
        """DataModel Config"""

        alias_generator = snake_to_camel
        validate_assignment = True


class OutputsModel(BaseModel):
    """Model definition for layout_json.outputs"""

    display: str | None
    name: str

    class Config:
        """DataModel Config"""

        alias_generator = snake_to_camel
        validate_assignment = True


class LayoutJsonModel(BaseModel):
    """Model definition for layout.json configuration file"""

    inputs: list[InputsModel]
    outputs: list[OutputsModel] = Field([], description='Layout output variable definitions.')

    class Config:
        """DataModel Config"""

        alias_generator = snake_to_camel
        validate_assignment = True

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


OutputsModel.update_forward_refs()
