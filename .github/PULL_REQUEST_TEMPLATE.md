## Description | 描述

**What does this PR do?** (fixes #issue if applicable)
本 PR 做了什么？（若关联 Issue 请写 fixes #编号）

Fixes #

## Plan | 实施计划

- [ ] Describe the bounded implementation steps and affected contracts.

## Security impact | 安全影响

Describe changes to trust boundaries, authentication, authorization, data, or
supply-chain behavior. Write `None` only when none apply.

## Risk and rollback | 风险与回滚

State failure modes, migration compatibility, and the concrete rollback path.

---

## Type of Change | 变更类型

-   [ ] Bug fix
-   [ ] New feature
-   [ ] Documentation update
-   [ ] Refactor / chore

---

## How to Verify | 如何验证

**Steps to test the change** (e.g. run tests, manual check).
验证步骤（如运行测试、手动检查）。

- [ ] Automated tests added or updated
- [ ] Negative/denied-path behavior verified where relevant

---

## Checklist | 检查项

-   [ ] Tests pass locally (`pytest`)
-   [ ] Frontend checks pass (`npm run check --prefix frontend`)
-   [ ] Generated contracts are current (`make contracts-check`)
-   [ ] Security boundaries and denied paths are covered where relevant
-   [ ] Docs/README updated if needed
-   [ ] No secrets or sensitive data in the diff
-   [ ] Database migrations include downgrade/rollback coverage where relevant
-   [ ] The submitter is not the sole approver for security-sensitive changes
