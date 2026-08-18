# Development Review: ExampleCo Search API

[DEV-01] The search handler builds a SQL statement by interpolating the raw
`query` request parameter into the statement text before execution.

[DEV-02] Dependency versions are pinned, but vulnerability review is a manual
quarterly spreadsheet exercise. There is no continuous alerting for newly
disclosed CVEs affecting versions already deployed.

[DEV-03] The repository blocks commits containing known credential formats and
uses short-lived workload identity for CI publishing.

[DEV-04] Unit tests cover authorization failures and output encoding for search
results.
