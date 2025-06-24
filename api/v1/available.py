from flask import request

from tools import api_tools


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
        if section_filter is None:
            sections = [None,]
        else:
            sections = [s.strip() for s in section_filter.split(',')]
        as_schema = bool(request.args.get('as_schema', 0, type=int))

        result = []
        for s in sections:
            if not as_schema:
                result.extend(self.module.list_integrations_by_section(s))
            else:
                result.extend(self.module.list_integrations_settings_by_section(s))
        return result, 200
