# Failure taxonomy for AI output evaluation

The categories used to tag failed responses, why each matters, and how it is detected.

| Tag | What went wrong | Example | How the harness detects it |
|---|---|---|---|
| `MISSING_FACT` | The required fact or answer is absent or wrong. Covers wrong answers and hallucinated answers to unanswerable questions. | Asked for the capital of Australia, the model answers "Sydney". | `must_include` terms (with `/` alternatives) not found as whole words |
| `FORBIDDEN_CONTENT` | Content that was explicitly ruled out appears. Covers broken negative instructions and unsafe compliance. | "Do not use the word green" and the response says green. | `must_not_include` terms found |
| `FORMAT_VIOLATION` | The requested structure is not followed. | "JSON only" but the JSON is inside a code fence; 4 bullets when 3 were requested. | `format` rule: `json`, `bullets:N`, `numbered:N`, `one_sentence`, `number_only` |
| `TOO_LONG` | The length limit is exceeded. | "At most 25 words" and the answer is 28. | word count above `max_words` |
| `EMPTY` | No usable response. | Blank output or an error string. | whitespace-only response |
| `INCONSISTENT` | Repeated runs of the same prompt disagree on correctness. | One run answers 17:05, another 16:05. | pass/fail differs across runs (reported in the consistency section) |

## Why these checks are deterministic

Every check is a rule a person could verify by hand, so a result can be explained and reproduced. This is a deliberate trade-off:

- **Strength:** no hidden judge model, repeatable scores, easy to run in CI.
- **Limit:** rules cannot judge tone, reasoning quality or nuance. Those need human review or an LLM-as-judge step with its own validation. Rule-based checks are best used as a fast first pass that catches clear failures.

## Writing good test cases

1. One behaviour per case, so a failure points to a single cause.
2. State the constraint in the prompt exactly as it is checked ("answer with the number only").
3. Prefer `/` alternatives over exact strings (`17:05/5:05`) so correct answers phrased differently still pass.
4. Include unanswerable and trick prompts (`hallucination_trap`), not only easy factual ones.
5. Run important cases several times; a model that is right once and wrong once is not reliable.
