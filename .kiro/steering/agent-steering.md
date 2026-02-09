---
inclusion: always
---
<!------------------------------------------------------------------------------------
   Steering rules for keeping solutions simple and controlled
   Learn about inclusion modes: https://kiro.dev/docs/steering/#inclusion-modes
------------------------------------------------------------------------------------> 

# Simplicity and Control Guidelines

## Core Principles

1. **Simplicity First**: Always choose the simplest solution that solves the problem. Avoid over-engineering, unnecessary abstractions, or complex patterns when a straightforward approach works.

2. **Minimal Changes**: Make the smallest possible change to achieve the goal. Don't refactor unrelated code or add "nice to have" features unless explicitly requested.

3. **Use Existing Code**: Before creating anything new, thoroughly check if existing functions, classes, or patterns in the codebase can be reused or extended.

## File Creation Rules

- **NEVER create new files without explicit user approval**
- Before suggesting a new file, explain why it's necessary and ask for permission
- If a feature can be added to an existing file, do that instead
- Consolidate related functionality rather than splitting into multiple files

## Implementation Approach

- Start with the most direct solution, even if it's not "perfect"
- Avoid premature optimization
- Don't add error handling, logging, or validation beyond what's necessary
- Skip documentation, comments, or type hints unless they're critical or requested
- Don't create helper functions, utilities, or abstractions unless the code is actually repeated multiple times

## When Proposing Solutions

- Present the simplest option first
- If multiple approaches exist, briefly mention them but recommend the easiest one
- Explain trade-offs only if they significantly impact the solution
- Don't suggest improvements or enhancements unless asked

## What NOT to Do

- Don't create configuration files, constants files, or utility modules "for organization"
- Don't add testing infrastructure unless explicitly requested
- Don't refactor working code to make it "cleaner" or "more maintainable"
- Don't add features "while we're at it"
- Don't create interfaces, base classes, or design patterns unless complexity demands it