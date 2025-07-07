Collaborate with Gemini CLI to implement a solution for a GitHub issue: $ARGUMENTS

This command orchestrates both Claude and Gemini to work on the same issue, cross-review implementations, and submit the best solution.

Steps:

1. Parse the issue number from arguments
2. Create separate working branches for each AI
3. Have each AI independently implement a solution
4. Cross-review each implementation
5. Collaboratively decide on the best approach
6. Submit the chosen solution as a PR

Implementation:

```bash
# Parse issue number
ISSUE_NUM=$(echo "$ARGUMENTS" | grep -oE '[0-9]+' | head -1)
if [ -z "$ISSUE_NUM" ]; then
    echo "Error: Please provide an issue number"
    exit 1
fi

# Get issue details
echo "=== Fetching Issue #$ISSUE_NUM ==="
gh issue view $ISSUE_NUM

# Create timestamp for unique branch names
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create Claude's branch
echo -e "\n=== Creating Claude's working branch ==="
git checkout -b claude-issue-$ISSUE_NUM-$TIMESTAMP
CLAUDE_BRANCH=$(git branch --show-current)

# Claude's implementation
echo -e "\n=== Claude implementing solution for issue #$ISSUE_NUM ==="
echo "Analyzing issue requirements and implementing solution..."
# [Claude implements here based on issue requirements]

# Save Claude's approach summary
cat > .claude_approach.md << 'EOF'
# Claude's Implementation Approach

## Key Design Decisions
[Claude fills this in during implementation]

## Trade-offs
[Claude documents trade-offs]

## Technical Highlights
[Claude notes key technical aspects]
EOF

# Commit Claude's work
git add -A
git commit -m "feat: Claude's implementation for issue #$ISSUE_NUM

Implemented by Claude Code addressing the requirements in issue #$ISSUE_NUM"

# Create Gemini's branch
echo -e "\n=== Creating Gemini's working branch ==="
git checkout main
git checkout -b gemini-issue-$ISSUE_NUM-$TIMESTAMP
GEMINI_BRANCH=$(git branch --show-current)

# Gemini's implementation
echo -e "\n=== Gemini implementing solution for issue #$ISSUE_NUM ==="
gemini -p "You are working on GitHub issue #$ISSUE_NUM. Here are the requirements:
$(gh issue view $ISSUE_NUM)

Implement a complete solution for this issue. Focus on:
1. Clean, maintainable code
2. Comprehensive error handling
3. Good test coverage
4. Performance considerations

After implementing, create a file called .gemini_approach.md documenting your key design decisions, trade-offs, and technical highlights."

# Wait for Gemini to complete (or simulate with sleep)
sleep 2

# Commit Gemini's work
git add -A
git commit -m "feat: Gemini's implementation for issue #$ISSUE_NUM

Implemented by Gemini CLI addressing the requirements in issue #$ISSUE_NUM"

# Cross-review phase
echo -e "\n=== Cross-Review Phase ==="

# Claude reviews Gemini's work
echo -e "\n--- Claude reviewing Gemini's implementation ---"
git checkout $CLAUDE_BRANCH
git diff main..$GEMINI_BRANCH > gemini_changes.diff

echo "Reviewing Gemini's implementation..."
# [Claude analyzes Gemini's code and approach]

cat > claude_review_of_gemini.md << 'EOF'
# Claude's Review of Gemini's Implementation

## Strengths
[Claude identifies strengths]

## Potential Improvements
[Claude suggests improvements]

## Comparison with My Approach
[Claude compares objectively]

## Overall Assessment
[Claude provides assessment]
EOF

# Gemini reviews Claude's work
echo -e "\n--- Gemini reviewing Claude's implementation ---"
git checkout $GEMINI_BRANCH
git diff main..$CLAUDE_BRANCH > claude_changes.diff

gemini -p "Review the implementation in claude_changes.diff for issue #$ISSUE_NUM. Compare it with your implementation. Create a file gemini_review_of_claude.md with:
1. Strengths of Claude's approach
2. Potential improvements
3. Objective comparison with your approach
4. Overall assessment

Be objective and focus on technical merit."

sleep 2

# Collaborative decision
echo -e "\n=== Collaborative Decision Phase ==="

# Create decision branch
git checkout main
git checkout -b pr-issue-$ISSUE_NUM-$TIMESTAMP

# Analyze both implementations
echo -e "\n--- Making collaborative decision ---"

cat > decision_matrix.md << 'EOF'
# Implementation Decision Matrix for Issue #$ISSUE_NUM

## Evaluation Criteria
1. Code Quality & Maintainability
2. Test Coverage
3. Performance
4. Error Handling
5. Adherence to Requirements
6. Innovation/Elegance

## Claude's Implementation
[Scores and rationale]

## Gemini's Implementation
[Scores and rationale]

## Hybrid Approach Opportunities
[Can we combine best aspects?]

## Final Decision
[Which implementation or hybrid to use]

## Rationale
[Detailed reasoning for decision]
EOF

# Let both AIs contribute to the decision
echo "Claude and Gemini collaborating on final decision..."

# Gemini's input on decision
gemini -p "Based on the cross-reviews and both implementations for issue #$ISSUE_NUM, help complete the decision_matrix.md. Consider:
- Technical merit of each approach
- Which solution better addresses the issue requirements
- Opportunities to combine best aspects of both
- Make an objective recommendation

Be fair and focus on what's best for the project."

sleep 2

# Claude finalizes decision and implements chosen approach
echo -e "\n--- Implementing chosen solution ---"
# [Claude implements the decided approach, potentially combining best aspects]

# Create final PR
echo -e "\n=== Creating Pull Request ==="

# Ensure all changes are committed
git add -A
git commit -m "feat: Collaborative implementation for issue #$ISSUE_NUM

This implementation represents the best approach after:
- Independent implementations by Claude and Gemini
- Cross-review of both approaches
- Collaborative decision on optimal solution

Closes #$ISSUE_NUM"

# Create PR with detailed description
PR_BODY="## Summary

This PR implements a solution for #$ISSUE_NUM through a collaborative AI process.

## Implementation Process

1. **Independent Development**: Both Claude and Gemini created separate implementations
2. **Cross-Review**: Each AI reviewed the other's approach
3. **Collaborative Decision**: Best approach selected based on technical merit
4. **Final Implementation**: Chosen solution implemented with potential improvements

## Technical Approach

[Summary of chosen approach]

## Key Features

[List key features implemented]

## Testing

[Describe testing approach]

## Decision Rationale

See \`decision_matrix.md\` for detailed comparison and decision process.

## Reviews

- Claude's review: \`claude_review_of_gemini.md\`
- Gemini's review: \`gemini_review_of_claude.md\`

---
*This PR was created through Claude-Gemini collaboration*"

gh pr create --title "fix: Collaborative solution for issue #$ISSUE_NUM" \
    --body "$PR_BODY" \
    --label "collaborative-ai"

# Cleanup
echo -e "\n=== Cleanup ==="
echo "Branches created:"
echo "- $CLAUDE_BRANCH"
echo "- $GEMINI_BRANCH" 
echo "- pr-issue-$ISSUE_NUM-$TIMESTAMP"
echo ""
echo "PR created! The collaborative implementation is ready for human review."
```

This command orchestrates a collaborative process where both AIs:
1. Work independently on the same issue
2. Review each other's work objectively
3. Make a joint decision on the best approach
4. Submit a PR with full documentation of the process