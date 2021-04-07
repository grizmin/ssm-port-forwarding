import click
import logging
import pexpect
import random
from ssmpfwd.helpers import configure_logging, verbose_debug_quiet, verify_plugin_version, print_version
from ssmpfwd.smsession import SMSession, ConsoleSMSession, ForwardingSMSession

logger = configure_logging("ssmpfwd", logging.WARN)

if not verify_plugin_version('1.2.54'):
    exit(1)


def spawn_socat(profile: str, region: str, instance: str, source_port: int, hostport: str) -> SMSession:
    """
    Creates regular sessions manager console session and executes socat.

    Args:
        profile: AWS profile.
        region:  AWS region.
        instance: AWS EC2 instance id.
        source_port: source port socat will listen on utility host.
        hostport: remote instance host:port.  Example: (10.1.2.3:123)

    Returns:
        Session Manager session
    """
    socat = ConsoleSMSession(instance, profile, region, source_port=source_port)
    socat.connect()
    command = f"socat TCP-LISTEN:{source_port},fork TCP:{hostport}"
    logger.debug(f"Spawning socat command: {command}")
    socat.child.sendline(command)

    return socat


def spawn_port_forwarding_ssm_session(profile: str, region: str, instance: str, lport: int,
                                      source_port: int) -> SMSession:
    """
    Creates port forwarding Sessions manager session

    Args:
        profile: AWS profile.
        region:  AWS region.
        instance: AWS EC2 instance id.
        source_port: source port socat will listen on utility host.
        hostport: remote instance host:port.  Example: (10.1.2.3:123)
        lport: local port on the host, where this code is running.

    Returns:
        Session Manager session
    """
    pfwsession = ForwardingSMSession(instance, profile, region,
                     document_name='AWS-StartPortForwardingSession',
                     parameters=f'{{\\"portNumber\\":[\\"{source_port}\\"],\\"localPortNumber\\":[\\"{lport}\\"]}}')

    pfwsession.connect()
    return pfwsession


@click.group(chain=False)
@verbose_debug_quiet
@click.option('--version', is_flag=True, callback=print_version,
              expose_value=False, is_eager=False)
@click.pass_context
def cli(ctx: click.Context, *args, **kwargs):
    ctx.ensure_object(dict)
    ctx.obj.update(kwargs)


@cli.command("forward", help="Open remote port forwarding session")
@click.argument("UtilityHostId", type=click.STRING)
@click.argument("HOSTPORT", type=click.STRING)
@click.option("--lport", type=click.INT, default=random.randint(1025, 65535), help="Local port")
@click.option("--sport", type=click.INT, default=random.randint(1025, 65535), help="Source port")
@click.option("--profile", type=str, default="default", envvar='AWS_DEFAULT_PROFILE',
              help="Configuration profile from ~/.aws/{credentials,config}")
@click.option("--region", type=str, default="us-east-1", envvar='AWS_DEFAULT_REGION',
              help="AWS region")
@verbose_debug_quiet
@click.pass_context
def command_forward(ctx, *args, **kwargs):
    ctx.obj.update(kwargs)
    profile_name = ctx.obj.get("profile")
    region = ctx.obj.get("region")
    hostport = ctx.obj.get("hostport")
    utility_host_id = ctx.obj.get("utilityhostid")
    local_port = ctx.obj.get('lport')
    source_port = ctx.obj.get('sport')
    socat_session = pfw_session = None
    logger.info(f"local port: {local_port}")

    try:
        socat_session = spawn_socat(profile_name, region, utility_host_id, source_port, hostport)
        pfw_session = spawn_port_forwarding_ssm_session(profile_name, region, utility_host_id, local_port, source_port)
        click.secho("Press Ctrl+C to exit.", bold=True, fg="red")
        pfw_session.child.interact()

    except pexpect.exceptions.EOF as e:
        if 'The security token included in the request is expired' in e.value:
            print('Check your credentials. Security token has expired.')
        elif 'is not connected.' in e.value:
            print(f"Instance {utility_host_id} does not exist in region {region}.")
        else:
            logger.error(e)

    finally:
        if pfw_session:
            pfw_session.exit()
        if socat_session:
            socat_session.exit()
