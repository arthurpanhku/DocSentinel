# Design Review: ExampleCo Document Service

[DES-01] A browser sends `X-User-Id` directly to the document API. The API uses
that value as the account identity without a signed session or trusted gateway.

[DES-02] The API sends document metadata to an internal indexing service over
unencrypted HTTP on the cluster network. Metadata includes customer names and
document titles.

[DES-03] Object storage denies public access, and each document is encrypted at
rest with a managed key whose rotation is enabled.

[DES-04] Authorization checks bind each document ID to the authenticated tenant
before object storage is queried.
