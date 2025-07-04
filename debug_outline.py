#!/usr/bin/env python3
"""Debug script to test outline generation step by step"""

import json
import dspy
from knowledge_storm.storm_wiki.modules.storm_dataclass import StormInformationTable
from knowledge_storm.storm_wiki.modules.outline_generation import StormOutlineGenerationModule
from knowledge_storm.lm import LitellmModel

# Load a conversation log to test with
print("Loading conversation log...")
with open("./results/ai_employment/Impact_of_AI_on_employment/conversation_log.json", "r") as f:
    conversation_log = json.load(f)

print(f"Found {len(conversation_log)} conversations")

# Create information table from conversation log
information_table = StormInformationTable.from_conversation_log_file(
    "./results/ai_employment/Impact_of_AI_on_employment/conversation_log.json"
)

print(f"Information table has {len(information_table.conversations)} conversations")

# Check the dialogue turns
total_turns = 0
for persona, conv in information_table.conversations:
    print(f"\nPersona: {persona}")
    print(f"Number of turns: {len(conv)}")
    total_turns += len(conv)
    if conv and len(conv) > 0:
        print(f"First turn user utterance: {conv[0].user_utterance[:100]}...")
        print(f"First turn agent utterance: {conv[0].agent_utterance[:100]}...")

print(f"\nTotal dialogue turns: {total_turns}")

# Test the outline generation module
print("\n\nTesting outline generation...")

# Initialize a simple test LM
test_lm = LitellmModel(
    model="gpt-3.5-turbo",  # Using a simpler model for testing
    max_tokens=400,
    temperature=0.7
)

outline_gen_module = StormOutlineGenerationModule(outline_gen_lm=test_lm)

# Test the WriteOutline module directly
print("\nTesting WriteOutline module directly...")
write_outline = outline_gen_module.write_outline

# Get concatenated dialogue turns
concatenated_dialogue_turns = sum(
    [conv for (_, conv) in information_table.conversations], []
)
print(f"Total concatenated dialogue turns: {len(concatenated_dialogue_turns)}")

# Test with a smaller subset first
test_topic = "Impact of AI on employment"
test_dialogue_turns = concatenated_dialogue_turns[:5]  # Just first 5 turns

print(f"\nTesting with topic: {test_topic}")
print(f"Testing with {len(test_dialogue_turns)} dialogue turns")

# Debug the conversation format
if test_dialogue_turns:
    print("\nSample dialogue turn structure:")
    turn = test_dialogue_turns[0]
    print(f"User utterance: {turn.user_utterance[:100]}...")
    print(f"Agent utterance: {turn.agent_utterance[:100]}...")

# Try to generate outline
try:
    with dspy.settings.context(lm=test_lm):
        # First test draft outline generation
        print("\nGenerating draft outline...")
        draft_result = write_outline.draft_page_outline(topic=test_topic)
        print(f"Draft outline result: {draft_result.outline[:200]}...")
        
        # Now test full outline generation
        print("\nGenerating full outline...")
        result = write_outline(
            topic=test_topic,
            dlg_history=test_dialogue_turns,
            callback_handler=None
        )
        print(f"Full outline result: {result.outline[:200]}...")
        print(f"Old outline: {result.old_outline[:200]}...")
        
except Exception as e:
    print(f"Error during outline generation: {e}")
    import traceback
    traceback.print_exc()

print("\nDebug complete.")