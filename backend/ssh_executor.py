import paramiko
import socket
from io import StringIO


class SSHExecutor:
    def __init__(self):
        self.client = None

    def connect(
        self,
        hostname,
        port,
        username,
        password=None,
        ssh_key=None,
        passphrase=None,
        auth_method="password",
    ):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connect_kwargs = {
            "hostname": hostname,
            "port": port,
            "username": username,
            "timeout": 10,
        }
        if auth_method == "password" and password:
            connect_kwargs["password"] = password
        elif auth_method in ("ssh_key", "ssh_key_passphrase") and ssh_key:
            key_file = None
            key_loaders = [
                paramiko.RSAKey,
                paramiko.Ed25519Key,
                paramiko.ECDSAKey,
                paramiko.DSSKey,
            ]
            is_key_content = "BEGIN" in ssh_key and "PRIVATE KEY" in ssh_key
            last_error = None
            for key_cls in key_loaders:
                try:
                    if is_key_content:
                        key_file = key_cls.from_private_key(
                            StringIO(ssh_key), password=passphrase
                        )
                    else:
                        key_file = key_cls.from_private_key_file(
                            ssh_key, password=passphrase
                        )
                    break
                except Exception as exc:
                    last_error = exc
                    continue
            if key_file is None and last_error is not None:
                raise last_error
            connect_kwargs["pkey"] = key_file
        self.client.connect(**connect_kwargs)

    def execute(self, command, timeout=30):
        if not self.client:
            raise RuntimeError("Not connected to SSH server")
        stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode("utf-8", errors="replace")
        error = stderr.read().decode("utf-8", errors="replace")
        result = output
        if error and exit_status != 0:
            result += f"\n[stderr]\n{error}"
        return {"output": result, "exit_status": exit_status}

    def close(self):
        if self.client:
            self.client.close()
            self.client = None

    @staticmethod
    def check_reachable(hostname, port, timeout=5):
        try:
            sock = socket.create_connection((hostname, port), timeout=timeout)
            sock.close()
            return True
        except (socket.timeout, socket.error, OSError):
            return False
