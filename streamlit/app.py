"""
Streamlit interface for AI Lifting Document Cleanup Tool
"""
import streamlit as st
import requests
import json
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

# Configuration
import os
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_PREFIX = "/api/v1"

# Page configuration
st.set_page_config(
    page_title="AI Document Cleanup",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .result-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)


def make_api_request(method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Optional[Dict]:
    """Make API request and handle errors."""
    url = f"{API_BASE_URL}{API_PREFIX}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, params=params, timeout=30)
        elif method == "POST":
            # Longer timeout for analysis and indexing endpoints that use LLM
            if "analyze" in endpoint.lower() or "index" in endpoint.lower():
                timeout_value = 600  # 10 minutes for LLM-heavy operations
            else:
                timeout_value = 60
            response = requests.post(url, json=data, params=params, timeout=timeout_value)
        elif method == "PUT":
            response = requests.put(url, json=data, params=params, timeout=60)
        elif method == "DELETE":
            response = requests.delete(url, timeout=30)
        else:
            st.error(f"Unsupported HTTP method: {method}")
            return None
            
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                st.error(f"Details: {error_detail}")
            except:
                st.error(f"Response: {e.response.text}")
        return None


def main():
    """Main application."""
    # Header
    st.markdown('<div class="main-header">📚 AI Document Cleanup Tool</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        # For Docker, use the environment variable, for local dev allow override
        default_url = API_BASE_URL
        if "localhost" in default_url or "127.0.0.1" in default_url:
            api_url = st.text_input("API URL", value=default_url, key="api_url_input")
        else:
            api_url = default_url
            st.info(f"API: {api_url}")
        
        st.divider()
        
        # Health check
        if st.button("🔍 Check API Status"):
            with st.spinner("Checking API..."):
                try:
                    response = requests.get(f"{api_url}/health", timeout=5)
                    if response.status_code == 200:
                        health_data = response.json()
                        st.success("✅ API is healthy")
                        st.json(health_data)
                    else:
                        st.error(f"❌ API returned status {response.status_code}")
                except Exception as e:
                    st.error(f"❌ Cannot connect to API: {str(e)}")
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔍 Search", "📄 Index Documents", "📊 Statistics", "⚙️ Management", "📝 Synthesis"])
    
    # Tab 1: Search
    with tab1:
        st.header("Semantic Search")
        st.markdown("Search through your indexed documents using semantic search.")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input(
                "Search query",
                placeholder="e.g., What are the safety requirements for lifting operations?",
                key="search_input"
            )
        
        with col2:
            top_k = st.number_input("Results", min_value=1, max_value=50, value=10, step=1)
        
        if st.button("🔍 Search", type="primary", use_container_width=True):
            if not search_query:
                st.warning("Please enter a search query")
            else:
                with st.spinner("Searching..."):
                    result = make_api_request(
                        "POST",
                        "/search/search",
                        data={
                            "query": search_query,
                            "top_k": top_k
                        }
                    )
                    
                    if result:
                        st.success(f"Found {result.get('total_results', 0)} results")
                        
                        results = result.get("results", [])
                        if results:
                            for idx, res in enumerate(results, 1):
                                with st.expander(
                                    f"📄 Result {idx}: {res.get('filename', 'Unknown')} "
                                    f"(Score: {res.get('score', 0):.3f})",
                                    expanded=(idx == 1)
                                ):
                                    col_a, col_b = st.columns([2, 1])
                                    
                                    with col_a:
                                        st.markdown("**Content:**")
                                        st.markdown(res.get('content', ''))
                                    
                                    with col_b:
                                        st.markdown("**Metadata:**")
                                        st.write(f"**File:** {res.get('filename', 'N/A')}")
                                        if res.get('page_number'):
                                            st.write(f"**Page:** {res.get('page_number')}")
                                        if res.get('section_title'):
                                            st.write(f"**Section:** {res.get('section_title')}")
                                        st.write(f"**Score:** {res.get('score', 0):.4f}")
                                        st.write(f"**Distance:** {res.get('distance', 0):.4f}")
                        else:
                            st.info("No results found")
    
    # Tab 2: Index Documents
    with tab2:
        st.header("Index Documents")
        st.markdown("Index documents from the data folder into the vector store.")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            session_id = st.number_input(
                "Session ID (optional)",
                min_value=1,
                value=1,
                step=1,
                help="Optional session ID to associate documents with"
            )
        
        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
        
        if st.button("🚀 Index Documents", type="primary", use_container_width=True):
            with st.spinner("Indexing documents... This may take a while."):
                result = make_api_request(
                    "POST",
                    "/documents/index-data-folder",
                    params={"session_id": session_id} if session_id else None
                )
                
                if result:
                    st.success("✅ Indexing completed!")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Processed", result.get("processed", 0))
                    
                    with col2:
                        st.metric("Failed", result.get("failed", 0))
                    
                    with col3:
                        st.metric("Indexed Chunks", result.get("indexed_chunks", 0))
                    
                    with col4:
                        st.metric("Success Rate", 
                                 f"{(result.get('processed', 0) / max(result.get('processed', 0) + result.get('failed', 0), 1) * 100):.1f}%")
                    
                    failed_docs = result.get("failed_documents", [])
                    if failed_docs:
                        st.warning(f"⚠️ {len(failed_docs)} documents failed to process:")
                        for doc in failed_docs:
                            with st.expander(f"❌ {doc.get('filename', 'Unknown')}"):
                                st.error(doc.get('error', 'Unknown error'))
        
        st.divider()
        
        # Index Schema
        st.subheader("Vector Store Schema")
        if st.button("📋 View Schema", use_container_width=True):
            with st.spinner("Loading schema..."):
                schema = make_api_request("GET", "/documents/index-schema")
                if schema:
                    st.json(schema)
    
    # Tab 3: Statistics
    with tab3:
        st.header("Vector Store Statistics")
        st.markdown("View statistics about your indexed documents.")
        
        if st.button("📊 Refresh Statistics", type="primary", use_container_width=True):
            with st.spinner("Loading statistics..."):
                stats = make_api_request("GET", "/search/stats")
                
                if stats:
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Vectors", stats.get("total_vectors", 0))
                    
                    with col2:
                        st.metric("Dimension", stats.get("dimension", 0))
                    
                    with col3:
                        st.metric("Current Count", stats.get("current_count", 0))
                    
                    with col4:
                        st.metric("Max Elements", stats.get("max_elements", 0))
                    
                    st.divider()
                    
                    st.subheader("Details")
                    st.json(stats)
                else:
                    st.error("Failed to load statistics")
    
    # Tab 4: Management
    with tab4:
        st.header("Index Management")
        st.markdown("Manage your vector store index.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Clear Index")
            st.warning("⚠️ This will delete all indexed documents!")
            
            if st.button("🗑️ Clear All Indexes", type="secondary", use_container_width=True):
                confirm = st.checkbox("I understand this will delete all data", key="clear_confirm")
                if confirm:
                    if st.button("✅ Confirm Clear", type="primary", use_container_width=True):
                        with st.spinner("Clearing index..."):
                            result = make_api_request("POST", "/search/clear-index")
                            if result:
                                st.success("✅ Index cleared successfully")
                                st.balloons()
        
        with col2:
            st.subheader("API Information")
            st.info(f"API Base URL: `{api_url}`")
            st.info(f"API Prefix: `{API_PREFIX}`")
            
            if st.button("🔗 Open API Docs", use_container_width=True):
                st.markdown(f"[Open Swagger UI]({api_url}/docs)")
    
    # Tab 5: Synthesis
    with tab5:
        st.header("📝 Document Synthesis")
        st.markdown("Create a unified document by synthesizing multiple source documents.")
        
        # Initialize session state
        if 'synthesis_session_id' not in st.session_state:
            st.session_state.synthesis_session_id = None
        if 'synthesis_inventory' not in st.session_state:
            st.session_state.synthesis_inventory = None
        if 'synthesis_paragraphs' not in st.session_state:
            st.session_state.synthesis_paragraphs = {}
        if 'synthesis_selected' not in st.session_state:
            st.session_state.synthesis_selected = {}
        
        # Step 1: Create or select session
        st.subheader("Step 1: Create Synthesis Session")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            session_name = st.text_input("Session Name", value="Synthesis Session", key="synth_session_name")
            session_desc = st.text_area("Description (optional)", key="synth_session_desc")
        
        with col2:
            st.write("")  # Spacing
        
        # Get available PDF files
        try:
            # Try multiple paths (local dev, Docker container)
            possible_paths = [
                Path("/app/data"),  # Docker container path
                Path("data"),  # Local development
                Path("../data"),  # Alternative local path
            ]
            
            pdf_files = []
            for data_dir in possible_paths:
                if data_dir.exists():
                    pdf_files = [f.name for f in data_dir.glob("*.pdf")]
                    if pdf_files:
                        break
        except Exception as e:
            st.warning(f"Error finding PDF files: {e}")
            pdf_files = []
        
        if pdf_files:
            selected_files = st.multiselect(
                "Select Source Documents",
                pdf_files,
                default=pdf_files[:3] if len(pdf_files) >= 3 else pdf_files,
                key="synth_selected_files"
            )
            
            if st.button("🚀 Create Session", type="primary", use_container_width=True):
                if not selected_files:
                    st.warning("Please select at least one document")
                else:
                    with st.spinner("Creating session..."):
                        result = make_api_request(
                            "POST",
                            "/synthesis/sessions",
                            data={
                                "name": session_name,
                                "description": session_desc,
                                "source_filenames": selected_files
                            }
                        )
                        
                        if result:
                            st.session_state.synthesis_session_id = result.get("id")
                            st.success(f"✅ Session created! ID: {result.get('id')}")
                            st.rerun()
        else:
            st.warning("No PDF files found in data folder. Please index documents first.")
        
        # Step 2: Analyze structures and create inventory
        if st.session_state.synthesis_session_id:
            st.divider()
            st.subheader("Step 2: Analyze Document Structures")
            
            if st.button("🔍 Analyze Structures & Generate Inventory Table", type="primary", use_container_width=True):
                with st.spinner("Analyzing document structures... This may take a while."):
                    result = make_api_request(
                        "POST",
                        f"/synthesis/sessions/{st.session_state.synthesis_session_id}/analyze-structures",
                        data={
                            "filenames": selected_files
                        }
                    )
                    
                    if result and result.get("success"):
                        analysis = result.get("analysis", {})
                        common_struct = analysis.get("common_structure", {})
                        inventory = common_struct.get("inventory_table", [])
                        st.session_state.synthesis_inventory = inventory
                        st.success("✅ Structure analysis completed!")
                        st.rerun()
            
            # Display and edit inventory table
            if st.session_state.synthesis_inventory:
                st.divider()
                st.subheader("Step 3: Review & Edit Inventory Table")
                st.markdown("Review the generated table of contents. You can add, remove, or modify sections.")
                
                # Editable inventory table
                inventory_data = []
                for idx, section in enumerate(st.session_state.synthesis_inventory):
                    inventory_data.append({
                        "Order": section.get("order", idx + 1),
                        "Title": section.get("title", ""),
                        "Level": section.get("level", 1)
                    })
                
                edited_inventory = st.data_editor(
                    inventory_data,
                    num_rows="dynamic",
                    use_container_width=True,
                    key="inventory_editor"
                )
                
                if st.button("💾 Save Inventory Table", type="primary", use_container_width=True):
                    # Convert back to API format
                    updated_inventory = [
                        {
                            "order": int(row.get("Order", idx + 1)),
                            "title": row.get("Title", ""),
                            "level": int(row.get("Level", 1))
                        }
                        for idx, row in enumerate(edited_inventory)
                    ]
                    
                    with st.spinner("Saving inventory table..."):
                        result = make_api_request(
                            "PUT",
                            f"/synthesis/sessions/{st.session_state.synthesis_session_id}/inventory-table",
                            data={"inventory_table": updated_inventory}
                        )
                        
                        if result and result.get("success"):
                            st.session_state.synthesis_inventory = updated_inventory
                            st.success("✅ Inventory table saved!")
                
                # Step 4: Review paragraphs for each section
                st.divider()
                st.subheader("Step 4: Review Paragraphs by Section")
                
                if st.session_state.synthesis_inventory:
                    for section in sorted(st.session_state.synthesis_inventory, key=lambda x: x.get("order", 999)):
                        section_title = section.get("title", "")
                        section_level = section.get("level", 1)
                        
                        # Add indentation to expander title based on level
                        indent_prefix = "  " * (section_level - 1)
                        expander_title = f"{indent_prefix}📄 {section_title}"
                        
                        with st.expander(expander_title, expanded=False):
                            if st.button(f"🔍 Find Paragraphs for: {section_title}", key=f"find_{section_title}"):
                                with st.spinner(f"Finding relevant paragraphs for '{section_title}'..."):
                                    result = make_api_request(
                                        "POST",
                                        f"/synthesis/sessions/{st.session_state.synthesis_session_id}/paragraphs",
                                        data={
                                            "section_title": section_title,
                                            "top_k": 10
                                        }
                                    )
                                    
                                    if result and result.get("success"):
                                        paragraphs = result.get("paragraphs", [])
                                        st.session_state.synthesis_paragraphs[section_title] = paragraphs
                                            
                                        st.info(f"Found {len(paragraphs)} relevant paragraphs")
                                        
                                        # Initialize selected_para_ids if not exists
                                        if section_title not in st.session_state.synthesis_selected:
                                            st.session_state.synthesis_selected[section_title] = []
                                        
                                        # Display paragraphs with selection
                                        for para in paragraphs:
                                            para_id = para.get("id", "")
                                            is_selected = para_id in st.session_state.synthesis_selected[section_title]
                                            
                                            # Build label with scores
                                            label_parts = [f"**{para.get('filename', 'Unknown')}**"]
                                            label_parts.append(f"Page {para.get('page_number', '?')}")
                                            
                                            # Show LLM relevance score if available
                                            if para.get('llm_relevance_score'):
                                                label_parts.append(f"LLM Relevance: {para.get('llm_relevance_score', 0):.2f}")
                                            else:
                                                label_parts.append(f"Vector Score: {para.get('score', 0):.3f}")
                                            
                                            checkbox_key = f"para_{section_title}_{para_id}"
                                            selected = st.checkbox(
                                                " | ".join(label_parts),
                                                value=is_selected,
                                                key=checkbox_key
                                            )
                                            
                                            # Update state directly based on checkbox value
                                            if selected and para_id not in st.session_state.synthesis_selected[section_title]:
                                                st.session_state.synthesis_selected[section_title].append(para_id)
                                            elif not selected and para_id in st.session_state.synthesis_selected[section_title]:
                                                st.session_state.synthesis_selected[section_title].remove(para_id)
                                            
                                            with st.container():
                                                # Get section level for indentation
                                                section_level = section.get("level", 1)
                                                indent = "  " * (section_level - 1)  # 2 spaces per level
                                                
                                                # Show full paragraph content
                                                st.markdown(f"{indent}*{para.get('content', '')}*")
                                                st.divider()
                                        
                                        # Show info after processing all checkboxes
                                        selected_count = len(st.session_state.synthesis_selected[section_title])
                                        st.info(f"{len(paragraphs)} paragraphs found, {selected_count} selected")
                                    
                            # Show already loaded paragraphs
                            elif section_title in st.session_state.synthesis_paragraphs:
                                paragraphs = st.session_state.synthesis_paragraphs[section_title]
                                
                                # Initialize selected_para_ids if not exists
                                if section_title not in st.session_state.synthesis_selected:
                                    st.session_state.synthesis_selected[section_title] = []
                                
                                # Display paragraphs with selection
                                for para in paragraphs:
                                    para_id = para.get("id", "")
                                    is_selected = para_id in st.session_state.synthesis_selected[section_title]
                                    
                                    # Build label with scores
                                    label_parts = [f"**{para.get('filename', 'Unknown')}**"]
                                    label_parts.append(f"Page {para.get('page_number', '?')}")
                                    
                                    # Show LLM relevance score if available
                                    if para.get('llm_relevance_score'):
                                        label_parts.append(f"LLM Relevance: {para.get('llm_relevance_score', 0):.2f}")
                                    else:
                                        label_parts.append(f"Vector Score: {para.get('score', 0):.3f}")
                                    
                                    checkbox_key = f"para_{section_title}_{para_id}_loaded"
                                    selected = st.checkbox(
                                        " | ".join(label_parts),
                                        value=is_selected,
                                        key=checkbox_key
                                    )
                                    
                                    # Update state directly based on checkbox value
                                    if selected and para_id not in st.session_state.synthesis_selected[section_title]:
                                        st.session_state.synthesis_selected[section_title].append(para_id)
                                    elif not selected and para_id in st.session_state.synthesis_selected[section_title]:
                                        st.session_state.synthesis_selected[section_title].remove(para_id)
                                    
                                    with st.container():
                                        # Get section level for indentation
                                        section_level = section.get("level", 1)
                                        indent = "  " * (section_level - 1)  # 2 spaces per level
                                        
                                        # Show full paragraph content
                                        st.markdown(f"{indent}*{para.get('content', '')}*")
                                        st.divider()
                                
                                # Show info after processing all checkboxes
                                selected_count = len(st.session_state.synthesis_selected[section_title])
                                st.info(f"{len(paragraphs)} paragraphs loaded, {selected_count} selected")
                    
                    # Save selections
                    if st.button("💾 Save Paragraph Selections", type="primary", use_container_width=True):
                        with st.spinner("Saving selections..."):
                            result = make_api_request(
                                "POST",
                                f"/synthesis/sessions/{st.session_state.synthesis_session_id}/select-paragraphs",
                                data={"selected_paragraphs": st.session_state.synthesis_selected}
                            )
                            
                            if result and result.get("success"):
                                st.success("✅ Paragraph selections saved!")
                    
                    # Step 5: Generate document
                    st.divider()
                    st.subheader("Step 5: Generate Synthesis Document")
                    
                    if st.button("📝 Generate Final Document", type="primary", use_container_width=True):
                        with st.spinner("Generating synthesis document... This may take a while."):
                            result = make_api_request(
                                "POST",
                                f"/synthesis/sessions/{st.session_state.synthesis_session_id}/generate-document"
                            )
                            
                            if result and result.get("success"):
                                document_base64 = result.get("document_base64", "")
                                filename = result.get("filename", "synthesis_document.docx")
                                st.session_state.synthesis_document = document_base64
                                st.session_state.synthesis_filename = filename
                                st.success("✅ Document generated successfully!")
                                
                                # Download button for DOCX
                                import base64
                                if document_base64:
                                    doc_bytes = base64.b64decode(document_base64)
                                    st.download_button(
                                        label="📥 Download DOCX Document",
                                        data=doc_bytes,
                                        file_name=filename,
                                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                    )
    
    # Footer
    st.divider()
    st.markdown(
        "<div style='text-align: center; color: #666; padding: 1rem;'>"
        "AI Document Cleanup Tool v0.1.0 | Built with Streamlit"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

