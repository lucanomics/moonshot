# Lazyweb local setup (Codex)

This repository can be used with the Lazyweb plugin in Codex.

## Local-only steps

1. Save your token in `~/.lazyweb/lazyweb_mcp_token`.
2. Add plugin source:
   `codex plugin marketplace add https://github.com/aboul3ata/lazyweb-skill`
3. Ensure Codex config has:

```toml
[plugins."lazyweb@lazyweb"]
enabled = true
```

4. Restart Codex.

## Verification

After restart, verify Lazyweb MCP tools include `lazyweb_health` and `lazyweb_search`.
