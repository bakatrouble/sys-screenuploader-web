from .telegram import DestinationModuleConfigTelegram
from .discord import DestinationModuleConfigDiscord
from .group import DestinationModuleConfigGroup

DESTINATION_MODULES = [DestinationModuleConfigTelegram, DestinationModuleConfigDiscord,
                       DestinationModuleConfigGroup]
