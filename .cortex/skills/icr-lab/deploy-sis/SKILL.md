---
name: icr-lab/deploy-sis
description: "Deploy ICR Lab to Snowflake Streamlit-in-Snowflake — validates config, tests connection, creates the Streamlit app object, and uploads files. Use when: deploying to Snowflake, publishing the app, shipping to production. Triggers: deploy sis, deploy snowflake, publish app, ship to snowflake, streamlit in snowflake, push to snowflake, release app."
---

# Deploy to Streamlit-in-Snowflake (SiS)

Deploy the ICR Lab application to Snowflake's Streamlit-in-Snowflake runtime.

## Prerequisites

- Snowflake connection configured (via `snow` CLI or connection.toml)
- Database, schema, and warehouse specified in `icr-lab.toml [deploy]`
- Required privileges: CREATE STREAMLIT, USAGE on warehouse

## Workflow

1. Validate `[deploy]` config in `icr-lab.toml`
2. Check Snowflake connectivity via `snow connection test`
3. Create or update the Streamlit app object
4. Upload application files to the stage
5. Verify deployment

## Configuration

Read from `icr-lab.toml`:
```toml
[deploy]
database = "MY_DB"
schema = "MY_SCHEMA"
warehouse = "MY_WH"
compute_pool = ""
connection = "default"
```

## Commands

```bash
# Test connection
snow connection test --connection {{connection}}

# Create Streamlit app
snow streamlit deploy --database {{database}} --schema {{schema}} --warehouse {{warehouse}}
```

## SiS Considerations

- SiS runs in a restricted environment — no outbound HTTP (lmstudio backend won't work)
- Use `backend.cortex` for live mode in SiS deployments
- The simulation backend always works (no external deps)
- File structure must be flat or use proper stage paths

## Routing

For detailed Streamlit-in-Snowflake development guidance, this skill routes to `$developing-with-streamlit-in-snowflake` for:
- Environment setup
- Session object usage
- Stage file management
- Snowpark integration patterns
