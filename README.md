# Endpoint Casebook

Reconstruct an endpoint incident from process, file and network telemetry. Pivot from a document viewer to its descendants, export an evidence timeline, and compare the result with a worked analyst report.

## Reproduce the case

Requires Python 3.11+. All examples use synthetic data and run locally with the standard library. Run from the repository root.

```sh
python casebook.py examples/endpoint.jsonl workstation-07 p-office --html case-output/timeline.html
```

Five events connect the viewer to a script, a staged file, a helper process and an outbound connection. Open `case-output/timeline.html` to inspect the timeline offline. [Read the worked investigation](CASE.md) for the evidence IDs, excluded observations and next collection steps.

## Design and limits

SQLite stores normalized events and their stable evidence IDs. A recursive CTE traces process-instance IDs within one host, follows time-consistent parent edges, then attaches events inside the selected window. The default window is 30 minutes from the root start. Ingest expects unique event IDs and unique process-start records per (host, process). PIDs alone cannot establish lineage. Missing starts, clock skew and agent gaps can hide activity. A network connection alone cannot identify its payload or establish exfiltration.

## Verification

```sh
python -m unittest discover -s tests -v
```

Tests assert the reconstructed case, rule out cross-host and pre-start evidence, exercise a bounded window, and verify that telemetry is escaped in HTML.
