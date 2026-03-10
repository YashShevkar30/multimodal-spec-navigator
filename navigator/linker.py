"""
Links architectural diagrams, spec sections, and code references together.
Enables "find code for this diagram" functionality.
"""

from typing import List, Dict, Optional
import structlog
from dataclasses import dataclass

logger = structlog.get_logger()

@dataclass
class LinkedEntity:
    entity_id: str
    diagram_ids: List[str]
    section_ids: List[str]
    code_refs: List[str]


class ArchitectureLinker:
    """
    Maintains relationships between different modalities (images, specs, code).
    Used to enrich search results with related context.
    """
    
    def __init__(self):
        # Maps entity ID to its links
        self._links: Dict[str, LinkedEntity] = {}
        # Maps specific item IDs (e.g. diagram_1) to the entity ID
        self._item_to_entity: Dict[str, str] = {}

    def register_entity(self, entity_id: str):
        if entity_id not in self._links:
            self._links[entity_id] = LinkedEntity(entity_id, [], [], [])

    def link_diagram(self, entity_id: str, diagram_id: str):
        self.register_entity(entity_id)
        if diagram_id not in self._links[entity_id].diagram_ids:
            self._links[entity_id].diagram_ids.append(diagram_id)
        self._item_to_entity[diagram_id] = entity_id

    def link_section(self, entity_id: str, section_id: str):
        self.register_entity(entity_id)
        if section_id not in self._links[entity_id].section_ids:
            self._links[entity_id].section_ids.append(section_id)
        self._item_to_entity[section_id] = entity_id

    def link_code(self, entity_id: str, code_path: str):
        self.register_entity(entity_id)
        if code_path not in self._links[entity_id].code_refs:
            self._links[entity_id].code_refs.append(code_path)
        self._item_to_entity[code_path] = entity_id

    def get_related_items(self, item_id: str) -> Optional[LinkedEntity]:
        """Given a diagram, section, or code ID, return all related linked items."""
        entity_id = self._item_to_entity.get(item_id)
        if not entity_id:
            # Fallback: maybe the item_id IS the entity_id
            return self._links.get(item_id)
        return self._links.get(entity_id)

    def resolve_code_references(self, item_ids: List[str]) -> List[str]:
        """Find all code files related to a list of retrieved items (diagrams/sections)."""
        code_refs = set()
        for item_id in item_ids:
            related = self.get_related_items(item_id)
            if related:
                code_refs.update(related.code_refs)
        return list(code_refs)

    def build_mock_links(self):
        """Populate mock links for demo purposes."""
        # AXI Bus Entity
        self.link_diagram("axi_bus", "img_axi_topology")
        self.link_section("axi_bus", "sec_axi_overview")
        self.link_section("axi_bus", "sec_axi_timing")
        self.link_code("axi_bus", "hw/axi_interconnect.v")
        self.link_code("axi_bus", "hw/axi_master_if.sv")

        # CDC FIFO Entity
        self.link_diagram("cdc_fifo", "img_cdc_sync")
        self.link_section("cdc_fifo", "sec_cdc_design")
        self.link_code("cdc_fifo", "hw/async_fifo.v")
        self.link_code("cdc_fifo", "hw/sync_stages.v")
        
        # Power Mgmt Entity
        self.link_diagram("power_mgmt", "img_power_states")
        self.link_section("power_mgmt", "sec_clock_gating")
        self.link_code("power_mgmt", "hw/clk_gate_cell.v")
        self.link_code("power_mgmt", "fw/pmu_controller.c")
