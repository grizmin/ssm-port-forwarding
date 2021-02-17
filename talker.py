import time
import logging
import pexpect
import sys


# TODO: extract logic from SsmTalker to classes based on session_type. SsmTalker should remain only wrapper class. (reduces magic)

class SsmTalker():
    def __init__(self, instance_id, profile, region, logger_name=__name__, session_type='regular', **kwargs):
        self.__dict__.update(kwargs)    # instance attributes from kwargs, comes first to avoid shadowing
        self._instance_id = instance_id
        self._logger = logging.getLogger(logger_name)
        self._session_type = session_type
        # print(kwargs)
        getattr(self, f"{session_type}_connect")(instance_id, profile, region)  # init proper class based on session_type

    def regular_connect(self, instance_id, profile, region):
        command_args = [
            f"--profile {profile}",
            f"--region {region}",
            f"ssm start-session --target {instance_id} "
        ]
        command = f"aws {' '.join(command_args)}"
        # print(command)
        self._logger.debug(f"Spawning: {command}")
        self._child = pexpect.spawn(command, echo=False, encoding='utf-8', timeout=10)
        # self._child.logfile_read = sys.stderr
        self._logger.debug(f"PID: {self._child.pid}")

        self.wait_for_prompt()
        self._logger.debug(f"{self._child.before.strip()}")
        self.shell_prompt = self._child.after

        # Turn off input echo
        self._child.sendline('stty -echo')
        self.wait_for_prompt()

        # Change to home directory (SSM session starts in '/')
        self._child.sendline('cd')
        self.wait_for_prompt()

    def forwarding_connect(self, instance_id, profile, region):
        command_args = [
            f"--profile {profile}",
            f"--region {region}",
            f"ssm start-session --target {instance_id}",
            f"--document-name {self.document_name}",
            f"--parameters {self.parameters}"
        ]
        command = f"aws {' '.join(command_args)}"
        # print(command)

        self._logger.debug(f"Spawning: {command}")
        self._child = pexpect.spawn(command, echo=True, encoding='utf-8', timeout=10)

        # self._child.logfile_read = sys.stderr
        self._logger.debug(f"PID: {self._child.pid}")
        self._child.expect('Starting session with SessionId')
        self._logger.debug("Forwarding sesison started")

    def exit(self):
        self._logger.debug("Closing session")
        if self._session_type == 'regular':
            self._child.sendcontrol('c')
            time.sleep(0.5)
            self._child.sendline('exit')
        if self._session_type == 'port_forwarding':
            self._child.sendcontrol('c')
            self.child.expect('Exiting session with sessionId')
        try:
            self._child.expect(['Exiting session', pexpect.EOF])
        except (OSError, pexpect.exceptions.EOF):
            pass


    def wait_for_prompt(self):
        """
        As of now a typical SSM prompt is 'sh-4.2$ '
        """
        self._child.expect('sh.*\$ $')
