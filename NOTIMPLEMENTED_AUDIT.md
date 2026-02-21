# synapse/ NotImplementedError audit

## Scope
- Directory audited: `synapse/`
- Pattern audited: `raise NotImplementedError` (including `raise NotImplementedError()` and attribute-call variants)

## Method
- Static AST walk over all `synapse/**/*.py` files to find `ast.Raise` nodes targeting `NotImplementedError`.
- Confirmed with ripgrep string scan for `NotImplementedError` references.

## Disposition by file
- `synapse/federation/sender/__init__.py`
  - **Classification:** informational comment only (not a raise site).
  - **Category:** N/A (neither A nor B).
- `synapse/http/federation/srv_resolver.py`
  - **Classification:** catches Twisted `DNSNotImplementedError` import/exception type; not a local `raise NotImplementedError` runtime gap.
  - **Category:** N/A (neither A nor B).

## Category summary
- **A) valid abstract interface:** 0 instances found.
- **B) concrete runtime gap:** 0 instances found.

## Outcome
- No runtime `raise NotImplementedError` paths exist under `synapse/` at this point.
- Added a regression check script at `tests/check_runtime_notimplemented.py` to prevent reintroduction of runtime `NotImplementedError` raises.
