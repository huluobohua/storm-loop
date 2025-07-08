#!/bin/bash

# AI Collaboration Script for GitHub Issues
# This script orchestrates Claude and Gemini to work together on implementing solutions

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse issue number
ISSUE_NUM=$(echo "$1" | grep -oE '[0-9]+' | head -1)
if [ -z "$ISSUE_NUM" ]; then
    echo -e "${RED}Error: Please provide an issue number${NC}"
    echo "Usage: $0 <issue-number>"
    exit 1
fi

echo -e "${BLUE}=== AI Collaboration for Issue #$ISSUE_NUM ===${NC}"

# Get issue details
echo -e "\n${YELLOW}Fetching issue details...${NC}"
ISSUE_DETAILS=$(gh issue view $ISSUE_NUM)
echo "$ISSUE_DETAILS"

# Create timestamp for unique identification
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
WORK_DIR=".ai_collab_$ISSUE_NUM_$TIMESTAMP"
mkdir -p "$WORK_DIR"

# Save issue details for reference
echo "$ISSUE_DETAILS" > "$WORK_DIR/issue_details.txt"

# Create branches
MAIN_BRANCH=$(git branch --show-current)
CLAUDE_BRANCH="claude-issue-$ISSUE_NUM-$TIMESTAMP"
GEMINI_BRANCH="gemini-issue-$ISSUE_NUM-$TIMESTAMP"
FINAL_BRANCH="pr-issue-$ISSUE_NUM-collab"

# Function to create implementation prompt
create_implementation_prompt() {
    cat << EOF
You are tasked with implementing a solution for GitHub issue #$ISSUE_NUM.

Issue Details:
$ISSUE_DETAILS

Requirements:
1. Implement a complete, production-ready solution
2. Include comprehensive error handling
3. Write clean, maintainable code following project conventions
4. Add appropriate tests
5. Document your design decisions

After implementing, create a file called .ai_approach.md with:
- Key design decisions and rationale
- Trade-offs considered
- Technical highlights
- Performance considerations
- Testing strategy
EOF
}

# Claude's Implementation
echo -e "\n${BLUE}=== Claude's Implementation Phase ===${NC}"
git checkout -b "$CLAUDE_BRANCH"

echo -e "${YELLOW}Claude is implementing...${NC}"
# Claude will implement based on the issue (this is where Claude actually codes)
# Save approach documentation
cat > "$WORK_DIR/claude_approach.md" << 'EOF'
# Claude's Implementation Approach for Issue #$ISSUE_NUM

## Design Philosophy
[To be filled by Claude during implementation]

## Key Components
[To be filled by Claude during implementation]

## Technical Decisions
[To be filled by Claude during implementation]

## Testing Strategy
[To be filled by Claude during implementation]
EOF

# Placeholder for Claude's actual implementation
echo -e "${GREEN}Claude: I'll implement the solution now...${NC}"
# [Claude implements here]

# Gemini's Implementation
echo -e "\n${BLUE}=== Gemini's Implementation Phase ===${NC}"
git checkout "$MAIN_BRANCH"
git checkout -b "$GEMINI_BRANCH"

echo -e "${YELLOW}Invoking Gemini...${NC}"
IMPL_PROMPT=$(create_implementation_prompt)

# Call Gemini CLI
gemini -p "$IMPL_PROMPT

Focus on creating a robust, scalable solution. Save your approach details in $WORK_DIR/gemini_approach.md"

# Cross-Review Phase
echo -e "\n${BLUE}=== Cross-Review Phase ===${NC}"

# Claude reviews Gemini
echo -e "\n${YELLOW}Claude reviewing Gemini's implementation...${NC}"
git checkout "$CLAUDE_BRANCH"
git diff "$MAIN_BRANCH".."$GEMINI_BRANCH" > "$WORK_DIR/gemini_changes.diff"

# Gemini reviews Claude  
echo -e "\n${YELLOW}Gemini reviewing Claude's implementation...${NC}"
git checkout "$GEMINI_BRANCH"
git diff "$MAIN_BRANCH".."$CLAUDE_BRANCH" > "$WORK_DIR/claude_changes.diff"

gemini -p "Review Claude's implementation in $WORK_DIR/claude_changes.diff for issue #$ISSUE_NUM.

