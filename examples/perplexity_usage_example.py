"""
Example usage of PerplexityRM with STORM

This example shows how to use Perplexity as a search engine for STORM.
You need to set PERPLEXITY_API_KEY environment variable or pass it directly.

Get your Perplexity API key from: https://www.perplexity.ai/settings/api
"""

import os
from knowledge_storm import STORMWikiRunnerArguments, STORMWikiRunner, STORMWikiLMConfigs
from knowledge_storm.lm import LitellmModel
from knowledge_storm.rm import PerplexityRM


def example_perplexity_usage():
    # Set up Perplexity search engine
    rm = PerplexityRM(
        perplexity_api_key=os.getenv("PERPLEXITY_API_KEY"),
        k=3,  # Number of search results
        model="sonar-pro",  # Perplexity model to use
    )
    
    # Example search
    query = "artificial intelligence recent developments"
    results = rm.forward(query)
    
    print(f"Search results for: {query}")
    for i, result in enumerate(results):
        print(f"\n{i+1}. {result['title']}")
        print(f"   URL: {result['url']}")
        print(f"   Description: {result['description'][:200]}...")


def example_storm_with_perplexity():
    """Example of using Perplexity with STORM for article generation"""
    
    # Configure language models (using Gemini as example)
    lm_configs = STORMWikiLMConfigs()
    gemini_kwargs = {
        "api_key": os.getenv("GEMINI_API_KEY"),
        "temperature": 1.0,
        "top_p": 0.9,
    }
    
    # Set up models
    conv_simulator_lm = LitellmModel(
        model="gemini/gemini-2.0-flash", max_tokens=500, **gemini_kwargs
    )
    article_gen_lm = LitellmModel(
        model="gemini/gemini-2.5-flash-lite-preview-06-17", max_tokens=700, **gemini_kwargs
    )
    
    lm_configs.set_conv_simulator_lm(conv_simulator_lm)
    lm_configs.set_question_asker_lm(conv_simulator_lm)
    lm_configs.set_outline_gen_lm(article_gen_lm)
    lm_configs.set_article_gen_lm(article_gen_lm)
    lm_configs.set_article_polish_lm(article_gen_lm)
    
    # Set up engine arguments
    engine_args = STORMWikiRunnerArguments(
        output_dir="./results/perplexity_example",
        max_conv_turn=3,
        max_perspective=3,
        search_top_k=3,
        max_thread_num=1,
    )
    
    # Set up Perplexity retrieval
    rm = PerplexityRM(
        perplexity_api_key=os.getenv("PERPLEXITY_API_KEY"),
        k=engine_args.search_top_k,
        model="sonar-pro",
    )
    
    # Create and run STORM
    runner = STORMWikiRunner(engine_args, lm_configs, rm)
    
    topic = "Quantum Computing Advances in 2024"
    print(f"Generating article about: {topic}")
    
    runner.run(
        topic=topic,
        do_research=True,
        do_generate_outline=True,
        do_generate_article=True,
        do_polish_article=True,
    )
    
    runner.post_run()
    runner.summary()


if __name__ == "__main__":
    print("=== Perplexity Search Example ===")
    example_perplexity_usage()
    
    print("\n\n=== STORM with Perplexity Example ===")
    print("Note: This requires both PERPLEXITY_API_KEY and GEMINI_API_KEY")
    # Uncomment the line below to run the full STORM example
    # example_storm_with_perplexity()