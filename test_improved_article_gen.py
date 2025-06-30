import os
import sys
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge_storm import STORMWikiLMConfigs, STORMWikiRunner, STORMWikiRunnerArguments
from knowledge_storm.lm import GoogleModel
from knowledge_storm.rm import PerplexityRM

# Load environment variables
load_dotenv()
load_dotenv('secrets.toml')

# Topic for testing
topic = "Renewable Energy Technologies"

# Initialize language models with increased limits
gemini_kwargs = {
    "temperature": 1.0,
    "top_p": 0.9,
}

# Set up language models with enhanced parameters
lm_configs = STORMWikiLMConfigs()
conv_simulator_lm = GoogleModel(model="models/gemini-2.0-flash", max_tokens=500, **gemini_kwargs)
question_asker_lm = GoogleModel(model="models/gemini-2.0-flash", max_tokens=500, **gemini_kwargs)
outline_gen_lm = GoogleModel(model="models/gemini-2.5-flash-lite-preview-06-17", max_tokens=2000, **gemini_kwargs)
article_gen_lm = GoogleModel(model="models/gemini-2.5-flash-lite-preview-06-17", max_tokens=4000, **gemini_kwargs)
article_polish_lm = GoogleModel(model="models/gemini-2.5-flash-lite-preview-06-17", max_tokens=6000, **gemini_kwargs)

lm_configs.set_conv_simulator_lm(conv_simulator_lm)
lm_configs.set_question_asker_lm(question_asker_lm)
lm_configs.set_outline_gen_lm(outline_gen_lm)
lm_configs.set_article_gen_lm(article_gen_lm)
lm_configs.set_article_polish_lm(article_polish_lm)

# Set up retriever
rm = PerplexityRM(perplexity_api_key=os.getenv("PERPLEXITY_API_KEY"), k=5)

# Runner arguments - improved settings
runner_args = STORMWikiRunnerArguments(
    output_dir="results/renewable_energy_improved",
    max_conv_turn=3,
    max_perspective=4,
    search_top_k=5,
    retrieve_top_k=8,
    max_thread_num=6,
    use_enhanced_outline=True,  # Enable enhanced outline generation
)

# Create and run STORM
storm_runner = STORMWikiRunner(runner_args, lm_configs, rm)
storm_runner.run(
    topic=topic,
    do_research=True,
    do_generate_outline=True,
    do_generate_article=True,
    do_polish_article=True,
    remove_duplicate=False,
)

storm_runner.post_run()

print(f"\nImproved article generation completed!")
print(f"Results saved to: {runner_args.output_dir}")
print("\nCheck the outline vs article coverage:")
print("- Outline: storm_gen_outline.txt")
print("- Article: storm_gen_article_polished.txt")