Create a review file $WORK_DIR/gemini_review.md with:
1. Strengths of the approach
2. Areas for improvement
3. Comparison with your implementation
4. Technical merit assessment

Be objective and constructive."

# Decision Phase
echo -e "\n${BLUE}=== Collaborative Decision Phase ===${NC}"

# Create decision criteria
cat > "$WORK_DIR/decision_criteria.md" << 'EOF'
# Decision Criteria for Issue #$ISSUE_NUM

## Evaluation Dimensions
1. **Code Quality** (0-10)
   - Readability
   - Maintainability
   - Following project conventions

2. **Completeness** (0-10)
   - Addresses all requirements
   - Edge case handling
   - Error handling

3. **Performance** (0-10)
   - Algorithmic efficiency
   - Resource usage
   - Scalability

4. **Testing** (0-10)
   - Test coverage
   - Test quality
   - Edge case coverage

5. **Innovation** (0-10)
   - Creative solutions
   - Elegant design
   - Future extensibility

## Scoring
- Claude's Implementation: [To be scored]
- Gemini's Implementation: [To be scored]

## Decision
[Final decision and rationale]
EOF

# Collaborative decision
echo -e "${YELLOW}Making collaborative decision...${NC}"

gemini -p "Based on both implementations and reviews for issue #$ISSUE_NUM:
- Claude's approach: $WORK_DIR/claude_approach.md
- Gemini's approach: $WORK_DIR/gemini_approach.md
- Reviews: $WORK_DIR/claude_review.md and $WORK_DIR/gemini_review.md

Complete the decision matrix in $WORK_DIR/decision_criteria.md
Recommend whether to use Claude's, Gemini's, or a hybrid approach.
Be objective and focus on technical merit."

# Final Implementation
echo -e "\n${BLUE}=== Final Implementation Phase ===${NC}"
git checkout "$MAIN_BRANCH"
git checkout -b "$FINAL_BRANCH"

echo -e "${YELLOW}Implementing chosen solution...${NC}"
# [Implement the decided approach]

# Create comprehensive PR
echo -e "\n${BLUE}=== Creating Pull Request ===${NC}"

# Generate PR body
cat > "$WORK_DIR/pr_body.md" << EOF
## Summary

This PR implements a solution for #$ISSUE_NUM through AI collaboration between Claude and Gemini.

## Implementation Process

### 1. Independent Development
- **Claude's Branch**: \`$CLAUDE_BRANCH\`
- **Gemini's Branch**: \`$GEMINI_BRANCH\`

Both AIs independently analyzed the requirements and implemented complete solutions.

### 2. Cross-Review
Each AI reviewed the other's implementation, providing objective technical assessment.

### 3. Collaborative Decision
Based on defined criteria, the best approach was selected:
- See \`$WORK_DIR/decision_criteria.md\` for detailed scoring

### 4. Final Implementation
The chosen approach was implemented in this PR.

## Technical Details

[Summary of the chosen implementation approach]

## Testing

[Description of test coverage]

## Performance Considerations

[Any performance optimizations or considerations]

## Documentation

All collaboration artifacts are preserved in \`$WORK_DIR/\`:
- \`issue_details.txt\` - Original issue
- \`claude_approach.md\` - Claude's design decisions  
- \`gemini_approach.md\` - Gemini's design decisions
- \`*_review.md\` - Cross-review documents
- \`decision_criteria.md\` - Decision matrix and rationale

---
*This PR was created through Claude-Gemini collaboration using ai-collaborate.sh*
EOF

# Create the PR
PR_BODY=$(cat "$WORK_DIR/pr_body.md")
gh pr create \
    --title "feat: [AI-Collab] Solution for issue #$ISSUE_NUM" \
    --body "$PR_BODY" \
    --label "ai-collaboration"

echo -e "\n${GREEN}=== Collaboration Complete ===${NC}"
echo -e "Work artifacts saved in: ${BLUE}$WORK_DIR/${NC}"
echo -e "Branches created:"
echo -e "  - ${YELLOW}$CLAUDE_BRANCH${NC}"
echo -e "  - ${YELLOW}$GEMINI_BRANCH${NC}"
echo -e "  - ${YELLOW}$FINAL_BRANCH${NC}"
echo -e "\n${GREEN}PR created successfully!${NC}"