# Deployment Review: ExampleCo Reporting Service

[DEP-01] The release image is promoted to production without a container or
infrastructure image vulnerability scan.

[DEP-02] Database backups are created nightly, but the team has never restored
one and has not measured recovery time or recovery-point objectives.

[DEP-03] Production credentials are injected from a managed secret store and
are absent from the image and deployment manifest.

[DEP-04] The service runs as a non-root user with a read-only root filesystem
and drops all Linux capabilities not required at runtime.
