import asyncio
import os
import pytest

pytest.importorskip("dspy")
from knowledge_storm.storm_wiki.engine import STORMWikiRunner, STORMWikiRunnerArguments, STORMWikiLMConfigs
from knowledge_storm.rm import PerplexityRM
from knowledge_storm.lm import GoogleModel

async def test_multi_agent_integration():
    print("Testing multi-agent integration...")

    # Setup dummy arguments and configs
    args = STORMWikiRunnerArguments(output_dir="./temp_output")
    lm_configs = STORMWikiLMConfigs()
    # Assuming GoogleModel is a valid LM, replace with actual if needed
    lm_configs.set_conv_simulator_lm(GoogleModel(model="models/gemini-pro", max_tokens=500))
    lm_configs.set_question_asker_lm(GoogleModel(model="models/gemini-pro", max_tokens=500))
    lm_configs.set_outline_gen_lm(GoogleModel(model="models/gemini-pro", max_tokens=2000))
    lm_configs.set_article_gen_lm(GoogleModel(model="models/gemini-pro", max_tokens=700))
    lm_configs.set_article_polish_lm(GoogleModel(model="models/gemini-pro", max_tokens=4000))

    # Assuming PerplexityRM is a valid RM, replace with actual if needed
    rm = PerplexityRM(perplexity_api_key="dummy_key", k=3)

    runner = STORMWikiRunner(args, lm_configs, rm)

    topic = "The impact of AI on employment"

    # Run the knowledge curation module (which now uses the multi-agent system)
    information_table = await runner.run_knowledge_curation_module(topic=topic, do_research=True)

    print(f"Information table retrieved: {information_table}")
    print("Multi-agent integration test complete.")

    # Clean up dummy output directory
    if os.path.exists("./temp_output"):
        os.rmdir("./temp_output")

if __name__ == "__main__":
    asyncio.run(test_multi_agent_integration())
