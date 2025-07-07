Run AI collaboration between Claude and Gemini for issue: $ARGUMENTS

This command orchestrates a collaborative implementation where both Claude and Gemini:
1. Independently implement solutions for the same issue
2. Review each other's work objectively  
3. Decide on the best approach based on technical merit
4. Submit the optimal solution as a PR

Steps:

1. Parse issue number and fetch details
2. Set up parallel implementation branches
3. Have each AI implement independently
4. Conduct cross-reviews
5. Make collaborative decision on best approach
6. Implement chosen solution and create PR

The process ensures:
- Both perspectives are considered
- Objective technical evaluation
- Best solution regardless of source
- Full documentation of decision process

Example usage:
- `/collab 69` - Work on issue #69
- `/collab issue 42` - Work on issue #42