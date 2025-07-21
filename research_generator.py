#!/usr/bin/env python3
"""
Universal Research Report Generator
Abstracted from quantum_research.py to handle any research topic
"""

import asyncio
import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv
from typing import List, Dict, Optional

# Load environment
load_dotenv()

class ResearchGenerator:
    def __init__(self, topic: str, output_base_dir: str = "results"):
        self.topic = topic
        self.output_base_dir = output_base_dir
        self.sanitized_topic = self._sanitize_topic_name(topic)
        self.output_dir = os.path.join(output_base_dir, f"{self.sanitized_topic}_research")
        
    def _sanitize_topic_name(self, topic: str) -> str:
        """Convert topic to safe directory name"""
        # Remove special characters, convert to lowercase, replace spaces with underscores
        sanitized = re.sub(r'[^\w\s-]', '', topic.lower())
        sanitized = re.sub(r'[-\s]+', '_', sanitized)
        return sanitized[:100]  # Limit length
    
    def generate_search_queries(self) -> List[str]:
        """Generate search queries for the given topic using LLM"""
        from knowledge_storm.lm import OpenAIModel
        
        openai_model = OpenAIModel(
            model='gpt-4o-mini',
            api_key=os.getenv('OPENAI_API_KEY'),
            max_tokens=1000,
            temperature=0.7
        )
        
        query_prompt = f"""Generate 8 comprehensive search queries for researching the topic: "{self.topic}"

The queries should cover different aspects and perspectives of the topic to ensure comprehensive coverage. 

Requirements:
- Each query should be specific and focused
- Queries should cover different aspects of the topic and not be too broad - they should cover what a highgly intelligent person would want to know about the topic
- Use terms that would return high-quality, authoritative sources
- Each query should be 3-10 words long
- Return ONLY the queries, one per line, without numbering or bullet points

Topic: {self.topic}"""

        response = openai_model.basic_request(query_prompt)
        
        # Handle different response formats
        if 'choices' in response:
            choice = response['choices'][0]
            if 'text' in choice:
                content = choice['text']
            elif 'message' in choice and 'content' in choice['message']:
                content = choice['message']['content']
            else:
                content = str(response)
        else:
            content = str(response)
        
        # Parse queries from response
        queries = [line.strip() for line in content.split('\n') if line.strip() and not line.strip().startswith(('#', '-', '*', '1.', '2.'))]
        
        # Filter and clean queries
        clean_queries = []
        for query in queries:
            # Remove numbering patterns
            clean_query = re.sub(r'^\d+[\.\)]\s*', '', query)
            clean_query = re.sub(r'^[-*]\s*', '', query)
            clean_query = clean_query.strip('"\'')
            
            if clean_query and len(clean_query) > 10:  # Ensure meaningful queries
                clean_queries.append(clean_query)
        
        return clean_queries[:8]  # Limit to 8 queries
    
    def display_queries_for_approval(self, queries: List[str]) -> None:
        """Display generated queries to user for approval"""
        print(f"\n📋 Generated search queries for: {self.topic}")
        print("=" * 60)
        for i, query in enumerate(queries, 1):
            print(f"{i:2}. {query}")
        print("=" * 60)
    
    def get_user_approval(self, queries: List[str]) -> tuple[bool, Optional[str]]:
        """Get user approval for queries. Returns (approved, feedback)"""
        self.display_queries_for_approval(queries)
        
        print("\nDo you approve these search queries?")
        print("Options:")
        print("  'yes' or 'y' - Approve and continue")
        print("  'no' or 'n' - Regenerate without instructions")
        print("  'modify: <instructions>' - Regenerate with your specific instructions")
        print("  'quit' or 'q' - Exit")
        
        user_input = input("\nYour choice: ").strip().lower()
        
        if user_input in ['yes', 'y']:
            return True, None
        elif user_input in ['no', 'n']:
            return False, None
        elif user_input.startswith('modify:'):
            feedback = user_input[7:].strip()  # Remove "modify:" prefix
            return False, feedback
        elif user_input in ['quit', 'q']:
            print("Research cancelled.")
            exit(0)
        else:
            print("Invalid option. Please try again.")
            return self.get_user_approval(queries)
    
    def regenerate_search_queries(self, feedback: Optional[str] = None) -> List[str]:
        """Regenerate search queries with optional user feedback"""
        from knowledge_storm.lm import OpenAIModel
        
        openai_model = OpenAIModel(
            model='gpt-4o-mini',
            api_key=os.getenv('OPENAI_API_KEY'),
            max_tokens=1000,
            temperature=0.8  # Slightly higher temperature for variation
        )
        
        if feedback:
            query_prompt = f"""Generate 8 comprehensive search queries for researching the topic: "{self.topic}"

User feedback for improvement: {feedback}

Requirements:
- Each query should be specific and focused
- Queries should cover different angles (technical, historical, current developments, applications, key players, future trends, etc.)
- Use terms that would return high-quality, authoritative sources
- Each query should be 3-10 words long
- Return ONLY the queries, one per line, without numbering or bullet points
- Incorporate the user's feedback above

Topic: {self.topic}"""
        else:
            query_prompt = f"""Generate 8 different comprehensive search queries for researching the topic: "{self.topic}"

Create a different set of queries than before, exploring alternative angles and perspectives.

Requirements:
- Each query should be specific and focused
- Queries should cover different angles (technical, historical, current developments, applications, key players, future trends, etc.)
- Use terms that would return high-quality, authoritative sources
- Each query should be 3-10 words long
- Return ONLY the queries, one per line, without numbering or bullet points

Topic: {self.topic}"""

        response = openai_model.basic_request(query_prompt)
        
        # Handle different response formats (same logic as generate_search_queries)
        if 'choices' in response:
            choice = response['choices'][0]
            if 'text' in choice:
                content = choice['text']
            elif 'message' in choice and 'content' in choice['message']:
                content = choice['message']['content']
            else:
                content = str(response)
        else:
            content = str(response)
        
        # Parse queries from response (same logic as generate_search_queries)
        queries = [line.strip() for line in content.split('\n') if line.strip() and not line.strip().startswith(('#', '-', '*', '1.', '2.'))]
        
        clean_queries = []
        for query in queries:
            clean_query = re.sub(r'^\d+[\.\)]\s*', '', query)
            clean_query = re.sub(r'^[-*]\s*', '', query)
            clean_query = clean_query.strip('"\'')
            
            if clean_query and len(clean_query) > 10:
                clean_queries.append(clean_query)
        
        return clean_queries[:8]
    
    async def get_approved_search_queries(self) -> List[str]:
        """Get user-approved search queries through iterative process"""
        print(f"\n🎯 Generating search queries for: {self.topic}")
        
        queries = self.generate_search_queries()
        
        while True:
            approved, feedback = self.get_user_approval(queries)
            
            if approved:
                print("\n✅ Queries approved! Proceeding with research...")
                return queries
            else:
                print("\n🔄 Regenerating search queries...")
                queries = self.regenerate_search_queries(feedback)
    
    async def generate_search_results(self, queries: List[str]) -> Dict[str, List[Dict]]:
        """Generate search results using approved queries"""
        from knowledge_storm.rm import SerpApiRM
        
        serpapi = SerpApiRM(serpapi_api_key=os.getenv('SERPAPI_KEY'), k=5)
        
        all_results = {}
        for query in queries:
            print(f"🔍 Searching: {query}")
            results = serpapi.forward(query)
            all_results[query] = results
            
        return all_results
    
    def generate_outline(self, search_results: Dict[str, List[Dict]]) -> str:
        """Generate comprehensive research outline"""
        from knowledge_storm.lm import OpenAIModel
        
        openai_model = OpenAIModel(
            model='gpt-4o-mini',
            api_key=os.getenv('OPENAI_API_KEY'),
            max_tokens=2000,
            temperature=0.7
        )
        
        # Compile search context
        context = "Search Results Summary:\n"
        for query, results in search_results.items():
            context += f"\nQuery: {query}\n"
            for i, result in enumerate(results[:3], 1):
                context += f"{i}. {result.get('title', 'No title')}\n"
                context += f"   {result.get('description', 'No description')[:200]}...\n"
        
        outline_prompt = f"""Based on the search results about "{self.topic}", create a comprehensive research outline that covers all major aspects of this topic.

Context from search results:
{context[:4000]}

Requirements:
- Create a detailed hierarchical outline with main sections and subsections
- Cover the most significant aspects and developments related to {self.topic}
- Organize information logically from introduction to conclusion
- Include sections on key players, current developments, applications, and future implications where relevant
- Ensure the outline is comprehensive and well-structured

Generate a detailed hierarchical outline covering the most important aspects of {self.topic}."""

        response = openai_model.basic_request(outline_prompt)
        # Handle different response formats
        if 'choices' in response:
            choice = response['choices'][0]
            if 'text' in choice:
                return choice['text']
            elif 'message' in choice and 'content' in choice['message']:
                return choice['message']['content']
        return str(response)
    
    def generate_article(self, outline: str, search_results: Dict[str, List[Dict]]) -> str:
        """Generate full research article"""
        from knowledge_storm.lm import OpenAIModel
        
        openai_model = OpenAIModel(
            model='gpt-4o-mini', 
            api_key=os.getenv('OPENAI_API_KEY'),
            max_tokens=4000,
            temperature=0.7
        )
        
        # Compile comprehensive context
        context = "Detailed Search Results:\n"
        for query, results in search_results.items():
            context += f"\n=== {query.upper()} ===\n"
            for i, result in enumerate(results, 1):
                context += f"\nSource {i}: {result.get('title', 'No title')}\n"
                context += f"URL: {result.get('url', 'No URL')}\n"
                context += f"Content: {result.get('description', 'No description')}\n"
                if 'snippets' in result:
                    for snippet in result['snippets'][:2]:
                        context += f"Snippet: {snippet[:300]}...\n"
        
        article_prompt = f"""Write a comprehensive research article about "{self.topic}". 

Use this outline structure:
{outline}

Base the article on these search results:
{context[:8000]}

Requirements:
- Write in professional academic style
- Include specific developments, dates, and achievements where available
- Reference key organizations, companies, or individuals mentioned in the search results
- Cover both current state and future implications
- Make it substantive (3000+ words)
- Use proper citations and references to the search results
- Ensure accuracy and provide balanced coverage

Generate a complete, well-researched article covering all significant aspects of {self.topic}."""

        response = openai_model.basic_request(article_prompt)
        # Handle different response formats
        if 'choices' in response:
            choice = response['choices'][0]
            if 'text' in choice:
                return choice['text']
            elif 'message' in choice and 'content' in choice['message']:
                return choice['message']['content']
        return str(response)

    def generate_polished_article(self, article: str) -> str:
        """Polish and enhance the article"""
        from knowledge_storm.lm import OpenAIModel
        
        openai_model = OpenAIModel(
            model='gpt-4o-mini',
            api_key=os.getenv('OPENAI_API_KEY'), 
            max_tokens=4000,
            temperature=0.5
        )
        
        polish_prompt = f"""Polish and enhance this research article about "{self.topic}":

{article}

Improvements needed:
- Enhance readability and flow
- Add more specific technical details where appropriate
- Ensure proper structure with clear sections
- Add executive summary at the beginning
- Improve transitions between sections
- Verify accuracy and add disclaimers where needed
- Format with proper headers and structure

Return the polished, publication-ready version."""

        response = openai_model.basic_request(polish_prompt)
        # Handle different response formats
        if 'choices' in response:
            choice = response['choices'][0]
            if 'text' in choice:
                return choice['text']
            elif 'message' in choice and 'content' in choice['message']:
                return choice['message']['content']
        return str(response)
    
    def save_results(self, search_queries: List[str], search_results: Dict[str, List[Dict]], 
                    outline: str, article: str, polished_article: str) -> str:
        """Save all research outputs"""
        # Create output directory
        topic_dir = os.path.join(self.output_dir, self.sanitized_topic)
        os.makedirs(topic_dir, exist_ok=True)
        
        # Save approved search queries
        with open(os.path.join(topic_dir, "approved_search_queries.txt"), "w") as f:
            f.write(f"Approved search queries for: {self.topic}\n")
            f.write("=" * 50 + "\n\n")
            for i, query in enumerate(search_queries, 1):
                f.write(f"{i}. {query}\n")
        
        # Save search results
        with open(os.path.join(topic_dir, "raw_search_results.json"), "w") as f:
            json.dump(search_results, f, indent=2)
        
        # Save outline
        with open(os.path.join(topic_dir, "storm_gen_outline.txt"), "w") as f:
            f.write(outline)
        
        # Save article
        with open(os.path.join(topic_dir, "storm_gen_article.txt"), "w") as f:
            f.write(article)
        
        # Save polished article
        with open(os.path.join(topic_dir, "storm_gen_article_polished.txt"), "w") as f:
            f.write(polished_article)
        
        # Save metadata
        metadata = {
            "topic": self.topic,
            "sanitized_topic": self.sanitized_topic,
            "generated_at": datetime.now().isoformat(),
            "search_queries_count": len(search_queries),
            "search_results_count": len(search_results),
            "total_sources": sum(len(results) for results in search_results.values())
        }
        
        with open(os.path.join(topic_dir, "run_config.json"), "w") as f:
            json.dump(metadata, f, indent=2)
        
        return topic_dir
    
    async def generate_complete_report(self, auto_approve: bool = False) -> str:
        """Generate complete research report with user approval workflow"""
        print(f"🔬 Starting comprehensive research on: {self.topic}")
        
        # Step 1: Get approved search queries
        if auto_approve:
            search_queries = await self.get_auto_approved_search_queries()
        else:
            search_queries = await self.get_approved_search_queries()
        
        # Step 2: Search
        print("📊 Gathering search results...")
        search_results = await self.generate_search_results(search_queries)
        
        # Step 3: Outline
        print("📋 Generating research outline...")
        outline = self.generate_outline(search_results)
        
        # Step 4: Article
        print("📄 Writing comprehensive article...")
        article = self.generate_article(outline, search_results)
        
        # Step 5: Polish
        print("✨ Polishing final article...")
        polished_article = self.generate_polished_article(article)
        
        # Step 6: Save
        print("💾 Saving research outputs...")
        output_path = self.save_results(search_queries, search_results, outline, article, polished_article)
        
        print(f"✅ Complete research report generated!")
        print(f"📂 Results saved to: {output_path}")
        
        return output_path
    
    async def get_auto_approved_search_queries(self) -> List[str]:
        """Generate and auto-approve search queries"""
        print(f"\n🎯 Generating search queries for: {self.topic}")
        
        queries = self.generate_search_queries()
        
        print(f"\n📋 Generated search queries for: {self.topic}")
        print("=" * 60)
        for i, query in enumerate(queries, 1):
            print(f"{i:2}. {query}")
        print("=" * 60)
        print("✅ Auto-approving queries (--auto flag enabled)")
        
        return queries


