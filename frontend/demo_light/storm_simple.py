import os
import streamlit as st

# Simple minimal version without problematic imports
script_dir = os.path.dirname(os.path.abspath(__file__))

def main():
    st.set_page_config(
        layout="wide",
        page_title="STORM - Enhanced Article Generator",
        page_icon="⚡"
    )

    st.markdown("# ⚡ STORM - Enhanced Article Generator")
    st.markdown("*Powered by Enhanced Outline Generation & Multi-Perspective AI Research*")
    
    # Simple menu
    tab1, tab2 = st.tabs(["My Articles", "Create New Article"])
    
    with tab1:
        st.markdown("### My Articles")
        st.info("Articles will be listed here once the full system is loaded.")
        
        # List any existing articles
        demo_dir = os.path.join(script_dir, "DEMO_WORKING_DIR")
        if os.path.exists(demo_dir):
            articles = [d for d in os.listdir(demo_dir) if os.path.isdir(os.path.join(demo_dir, d))]
            if articles:
                st.markdown("#### Generated Articles:")
                for article in articles:
                    with st.expander(f"📄 {article.replace('_', ' ').title()}"):
                        article_path = os.path.join(demo_dir, article)
                        
                        # Show outline if exists
                        outline_path = os.path.join(article_path, "storm_gen_outline.txt")
                        if os.path.exists(outline_path):
                            with open(outline_path, 'r') as f:
                                outline = f.read()
                            st.markdown("**Enhanced Outline:**")
                            st.code(outline)
                        
                        # Show article if exists
                        article_file = os.path.join(article_path, "storm_gen_article_polished.txt")
                        if os.path.exists(article_file):
                            with open(article_file, 'r') as f:
                                content = f.read()
                            st.markdown("**Generated Article:**")
                            st.markdown(content)
            else:
                st.info("No articles generated yet. Use the 'Create New Article' tab to get started.")
        else:
            st.info("No articles directory found. Create your first article to get started.")
    
    with tab2:
        st.markdown("### Create New Article")
        st.warning("⚠️ Full article generation requires the complete STORM system.")
        st.markdown("The system includes:")
        st.markdown("- ✅ Enhanced outline generation with validation")
        st.markdown("- ✅ Multi-perspective AI research")
        st.markdown("- ✅ Gemini models integration")
        st.markdown("- ✅ Perplexity search engine")
        
        topic = st.text_input("Enter article topic:", placeholder="e.g., Impact of AI on employment")
        
        if st.button("Generate Article"):
            if topic:
                st.info(f"To generate an article about '{topic}', please run the enhanced STORM system via command line:")
                st.code(f"""
# Run the enhanced STORM system
python test_enhanced_outline.py

# Or use the original command line interface
python examples/storm_examples/run_storm_wiki_gemini.py
                """)
                st.markdown("The results will appear in the 'My Articles' tab once generated.")
            else:
                st.error("Please enter a topic first.")

if __name__ == "__main__":
    main()