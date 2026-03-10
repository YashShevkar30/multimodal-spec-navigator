"""
Orchestrates the entire spec navigation workflow.
Queries the index and enriches results using the linker.
"""

from typing import List, Dict, Any, Optional

import structlog

from navigator.cross_modal import CrossModalIndex, SearchResult
from navigator.linker import ArchitectureLinker
from navigator.feedback import FeedbackTracker

logger = structlog.get_logger()

class NavigationWorkflow:
    """Packages retrieval and linking into one end-to-end flow."""
    
    def __init__(self, index: CrossModalIndex, linker: ArchitectureLinker, tracker: FeedbackTracker):
        self.index = index
        self.linker = linker
        self.tracker = tracker

    def query(self, text_query: str, top_k: int = 5) -> Dict[str, Any]:
        """Run a text query to find matching figures, sections, and code."""
        # 1. Start session
        session_id = self.tracker.start_session(text_query, query_type="text")
        
        # 2. Search index
        results = self.index.search_by_text(text_query, top_k=top_k)
        
        # 3. Enrich and format results
        enriched_results = []
        for rank, res in enumerate(results, 1):
            item_id = res.item.id
            
            # Find linked items (e.g. if this is a diagram, find the code)
            related = self.linker.get_related_items(item_id)
            code_refs = related.code_refs if related else []
            related_diagrams = related.diagram_ids if related else []
            
            # Remove self from related
            if item_id in related_diagrams:
                related_diagrams.remove(item_id)
                
            entry = {
                "rank": rank,
                "score": round(res.score, 3),
                "item_id": item_id,
                "type": res.item.type,
                "content": res.item.content,
                "source": res.item.source,
                "title": res.item.metadata.get("title", "Untitled"),
                "related_code": code_refs,
                "related_diagrams": related_diagrams
            }
            enriched_results.append(entry)
            
        # 4. Log to tracker
        self.tracker.log_results(session_id, [r["item_id"] for r in enriched_results])
        
        logger.info(
            "workflow_completed",
            query=text_query,
            results=len(enriched_results),
            session_id=session_id
        )
        
        return {
            "session_id": session_id,
            "query": text_query,
            "results": enriched_results
        }
