---
name: Clerk compatibility
description: Why the managed Clerk integration uses a Python adapter and needs separate published-site verification.
---
Preserve the existing Flask/Jinja application when following Clerk guidance written for Express/React. Adapt the current canonical proxy semantics rather than migrating frameworks merely to match the examples.

**Why:** The published account form failed while preview worked: development bypasses the managed production proxy. A working preview alone therefore does not establish that published authentication works.

**How to apply:** Read the latest Clerk skill and canonical proxy before changing authentication. Test the Python adaptation with isolated upstream responses, then verify the published site after the user republishes. Do not change managed keys or DNS to repair missing proxy wiring.