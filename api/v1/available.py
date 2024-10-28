from flask import request

from tools import auth, api_tools


class ProjectAPI(api_tools.APIModeHandler):
    ...


class AdminAPI(api_tools.APIModeHandler):
    ...


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

    def get(self, **kwargs):
        section_filter = request.args.get('section')
        result = []
        if section_filter:
            for s in section_filter.split(','):
                result.extend(self.module.list_integrations_by_section(s.strip()))
            return result, 200
        return list(self.module.list_integrations()), 200
