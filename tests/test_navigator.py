"""
Tests for Multimodal Spec Navigator.
"""

import pytest
import numpy as np
from navigator.cross_modal import CrossModalIndex
from navigator.linker import ArchitectureLinker
from navigator.feedback import FeedbackTracker
from navigator.workflow import NavigationWorkflow

def test_cross_modal_index_mock():
    index = CrossModalIndex(demo_mode=True)
    
    # Test encoding
    vecs = index.encode_text(["hello", "world"])
    assert vecs.shape == (2, 512)
    
    # Test adding and searching
    index.add_texts(["text1", "text2"], ["id1", "id2"], ["s1", "s2"], [{}, {}])
    index.add_images(["img1.png"], ["id3"], ["s3"], [{}])
    
    assert len(index.items) == 3
    
    results = index.search_by_text("query", top_k=2)
    assert len(results) == 2
    
def test_architecture_linker():
    linker = ArchitectureLinker()
    
    linker.link_diagram("module_a", "diagram_1")
    linker.link_section("module_a", "section_2")
    linker.link_code("module_a", "code_3.py")
    
    related = linker.get_related_items("diagram_1")
    assert related is not None
    assert "section_2" in related.section_ids
    assert "code_3.py" in related.code_refs
    
    code = linker.resolve_code_references(["diagram_1"])
    assert "code_3.py" in code

def test_feedback_tracker(tmp_path):
    tracker = FeedbackTracker(storage_dir=str(tmp_path))
    
    sess_id = tracker.start_session("test query", "text")
    assert sess_id is not None
    
    tracker.log_results(sess_id, ["item1", "item2"])
    tracker.submit_feedback(sess_id, "item1", True, "Great result")
    tracker.submit_feedback(sess_id, "item2", False, "Not relevant")
    
    metrics = tracker.get_metrics()
    assert metrics["total_queries"] == 1
    assert metrics["positive_feedback"] == 1
    assert metrics["negative_feedback"] == 1

def test_workflow(tmp_path):
    index = CrossModalIndex(demo_mode=True)
    index.add_texts(["text"], ["id1"], ["s"], [{"title": "t"}])
    
    linker = ArchitectureLinker()
    linker.link_code("id1", "file.py")
    
    tracker = FeedbackTracker(storage_dir=str(tmp_path))
    
    workflow = NavigationWorkflow(index, linker, tracker)
    res = workflow.query("query")
    
    assert res["session_id"] is not None
    assert len(res["results"]) == 1
    assert res["results"][0]["item_id"] == "id1"
    assert "file.py" in res["results"][0]["related_code"]
