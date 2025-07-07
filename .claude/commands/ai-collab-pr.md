Orchestrate Claude and Gemini to collaboratively solve issue: $ARGUMENTS

This command manages a structured collaboration between Claude and Gemini to create the best possible solution for a GitHub issue.

Process Overview:
1. Both AIs independently analyze and implement solutions
2. Cross-review each other's implementations
3. Collaborative synthesis of the best approach
4. Submit optimal solution as PR

Steps:

1. **Setup Phase**
   - Parse issue number from arguments
   - Fetch and analyze issue requirements
   - Create working directories for each AI

2. **Independent Implementation Phase**
   - Claude implements solution in dedicated branch
   - Gemini implements solution in separate branch
   - Both document their approaches

3. **Cross-Review Phase**
   - Claude reviews Gemini's implementation
   - Gemini reviews Claude's implementation
   - Both provide objective technical assessments

4. **Synthesis Phase**
   - Compare implementations across multiple criteria
   - Identify best aspects of each approach
   - Decide on optimal solution (pure or hybrid)

5. **Final Implementation**
   - Implement the chosen approach
   - Comprehensive testing
   - Create PR with full documentation

6. **Documentation**
   - Implementation comparison matrix
   - Decision rationale
   - Cross-review summaries

Example usage:
```
/ai-collab-pr 69
/ai-collab-pr issue #42
/ai-collab-pr "implement testing framework for issue 69"
```

The command will:
- Ensure both AIs work from the same requirements
- Facilitate objective comparison of approaches
- Document the entire decision process
- Submit the technically superior solution
- Maintain full transparency in the selection process