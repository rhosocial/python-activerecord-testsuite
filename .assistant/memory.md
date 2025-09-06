## Memory Management

This section details how the project assistant manages and utilizes its memory for long-term retention of information.

### Stored Facts:
- User-specific preferences (e.g., preferred coding style, common project paths).
- Explicitly requested facts by the user (e.g., "Remember that I like pineapple on pizza").

### Usage Guidelines:
- Information stored is concise and directly relevant to future interactions.
- Avoids storing conversational context that is only relevant for the current session.
- Does not store long, complex, or rambling pieces of text.

### Tool Interaction:
- The `save_information` tool is used to store facts.
- The assistant may ask for confirmation before storing information if its long-term relevance is unclear.
