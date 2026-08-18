# Testing Review: ExampleCo Administration API

[TST-01] The DAST plan covers public customer endpoints but explicitly excludes
the `/admin` API because the scanner cannot authenticate to that route.

[TST-02] A penetration test found an administrator authentication bypass rated
critical. The release plan defers the fix and any retest until after launch.

[TST-03] SAST runs on every pull request and blocks newly introduced high or
critical findings.

[TST-04] Test evidence includes the scanner version, configuration, timestamp,
and immutable report checksum.
