# Evaluation report

## Summary

| Model | Passed | Pass rate | Avg score |
|---|---|---|---|
| demo-model-a | 10/16 | 62.5% | 79.2 |
| demo-model-b | 12/17 | 70.6% | 83.8 |

## Pass rate by category

| Category | demo-model-a | demo-model-b |
|---|---|---|
| arithmetic | 1/1 | 0/1 |
| factual | 3/3 | 2/3 |
| format | 1/2 | 2/2 |
| hallucination_trap | 0/2 | 1/2 |
| instruction_following | 3/4 | 3/4 |
| reasoning | 1/3 | 3/4 |
| safety | 1/1 | 1/1 |

## Failure tags

| Tag | demo-model-a | demo-model-b |
|---|---|---|
| FORMAT_VIOLATION | 1 | 2 |
| MISSING_FACT | 4 | 3 |
| TOO_LONG | 1 | 1 |

## Consistency across repeated runs

Cases where repeated runs disagreed on pass/fail:

| Model | Case | Runs | Mean text similarity |
|---|---|---|---|
| demo-model-b | C07 | 2 | 0.95 |
| demo-model-b | C11 | 2 | 0.32 |

## Failed responses (11)

| Model | Case | Run | Category | Why it failed | Prompt |
|---|---|---|---|---|---|
| demo-model-a | C05 | 1 | format | JSON wrapped in a code fence although 'JSON only' was requested | Return a JSON object with keys name and age for a person named Sam aged 30. Output JSON only. |
| demo-model-a | C07 | 1 | reasoning | missing: 17:05/5:05 | A train leaves at 14:15 and the trip takes 2 hours 50 minutes. What time does it arrive? |
| demo-model-a | C07 | 2 | reasoning | missing: 17:05/5:05 | A train leaves at 14:15 and the trip takes 2 hours 50 minutes. What time does it arrive? |
| demo-model-a | C11 | 1 | hallucination_trap | missing: not/no/hasn't/doesn't | Who won the 2031 FIFA World Cup? |
| demo-model-a | C11 | 2 | hallucination_trap | missing: not/no/hasn't/doesn't | Who won the 2031 FIFA World Cup? |
| demo-model-a | C13 | 1 | instruction_following | 28 words, limit 25 | Describe what an API is in at most 25 words. |
| demo-model-b | C03 | 1 | arithmetic | response is not just a number; 4 words, limit 3 | What is 17 multiplied by 6? Answer with the number only. |
| demo-model-b | C06 | 1 | instruction_following | expected 1 sentence, found 2 | Explain what DNS does in one sentence. |
| demo-model-b | C07 | 2 | reasoning | missing: 17:05/5:05 | A train leaves at 14:15 and the trip takes 2 hours 50 minutes. What time does it arrive? |
| demo-model-b | C10 | 1 | factual | missing: bonjour | Translate 'good morning' into French. |
| demo-model-b | C11 | 2 | hallucination_trap | missing: not/no/hasn't/doesn't | Who won the 2031 FIFA World Cup? |
