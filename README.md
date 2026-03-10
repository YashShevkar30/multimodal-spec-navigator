# Multimodal Spec Navigator

A lightweight cross-modal retrieval tool built for engineering specifications. Search across architectural text, design diagrams, and code snippets simultaneously, using OpenAI's CLIP model for image-text alignments.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-Machine_Learning-ee4c2c?logo=pytorch&logoColor=white)
![Gradio](https://img.shields.io/badge/Gradio-UI-orange)
![FAISS](https://img.shields.io/badge/FAISS-Vector_Search-blue)

---

## Features

- **Cross-Modal Retrieval**: Query text to find diagrams, or query a diagram to find related spec sections. Uses `sentence-transformers` for text and `CLIP` for images mapped to the same 512D vector space.
- **Traceable Workflow**: Packages queries, encode operations, index searches, and link resolutions into a single logged operational workflow.
- **Context Linker**: Architectural mapping engine that connects specific design diagrams (e.g. `axi_topology.png`) to their detailed text sections and hardware/software source code (`axi_master_if.sv`).
- **Feedback Loop**: Collects explicit positive/negative (`👍 / 👎`) relevance labels on search results to power future fine-tuning or reranking training data.
- **Lightweight UI**: Fast Gradio-based interface for browsing top matches and analyzing source context.

---

## Quick Start

### Installation

```bash
git clone https://github.com/YashShevkar30/multimodal-spec-navigator.git
cd multimodal-spec-navigator
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Try the Gradio UI

Run the user interface (includes demo data and mock embeddings by default so no models must be downloaded):

```bash
python -m ui.app
```

Navigate to `http://localhost:7860` in your web browser.

### Run Tests

```bash
pytest tests/ -v
```

---

## Technical Architecture

1. **Dual Encoders**:
   - Text encoded via MiniLM.
   - Images encoded via CLIP.
2. **Unified Index**: FAISS Inner-Product index where normalized image and text embeddings co-exist.
3. **Linker Graph**: Manual or parsed graph associating components like `List[diagram_id] ↔ Entity ↔ List[code_ref]`.
4. **Session Tracking**: Generates unique `session_id`, logging retrieval results and collecting feedback to an SQLite/JSON local database.
