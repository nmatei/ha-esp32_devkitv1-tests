"""Base entity: every entity of an entry sits on one device."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .controller import AlfabetController


class AlfabetEntity(Entity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, controller: AlfabetController, key: str, name: str) -> None:
        self.controller = controller
        entry = controller.entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        # Romanian names on purpose: they make the entity ids used by the card
        # (text.esp32_devkitv1_mesaj, …), whatever language HA runs in.
        self._attr_name = name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Alfabetul pe fire",
            model="5 fire",
        )
