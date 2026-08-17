from mythic import mythic


class MythicAPI:
    def __init__(self, username, password, server_ip, server_port):
        self.username = username
        self.password = password
        self.server_ip = server_ip
        self.server_port = server_port
        self.mythic_instance = None

    async def connect(self):
        try:
            self.mythic_instance = await mythic.login(
                username=self.username,
                password=self.password,
                server_ip=self.server_ip,
                server_port=self.server_port,
            )

            return {
                "success": True,
                "message": "Connected to Mythic successfully",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def _check_connection(self):
        if self.mythic_instance is None:
            raise RuntimeError("Not connected to Mythic")

    async def execute_shell_command(self, agent_id, command):
        try:
            self._check_connection()

            output = await mythic.issue_task_and_waitfor_task_output(
                self.mythic_instance,
                command_name="shell",
                parameters=command,
                callback_display_id=agent_id,
            )

            return {
                "success": True,
                "agent_id": agent_id,
                "command": command,
                "output": str(output),
            }

        except Exception as e:
            return {
                "success": False,
                "agent_id": agent_id,
                "command": command,
                "error": str(e),
            }

    async def read_file(self, agent_id, file_path):
        try:
            self._check_connection()

            output = await mythic.issue_task_and_waitfor_task_output(
                self.mythic_instance,
                command_name="cat",
                callback_display_id=agent_id,
                parameters={"path": file_path},
            )

            if isinstance(output, bytes):
                output = output.decode(errors="replace")
            else:
                output = str(output)

            return {
                "success": True,
                "agent_id": agent_id,
                "file_path": file_path,
                "output": output,
            }

        except Exception as e:
            return {
                "success": False,
                "agent_id": agent_id,
                "file_path": file_path,
                "error": str(e),
            }

    async def make_token(self, agent_id, username, password):
        try:
            self._check_connection()

            output = await mythic.issue_task_and_waitfor_task_output(
                self.mythic_instance,
                command_name="make_token",
                callback_display_id=agent_id,
                parameters={
                    "username": username,
                    "password": password,
                },
            )

            return {
                "success": True,
                "agent_id": agent_id,
                "output": str(output),
            }

        except Exception as e:
            return {
                "success": False,
                "agent_id": agent_id,
                "error": str(e),
            }

    async def execute_mimikatz(self, agent_id, mimikatz_command):
        try:
            self._check_connection()

            parameters = {
                "commands": [mimikatz_command]
            }

            output = await mythic.issue_task_and_waitfor_task_output(
                self.mythic_instance,
                command_name="mimikatz",
                callback_display_id=agent_id,
                parameters=parameters,
            )

            if isinstance(output, bytes):
                output = output.decode(errors="replace")
            else:
                output = str(output)

            return {
                "success": True,
                "agent_id": agent_id,
                "output": output,
            }

        except Exception as e:
            return {
                "success": False,
                "agent_id": agent_id,
                "error": str(e),
            }

    async def get_all_agents(self):
        try:
            self._check_connection()

            agents = await mythic.get_all_active_callbacks(
                self.mythic_instance
            )

            return {
                "success": True,
                "agents": agents,
            }

        except Exception as e:
            return {
                "success": False,
                "agents": [],
                "error": str(e),
            }

    async def upload_file(
        self,
        agent_id,
        filename,
        file_path,
        contents,
    ):
        try:
            self._check_connection()

            file_id = await mythic.register_file(
                mythic=self.mythic_instance,
                filename=filename,
                contents=contents,
            )

            status = await mythic.issue_task(
                mythic=self.mythic_instance,
                command_name="upload",
                parameters={
                    "remote_path": file_path,
                    "file": file_id,
                },
                callback_display_id=agent_id,
                wait_for_complete=True,
            )

            if status["status"] == "success":
                return {
                    "success": True,
                    "agent_id": agent_id,
                    "file": filename,
                    "remote_path": file_path,
                }

            return {
                "success": False,
                "agent_id": agent_id,
                "file": filename,
                "error": str(status),
            }

        except Exception as e:
            return {
                "success": False,
                "agent_id": agent_id,
                "file": filename,
                "error": str(e),
            }