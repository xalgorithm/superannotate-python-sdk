import logging

import src.lib.core as constances
from src.lib.infrastructure.controller import Controller
from src.lib.infrastructure.repositories import ConfigRepository
from src.lib.infrastructure.services import SuperannotateBackendService


logger = logging.getLogger()


class BaseInterfaceFacade:
    @property
    def controller(self):
        if not ConfigRepository().get_one("token"):
            raise Exception("Config does not exsits!")
        return Controller(
            backend_client=SuperannotateBackendService(
                api_url=constances.BACKEND_URL,
                auth_token=ConfigRepository().get_one("token"),
                logger=logger,
            ),
        )
