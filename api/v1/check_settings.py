from flask import request
from pydantic.v1 import ValidationError

from tools import auth, api_tools


class ProjectAPI(api_tools.APIModeHandler):
    ...


class AdminAPI(api_tools.APIModeHandler):
    ...


class API(api_tools.APIBase):
    url_params = [
        '<string:integration_name>',
        '<string:mode>/<string:integration_name>',
    ]

    mode_handlers = {
        'default': ProjectAPI,
        'administration': AdminAPI,
    }

    @auth.decorators.check_api(
        [
            "configuration.integrations.integrations.create",
            "configuration.integrations.integrations.edit"
        ],
        project_id_in_request_json=True
    )
    def post(self, integration_name: str, **kwargs):
        integration = self.module.get_by_name(integration_name)
        payload = request.json
        if not integration:
            return {'error': 'integration not found'}, 404
        try:
            settings = integration.settings_model.parse_obj(payload)
        except ValidationError as e:
            # return e.json(), 400
            return e.errors(), 400

        project_id = payload.get('project_id')
        project_id = int(project_id) if project_id else project_id
        check_connection_response = settings.check_connection(project_id)
        if not request.json.get('save_action'):
            if check_connection_response is True:
                return 'OK', 200
            return [{'loc': ['check_connection'], 'msg': check_connection_response}], 400
