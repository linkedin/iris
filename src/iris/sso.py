import logging
import importlib

logger = logging.getLogger(__name__)


class SSOManager:

    def __init__(self, config):
        sso_cfg = config.get('sso', {})
        if not sso_cfg.get('enabled', False):
            logger.info('SSO passthrough enabled')
            self.authenticate = self.passthrough
            return

        if sso_cfg.get('debug', False):
            logger.info('SSO debug mode enabled')
            self.authenticate = self.debug_authenticate
            return
        logger.info('SSO authentication enabled, using module %s', sso_cfg['sso_module'])
        sso_auth = importlib.import_module(sso_cfg['sso_module'])
        sso_auth_manager = getattr(sso_auth, 'Authenticator')(config)
        self.authenticate = sso_auth_manager.authenticate

    def passthrough(self, request):
        """Ignore SSO and defer to legacy authentication"""
        return None

    def debug_authenticate(self, request):
        """Authenticate using debug credentials taken from header"""
        # DUMMY SSO AUTHENTICATION FOR TEST USE ONLY, DO NOT USE IN PRODUCTION! Replace with your own SSO authentication module.
        if 'SSO-DEBUG-HEADER' in request.headers:
            return request.headers.get('SSO-DEBUG-HEADER')
        return None
