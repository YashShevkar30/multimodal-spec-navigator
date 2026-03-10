"""
Gradio UI for the Multimodal Spec Navigator.
"""

import os
import gradio as gr
from PIL import Image

from navigator.cross_modal import CrossModalIndex
from navigator.linker import ArchitectureLinker
from navigator.feedback import FeedbackTracker
from navigator.workflow import NavigationWorkflow
from navigator.config import get_settings

settings = get_settings()

def get_demo_app():
    """Build and return the Gradio interface."""
    
    # 1. Initialize components
    index = CrossModalIndex(demo_mode=True)
    linker = ArchitectureLinker()
    tracker = FeedbackTracker(storage_dir="feedback_db")
    workflow = NavigationWorkflow(index, linker, tracker)
    
    # 2. Add some dummy data for demo purposes
    index.add_texts(
        texts=[
            "The AXI bus protocol defines rules for high-performance, high-frequency system designs.",
            "Asynchronous FIFOs are used for reliable Clock Domain Crossing (CDC) between primary and bus clocks."
        ],
        ids=["sec_axi_overview", "sec_cdc_design"],
        sources=["axi_spec.md", "cdc_design.md"],
        metadatas=[{"title": "AXI Overview"}, {"title": "CDC Design"}]
    )
    
    # Needs valid image paths for CLIP encoding if not in demo mode
    # For demo mode (mock), any string works
    index.add_images(
        image_paths=["data/sample_specs/axi_topology.png", "data/sample_specs/cdc_fifo.png"],
        ids=["img_axi_topology", "img_cdc_sync"],
        sources=["axi_spec.md", "cdc_design.md"],
        metadatas=[{"title": "AXI Bus Topology"}, {"title": "CDC Synchronizer Block"}]
    )
    
    linker.build_mock_links()

    # 3. Define UI layout
    with gr.Blocks(title="Multimodal Spec Navigator", theme=gr.themes.Soft()) as app:
        
        # State to store current session ID
        current_session = gr.State("")
        current_results = gr.State([])
        
        gr.Markdown("# 🔍 Multimodal Spec Navigator")
        gr.Markdown("Search across text specifications, architectural diagrams, and code references simultaneously.")
        
        with gr.Row():
            search_input = gr.Textbox(
                label="Search Query", 
                placeholder="e.g. 'How does clock domain crossing work?' or 'AXI bus topology'",
                scale=4
            )
            search_btn = gr.Button("Search", variant="primary", scale=1)
            
        gr.Markdown("### Results")
        
        # We'll display results dynamically in a generic HTML block, or using Dataframes
        results_html = gr.HTML(value="<div style='color: gray'>Enter a query to see results...</div>")
        
        with gr.Accordion("Rate Results (Feedback)", open=False):
            gr.Markdown("Help improve retrieval by rating the top result.")
            with gr.Row():
                upvote_btn = gr.Button("👍 Relevant")
                downvote_btn = gr.Button("👎 Not Relevant")
            feedback_msg = gr.Markdown("")

        def run_search(query):
            if not query.strip():
                return "<div style='color: red'>Please enter a query.</div>", "", []
                
            res = workflow.query(query, top_k=3)
            sess_id = res["session_id"]
            items = res["results"]
            
            html = "<div style='display: flex; flex-direction: column; gap: 20px;'>"
            for r in items:
                # Format each result card
                card = f"""
                <div style='border: 1px solid #ddd; border-radius: 8px; padding: 16px; background: white;'>
                    <h3 style='margin-top: 0;'>{r['title']} <span style='color: gray; font-size: 0.8em'>({round(r['score'], 2)})</span></h3>
                    <div style='margin-bottom: 8px;'>
                        <span style='background: #eee; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; margin-right: 8px;'>
                            {'🖼️ Image' if r['type'] == 'image' else '📄 Text'}
                        </span>
                        <span style='color: #666; font-size: 0.9em;'>Source: {r['source']}</span>
                    </div>
                """
                
                if r['type'] == 'text':
                    card += f"<p style='background: #f9f9f9; padding: 12px; border-left: 3px solid #ccc;'>{r['content']}</p>"
                else:
                    card += f"<p style='color: gray'>[Image placeholder: {r['content']}]</p>"
                    
                if r['related_code'] or r['related_diagrams']:
                    card += "<div style='margin-top: 12px; font-size: 0.9em; border-top: 1px solid #eee; padding-top: 8px;'>"
                    if r['related_code']:
                        card += f"<div><strong>💻 Related Code:</strong> {', '.join(r['related_code'])}</div>"
                    if r['related_diagrams']:
                        card += f"<div><strong>📊 Related Figures:</strong> {', '.join(r['related_diagrams'])}</div>"
                    card += "</div>"
                    
                card += "</div>"
                html += card
                
            html += "</div>"
            
            return html, sess_id, items

        def handle_feedback(sess_id, results_list, is_relevant):
            if not sess_id or not results_list:
                return "No active search session."
            
            # Submit feedback for the top item
            top_item = results_list[0]["item_id"]
            tracker.submit_feedback(sess_id, top_item, is_relevant)
            
            icon = "👍" if is_relevant else "👎"
            return f"{icon} Feedback saved for '{top_item}'. Thank you!"

        search_btn.click(
            fn=run_search,
            inputs=[search_input],
            outputs=[results_html, current_session, current_results]
        )
        search_input.submit(
            fn=run_search,
            inputs=[search_input],
            outputs=[results_html, current_session, current_results]
        )
        
        upvote_btn.click(
            fn=lambda s, r: handle_feedback(s, r, True),
            inputs=[current_session, current_results],
            outputs=[feedback_msg]
        )
        downvote_btn.click(
            fn=lambda s, r: handle_feedback(s, r, False),
            inputs=[current_session, current_results],
            outputs=[feedback_msg]
        )

    return app

if __name__ == "__main__":
    app = get_demo_app()
    app.launch(server_port=settings.ui_port, share=settings.ui_share)
