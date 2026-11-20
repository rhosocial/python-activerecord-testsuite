# DDL Feature Tests — immature

> **Status: immature. Backends must not import this group yet.**

This group covers the backend-independent `DDLSource` contract: what a model may
declare, how declarations derive into DDL statements, and the function-migration
mechanism. Its tests render statements and inspect declarations; they never create
tables. A directory-owned database exists only to obtain an adapted dialect for
version-gated probes.

The declaration surface and the derivation rules are still evolving. Importing
this group into a backend would pin that backend to a moving target, so no backend
should ship a bridge file for `feature/ddl` while this notice is here. Keep the
group local to the testsuite; revisit when the contract is declared stable.
