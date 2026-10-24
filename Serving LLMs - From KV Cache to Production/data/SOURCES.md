# Sources and licences: data in this course

## Kubernetes JSON schemas (lesson 32)

Folder: `infra/schemas/v1.33.0-standalone-strict/` (three files), with the upstream licence in `infra/schemas/LICENSE`.

| File | Kind it checks |
| --- | --- |
| `deployment-apps-v1.json` | Deployment (apps/v1) |
| `service-v1.json` | Service (v1) |
| `poddisruptionbudget-policy-v1.json` | PodDisruptionBudget (policy/v1) |

- **Source:** https://github.com/yannh/kubernetes-json-schema, directory `v1.33.0-standalone-strict` (Kubernetes v1.33.0, strict mode).
- **Derived from:** the Kubernetes OpenAPI specification, converted to JSON Schema with openapi2jsonschema (upstream README, "Building the schemas yourself"). Kubernetes is Apache-2.0.
- **Licence:** Apache License, Version 2.0. The upstream LICENSE file reads: "Licensed under the Apache License, Version 2.0 (the "License");" and carries the copyright lines "Copyright (C) 2017 Gareth Rushgrove" and "Copyright (C) 2017 Yanh Hamon" (spelled as in the upstream file).
- **Changes:** none. The three files are copied as they are upstream.
- **Date copied into this course:** 2026-10-23.
- **SHA-256 checksums:**
  - `deployment-apps-v1.json`: 8a4163cd36194edf94abdedff96b5bd8f612f76818a2a3767b35d1c72b8a7868
  - `poddisruptionbudget-policy-v1.json`: da73f50ad0264d73f668eecaa9959da65afe2846602a7a5c8fd51f7799d6a258
  - `service-v1.json`: 8bf019854daed511e7c174896a898173fa65d88ec5937c687a37303d4cc9351b
