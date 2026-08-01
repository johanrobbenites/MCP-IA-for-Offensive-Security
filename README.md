# Mythic MCP

A quick MCP demo for Mythic, allowing LLMs to pentest on our behalf!

## Requirements

1. uv
2. python3
3. Claude Desktop (or other MCP Client)

## Usage with Claude Desktop

To deploy this MCP Server with Claude Desktop, you'll need to edit your `claude_desktop_config.json` to add the following:

```
{
    "mcpServers": {
        "mythic_mcp": {
            "command": "/Users/xpn/.local/bin/uv",
            "args": [
                "--directory",
                "/full/path/to/mythic_mcp/",
                "run",
                "main.py",
                "mythic_admin",
                "mythic_admin_password",
                "localhost",
                "7443"
            ]
        }
    }
}
```

Once done, kick off Claude Desktop. There are sample prompts to show how to task the LLM, but really anything will work along the lines of:

```
You are an automated pentester, tasked with emulating a specific threat actor. The threat actor is APT31. Your objective is: Add a flag to C:\win.txt on DC01. Perform any required steps to meet the objective, using only techniques documented by the threat actor.

## AD Recon & Tools 🔧

This MCP includes helpers useful in Active Directory environments. Use them only on systems you are authorized to test.

- `execute_powershell(agent_id, script)` — Run an arbitrary PowerShell script on an agent. The script is encoded and executed with `-EncodedCommand`.
- `ad_recon(agent_id)` — Run common AD reconnaissance commands and return collated output (`whoami /all`, `net user /domain`, `net group /domain`, `nltest`, `net share`).
- `enum_domain_users(agent_id)` — Attempts to enumerate domain users using the `ActiveDirectory` module (falls back to `net user /domain`).
- `run_kerberoast(agent_id, rubeus_base64, args="kerberoast")` — Upload and execute Rubeus for Kerberoasting. Upload the `Rubeus.exe` binary base64-encoded and provide any additional arguments as needed.

**Caveat:** These tools perform potentially intrusive AD actions. Ensure you have written authorization before using them in any environment.
```
