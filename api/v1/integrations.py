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
    
    # Mark default models for AI section
    if section == 'ai':
        _mark_default_models_in_serialized_data(resp, project_id)
    
    return resp


def _mark_default_models_in_serialized_data(integrations: list, project_id: int):
    """
    Mark default models in serialized integration data based on project secret 'default_model'.
    If no secret is found, mark the first chat model as default.
    Ensures at least one chat model is marked as default across all integrations.
    """
    # Parse default_model secret once
    target_integration_id = None
    target_model_id = None
    
    try:
        # Get the default_model secret from vault
        vault_client = VaultClient(project_id)
        secrets = vault_client.get_all_secrets()
        default_model_secret = secrets.get('default_model')
        
        # Parse the secret format: integration_id___model_id
        if default_model_secret and '___' in default_model_secret:
            parts = default_model_secret.split('___', 1)
            if len(parts) == 2:
                target_integration_id = int(parts[0])
                target_model_id = parts[1]
    except Exception as e:
        log.debug(f'Could not retrieve or parse default_model secret for project {project_id}: {e}')
    
    # Track if we've set any default model from secret
    secret_default_set = False
    
    for integration in integrations:
        if not (integration.get('settings') and integration['settings'].get('models')):
            continue
            
        models = integration['settings']['models']
        if not models:
            continue
        
        # Initialize all models with default=False
        for model in models:
            model['default'] = False
        
        default_model_set = False
        
        # If we have a target integration and model, try to match it
        if target_integration_id == integration.get('id') and target_model_id:
            # Find and mark the matching model as default
            for model in models:
                if model.get('id') == target_model_id:
                    model['default'] = True
                    default_model_set = True
                    secret_default_set = True
                    break
        
        # If no default was set from secret, mark first chat model as default
        if not default_model_set:
            for model in models:
                if model.get('capabilities', {}).get('chat_completion', False):
                    model['default'] = True
                    break
    
    # Ensure at least one chat model is marked as default across all integrations
    if not secret_default_set:
        # Check if any chat model is already marked as default
        has_default = False
        for integration in integrations:
            if not (integration.get('settings') and integration['settings'].get('models')):
                continue
                
            models = integration['settings']['models']
            for model in models:
                if (model.get('capabilities', {}).get('chat_completion', False) and
                    model.get('default', False)):
                    has_default = True
                    break
            if has_default:
                break
        
        # No default chat model found, set the first chat model we find as default
        if not has_default:
            for integration in integrations:
                if not (integration.get('settings') and integration['settings'].get('models')):
                    continue
                    
                models = integration['settings']['models']
                for model in models:
                    if model.get('capabilities', {}).get('chat_completion', False):
                        model['default'] = True
                        return



class ProjectAPI(api_tools.APIModeHandler):
    @auth.decorators.check_api({
        "permissions": ["configuration.integrations.integrations.view"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": True, "editor": True},
            "default": {"admin": True, "viewer": True, "editor": True},
            "developer": {"admin": True, "viewer": False, "editor": False},
        }})
    def get(self, project_id: int):
        ret = resp = get_project_integrations_api(
            self=self.module,
            project_id=project_id,
            name=request.args.get('name'),
            section=request.args.get('section'),
            unsecret=bool(request.args.get('unsecret', False))
        )
        if query := request.args.get('query'):
            ret = []
            for integration in resp:
                names = {
                    integration.get('name') or '',
                    integration.get('settings', {}).get('title') or '',
                    integration.get('config', {}).get('name') or ''
                }
                if any(query in name for name in names):
                    ret.append(integration)

        return ret, 200


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
        
        integrations = self.module.get_sorted_paginated_integrations_by_section(
            self.AI_SECTION, project_id, sort_order, sort_by, offset, limit
        )
        
        # Serialize integrations
        serialized_integrations = [serialize(i) for i in integrations]
        
        # Mark default models in serialized data
        _mark_default_models_in_serialized_data(serialized_integrations, project_id)
        
        return serialized_integrations, 200


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
