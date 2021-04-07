import time
import logging
import pexpect
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class SMSession(ABC):
    @abstractmethod
    def exit(self):
        pass

    @abstractmethod
    def connect(self):
        pass


class ConsoleSMSession(SMSession):
    def __init__(self, instance_id: str, profile: str, region: str, **kwargs):
        self.__dict__.update(kwargs)
        self._instance_id = instance_id
        self.profile = profile
        self.region = region
        self.prompt = "sh.*\$ $"
        self.command = self.build_command(instance_id, profile, region)

    @property
    def prompt(self) -> str:
        """

        Returns:
            prompt string.

        """
        return self._prompt

    @prompt.setter
    def prompt(self, prompt):
        self._prompt = prompt

    def build_command(self, instance_id: str, profile: str, region: str) -> str:
        """

        Args:
            instance_id: AWS EC2 instance id.
            profile: AWS profile.
            region: AWS region.

        Returns:
            Command string

        """
        command_args = [f"--profile {profile}", f"--region {region}", "ssm start-session", f"--target {instance_id}"]
        command = f"aws {' '.join(command_args)}"
        return command

    def connect(self) -> None:
        """
        spawns pexpect subshell with command.
        """
        logger.debug(f"Spawning: {self.command}")
        self.child = pexpect.spawn(self.command, echo=False, encoding="utf-8", timeout=10)
        logger.debug(f"PID: {self.child.pid}")

        self.wait_for_prompt()
        logger.debug(f"{self.child.before.strip()}")
        self.shell_prompt = self.child.after

        # Turn off input echo
        self.child.sendline("stty -echo")
        self.wait_for_prompt()

        # Change to home directory (SSM session starts in '/')
        self.child.sendline("cd")
        self.wait_for_prompt()

    def exit(self) -> None:
        """
        Cleanup.
        """
        logger.debug("Closing Console session")
        self.child.sendcontrol("c")
        time.sleep(0.5)
        self.child.sendline("exit")
        try:
            self.child.expect(["Exiting session", pexpect.EOF])
        except (OSError, pexpect.exceptions.EOF):
            pass

    def wait_for_prompt(self) -> None:
        """
        As of now a typical SSM prompt is 'sh-4.2$ '
        """
        self.child.expect(self.prompt)


class ForwardingSMSession(SMSession):
    def __init__(self, instance_id, profile, region, **kwargs):
        self.__dict__.update(kwargs)
        self._instance_id = instance_id
        self.profile = profile
        self.region = region
        self.command = self.build_command(instance_id, profile, region)

    def build_command(self, instance_id, profile, region):

        command_args = [
            f"--profile {profile}",
            f"--region {region}",
            f"ssm start-session --target {instance_id}",
            f"--document-name {self.document_name}",
            f"--parameters {self.parameters}",
        ]
        command = f"aws {' '.join(command_args)}"
        return command

    def connect(self):
        logger.debug(f"Spawning: {self.command}")
        self.child = pexpect.spawn(self.command, echo=False, encoding="utf-8", timeout=10)
        logger.debug(f"PID: {self.child.pid}")

    def exit(self):
        logger.debug("Closing port forwarding session")
        self.child.sendcontrol("c")
        try:
            self.child.expect(["Exiting session", pexpect.EOF])
        except (OSError, pexpect.exceptions.EOF):
            pass
