from typing import Optional, Union

from pydantic.v1.class_validators import validator
from pydantic.v1.main import ModelMetaclass
from pydantic.v1 import BaseModel, root_validator


def name_validator(cls, value: str):
    return value.lower()


class SectionRegistrationForm(BaseModel):
    name: str
    integration_description: Optional[str] = ''
    test_planner_description: Optional[str] = ''

    _lower_name = validator('name', allow_reuse=True)(name_validator)


class RegistrationForm(BaseModel):
    name: str
    section: str  # we manually manage relationships
    settings_model: Optional[ModelMetaclass]  # todo: replace for validation callback
    create_settings_model: Optional[ModelMetaclass]
    # integration_callback: Optional[Callable] = lambda context, slot, payload: None

    _lower_name = validator('name', allow_reuse=True)(name_validator)

    @validator('section')
    def section_validator(cls, value: Union[str, dict]):
        # section = rpc_tools.RpcMixin().rpc.call.integrations_get_section(value)
        from tools import integrations_tools
        section = integrations_tools.get_section(value)
        if not section:
            if isinstance(value, str):
                section = integrations_tools.register_section(name=value)
            else:
                section = integrations_tools.register_section(**value)

        return section.name

    @root_validator
    def create_settings_validator(cls, values):
        create_settings_model = values.get('create_settings_model')
        settings_model = values.get('settings_model')
        if create_settings_model is None and settings_model:
            values['create_settings_model'] = settings_model

        return values

    class Config:
        json_encoders = {
            ModelMetaclass: lambda v: str(type(v)),
        }
        arbitrary_types_allowed = True
