from flask import request
from pylon.core.tools import log

from tools import api_tools, auth


class ProjectAPI(api_tools.APIModeHandler):
    @auth.decorators.check_api({
        "permissions": ["configuration.integrations.integrations.view"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": True, "editor": True},
            "default": {"admin": True, "viewer": True, "editor": True},
            "developer": {"admin": True, "viewer": False, "editor": False},
        }})
    def get(self, project_id: int):
        if request.args.get('name'):
            return [
                i.dict() for i in self.module.get_all_integrations_by_name(project_id, request.args['name'])
            ], 200
        if request.args.get('section'):
            return [
                i.dict() for i in self.module.get_all_integrations_by_section(project_id, request.args['section'])
            ], 200
        return [
            i.dict() for i in self.module.get_all_integrations(project_id, False)
        ], 200


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
                i.dict() for i in self.module.get_administration_integrations_by_name(request.args['name'])
            ], 200
        if request.args.get('section'):
            return [
                i.dict() for i in self.module.get_administration_integrations_by_section(request.args['section'])
            ], 200
        return [
            i.dict() for i in self.module.get_administration_integrations(False)
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
    }
