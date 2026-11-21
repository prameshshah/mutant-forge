# Draft DIAG task (generated): earliest failure stage

Read the input file and the ordered solver messages. Report:

1. the earliest workflow stage that fails, and
2. the terminal symptom that ends the run.

Return `response.json` with exactly this shape:

{"claim": {"failure_stage": "<identifier>", "terminal_symptom": "<identifier>"},
 "evidence": [{"source_id": "solver_events", "observation": "<first failure>", "interpretation": "<what it shows>"},
              {"source_id": "solver_events", "observation": "<terminal message>", "interpretation": "<why it is downstream>"}]}

Allowed failure_stage values: {stages}
Allowed terminal_symptom values: {symptoms}

Give the first-failure evidence first and the terminal evidence second. Do not modify or run the input.
