from typing import Optional

from flask import request
from pylon.core.tools import log

from tools import api_tools, auth, serialize, VaultClient


def get_project_integrations_api(self, project_id: int, name: Optional[str] = None, section: Optional[str] = None,
                                 unsecret: bool = False):
    if name:
        resp = [
            serialize(i) for i in self.get_all_integrations_by_name(project_id, name)
        ]
    elif section:
        resp = [
            serialize(i) for i in self.get_all_integrations_by_section(project_id, section)
        ]
    else:
        resp = [
            serialize(i) for i in self.get_all_integrations(project_id, False)
        ]
    if unsecret:
        VaultClient(project_id).unsecret(resp)
    return resp



class ProjectAPI(api_tools.APIModeHandler):
    @auth.decorators.check_api({
        "permissions": ["configuration.integrations.integrations.view"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": True, "editor": True},
            "default": {"admin": True, "viewer": True, "editor": True},
            "developer": {"admin": True, "viewer": False, "editor": False},
        }})
    def get(self, project_id: int):
        resp = get_project_integrations_api(
            self=self.module,
            project_id=project_id,
            name=request.args.get('name'),
            section=request.args.get('section'),
            unsecret=bool(request.args.get('unsecret', False))
        )
        return resp, 200


class AdminAPI(api_tools.APIModeHandler):
    @auth.decorators.check_api({
        "permissions": ["configuration.integrations.integrations.view"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": True, "editor": True},
            "default": {"admin": True, "viewer": True, "editor": True},
            "developer": {"admin": True, "viewer": False, "editor": False},
        }})
    def get(self, **kwargs):
        if request.args.get('name'):
            return [
                serialize(i) for i in self.module.get_administration_integrations_by_name(request.args['name'])
            ], 200
        if request.args.get('section'):
            return [
                serialize(i) for i in self.module.get_administration_integrations_by_section(request.args['section'])
            ], 200
        return [
            serialize(i) for i in self.module.get_administration_integrations(False)
        ], 200


class PromptLibAPI(api_tools.APIModeHandler):
    AI_SECTION: str = 'ai'

    @auth.decorators.check_api({
        "permissions": ["configuration.integrations.integrations.view"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": True, "editor": True},
            "default": {"admin": True, "viewer": True, "editor": True},
            "developer": {"admin": True, "viewer": False, "editor": False},
        }})
    def get(self, project_id: int):
        sort_order = request.args.get('sort_order', 'asc')
        sort_by = request.args.get('sort_by', 'name')
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 10_000))
        return [
            serialize(i) for i in self.module.get_sorted_paginated_integrations_by_section(
                self.AI_SECTION, project_id, sort_order, sort_by, offset, limit
            )
        ], 200


class API(api_tools.APIBase):
    url_params = [
        '<int:project_id>',
        '<string:mode>/<int:project_id>',
        '<string:project_id>',
        '<string:mode>/<string:project_id>'
    ]

    mode_handlers = {
        'default': ProjectAPI,
        'administration': AdminAPI,
        'prompt_lib': PromptLibAPI,
    }
