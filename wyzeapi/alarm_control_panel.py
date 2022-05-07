import logging
from datetime import timedelta

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    SUPPORT_ALARM_ARM_HOME,
    SUPPORT_ALARM_ARM_AWAY
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.core import HomeAssistant
from wyzeapy.client import Client
from wyzeapy.types import HMSStatus

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
ATTRIBUTION = "Data provided by Wyze"
SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    _LOGGER.debug("""Creating new WyzeApi Home Monitoring System component""")
    client: Client = hass.data[DOMAIN][config_entry.entry_id]

    def create_hms_if_exists():
        if client.has_hms():
            return WyzeHomeMonitoring(client)
        return None

    hms = await hass.async_add_executor_job(create_hms_if_exists)

    if hms is not None:
        async_add_entities([hms], True)


class WyzeHomeMonitoring(AlarmControlPanelEntity):
    DEVICE_MODEL = "HMS"
    NAME = "Wyze Home Monitoring System"
    AVAILABLE = True
    _state = "disarmed"
    _server_out_of_sync = False

    def __init__(self, client):
        self._client: Client = client
        self.hms_id = self._client.net_client.get_hms_id()

    @property
    def state(self):
        return self._state

    def alarm_disarm(self, code=None):
        self._client.set_hms_status(HMSStatus.DISARMED)
        self._state = "disarmed"
        self._server_out_of_sync = True

    def alarm_arm_home(self, code=None):
        self._client.set_hms_status(HMSStatus.HOME)
        self._state = "armed_home"
        self._server_out_of_sync = True

    def alarm_arm_away(self, code=None):
        self._client.set_hms_status(HMSStatus.AWAY)
        self._state = "armed_away"
        self._server_out_of_sync = True

    def alarm_arm_night(self, code=None):
        raise NotImplementedError

    def alarm_trigger(self, code=None):
        raise NotImplementedError

    def alarm_arm_custom_bypass(self, code=None):
        raise NotImplementedError

    @property
    def supported_features(self) -> int:
        return SUPPORT_ALARM_ARM_HOME | SUPPORT_ALARM_ARM_AWAY

    @property
    def device_info(self):
        return {
            "identifiers": {
                (DOMAIN, self.unique_id)
            },
            "name": self.NAME,
            "manufacturer": "WyzeLabs",
            "model": self.DEVICE_MODEL
        }

    @property
    def name(self) -> str:
        return self.NAME

    @property
    def unique_id(self):
        return f"{self.hms_id}-hms"

    @property
    def device_state_attributes(self):
        """Return device attributes of the entity."""
        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            "state": self.state,
            "available": self.AVAILABLE,
            "device model": self.DEVICE_MODEL,
            "mac": self.unique_id
        }

    def update(self):
        if not self._server_out_of_sync:
            state = self._client.get_hms_info()
            if state is HMSStatus.DISARMED:
                self._state = "disarmed"
            elif state is HMSStatus.AWAY:
                self._state = "armed_away"
            elif state is HMSStatus.HOME:
                self._state = "armed_home"
            else:
                _LOGGER.warning(f"Received {state} from server")

        self._server_out_of_sync = False
