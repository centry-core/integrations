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


class ModelsAPI(api_tools.APIModeHandler):
    AI_SECTION: str = 'ai'

    @auth.decorators.check_api({
        "permissions": ["configuration.integrations.integrations.view"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": True, "editor": True},
            "default": {"admin": True, "viewer": True, "editor": True},
            "developer": {"admin": True, "viewer": False, "editor": False},
        }})
    def get(self, project_id: int):
        sort_order, sort_field = 'asc', 'name'
        page, per_page = None, 10

        if request.args.get('sort_order'):
            sort_order = request.args.get('sort_order')
        if request.args.get('sort_field'):
            sort_field = request.args.get('sort_field')
        if request.args.get('page'):
            page = int(request.args.get('page'))
        if request.args.get('size'):
            per_page = int(request.args.get('size'))

        return [
            i.dict() for i in self.module.get_sorted_paginated_integrations_by_section(
                self.AI_SECTION, project_id, sort_order, sort_field, page, per_page
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
        'prompt_lib': ModelsAPI,
    }
