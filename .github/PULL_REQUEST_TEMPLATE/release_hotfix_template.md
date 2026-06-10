---
name: "Release or Hotfix Pull Request"
about: Propose changes for a release (e.g., merging a release branch to main) or a critical hotfix.
title: "chore: Release vX.Y.Z"
labels: "release, hotfix"
assignees: ""
---

## Description

<!--
Please include a summary of the change.
For releases, summarize the key features, bug fixes, and breaking changes included.
For hotfixes, describe the critical issue being addressed.
-->

## Release/Hotfix Details

- **Target Version**: (e.g., `v1.2.0`)
- **Type**: (e.g., `Major Release`, `Minor Release`, `Patch Release`, `Security Hotfix`)
- **Key Changes**:
    - [ ] New Features (if applicable)
    - [ ] Bug Fixes (if applicable)
    - [ ] Breaking Changes (if applicable, with migration path)
    - [ ] Security Fixes (if applicable, with CVE)

## Related Issues/PRs

<!-- List any relevant issues or pull requests that this release/hotfix addresses or is dependent on. -->

## Breaking Change

<!--
Does this PR introduce a breaking change for a hotfix, or finalize breaking changes for a release?
- If YES, please describe the impact and migration path for existing applications.
- If NO, please indicate N/A.
-->

- [ ] Yes
- [ ] No
(If Yes, please describe the impact and migration path below):



## Testing

<!--
Please describe how the changes in this test suite have been verified.
As this is a test suite, its primary verification occurs when integrated
and run within the CI of dependent `rhosocial-activerecord` backend
projects or the core `python-activerecord` project.
-->

- [ ] All CI checks passed on the source branch of this repository.
- [ ] Verification has been confirmed through CI runs in dependent projects
      (e.g., `python-activerecord` or specific backend integrations).
      Please provide links to relevant CI runs if applicable.

**Test Plan:**
<!-- e.g., "Confirmed successful CI runs for `python-activerecord-mysql` and `python-activerecord-postgres` using this test suite version.", or "Executed `pytest` within a backend project using this test suite." -->


## Checklist

<!--
Go over all the following points, and put an `x` in all the boxes that apply.
-->

- [ ] My changes follow the project's [version control guidelines](./.claude/version_control.md) (especially for release and hotfix procedures).
- [ ] I have updated the `CHANGELOG.md` using `towncrier build` (for releases).
- [ ] All necessary documentation (e.g., release notes, migration guides) has been prepared or updated.
- [ ] I have confirmed all CI checks have passed on the target branch after merging (post-merge verification).

## Additional Notes

<!-- Any additional information, context, or questions for reviewers. -->