async def main():
    """Main function with command line and interactive modes"""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Universal Research Report Generator')
    parser.add_argument('topic', nargs='*', help='Research topic (if not provided, runs in interactive mode)')
    parser.add_argument('--auto', action='store_true', help='Auto-approve search queries without user input')
    
    args = parser.parse_args()
    
    print("🎯 Universal Research Report Generator")
    print("=" * 50)
    
    # Determine topic and mode
    if args.topic:
        topic = " ".join(args.topic)
        auto_approve = args.auto
        
        print(f"📋 Research topic: {topic}")
        if auto_approve:
            print("🤖 Auto-approval mode enabled")
        else:
            print("👤 Manual approval mode (use --auto to skip approval)")
            
    else:
        # Interactive mode
        topic = input("Enter your research topic: ").strip()
        
        if not topic:
            print("❌ No topic provided. Exiting.")
            return
        
        # Confirm topic
        print(f"\n📋 Research topic: {topic}")
        confirm = input("Proceed with this topic? (y/n): ").strip().lower()
        
        if confirm not in ['y', 'yes']:
            print("Research cancelled.")
            return
        
        auto_approve = False  # Interactive mode never auto-approves
    
    # Generate research
    generator = ResearchGenerator(topic)
    output_path = await generator.generate_complete_report(auto_approve=auto_approve)
    
    # Show results
    print(f"\n🎯 RESEARCH COMPLETE!")
    print(f"📁 Output directory: {output_path}")
    
    # Display file contents summary
    files = [
        "approved_search_queries.txt",
        "storm_gen_outline.txt",
        "storm_gen_article_polished.txt",
        "raw_search_results.json"
    ]
    
    for filename in files:
        filepath = os.path.join(output_path, filename)
        if os.path.exists(filepath):
            print(f"\n📄 {filename}:")
            with open(filepath, 'r') as f:
                content = f.read()
                if filename.endswith('.json'):
                    print(f"   {len(json.loads(content))} search queries with results")
                else:
                    print(f"   {len(content)} characters, {len(content.split())} words")


if __name__ == "__main__":
    asyncio.run(main())