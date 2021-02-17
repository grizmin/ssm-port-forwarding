from talker import SsmTalker
import random
import argparse
import botocore
import logging
import sys
from common import *
from time import sleep

# HOSTPORT = "10.243.9.78:22"
SPORT = random.randint(1025, 65535)
# LPORT = random.randint(1025, 65535)
logger_name = "pfwd"
logger = logging.getLogger()

def parse_args():
    """
    Parse command line arguments.
    """

    # parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, add_help=False)
    parser = argparse.ArgumentParser(add_help=False)

    group_general = add_general_parameters(parser)

    group_instance = parser.add_argument_group('Instance Selection')
    group_instance.add_argument('instance', nargs='?', help='Instance ID')
    group_network = parser.add_argument_group('Networking Options')
    group_network.add_argument('HOSTPORT', type=str, help='HOST:PORT')
    group_network.add_argument('--lport', '-l', type=str, default=random.randint(1025, 65535), help=f'local port')

    parser.description = 'Start IP tunnel to a given SSM instance'

    # Parse supplied arguments
    args = parser.parse_args()

    # If --version do it now and exit
    if args.show_version:
        show_version(args)

    return args

# arg.instance = 'i-01f08b41270e4ae3f'
# arg.profile = 'confer-test-oktaAdminDefenseRole'
# arg.region = 'us-east-1'

arg = parse_args()

def spawn_socat(sport, HOSTPORT):

    socat = SsmTalker(arg.instance, arg.profile, arg.region, logger_name=logger_name, session_type='regular')
    command = f"socat TCP-LISTEN:{SPORT},fork TCP:{HOSTPORT}"
    logger.debug(f"Spawning socat command: {command}")
    socat._child.sendline(command)

    return socat

def spawn_port_forwarding_ssm_session(lport, sport):

    pfwsession = SsmTalker(arg.instance, arg.profile, arg.region, logger_name=logger_name, session_type='forwarding', document_name='AWS-StartPortForwardingSession',
                           parameters=f'{{\\"portNumber\\":[\\"{sport}\\"],\\"localPortNumber\\":[\\"{lport}\\"]}}')

    # pfwsession._child.expect(f"Port {SPORT} opened for sessionId")

    return pfwsession

def main():

    args = parse_args()

    logger = configure_logging(logger_name, args.log_level)

    socat_session = pfw_session = None
    print(f"local port: {args.lport}")

    try:
        socat_session = spawn_socat(SPORT, args.HOSTPORT)
        sleep(2)
        pfw_session = spawn_port_forwarding_ssm_session(args.lport, SPORT)
        # pfw_session._child.expect(f"Port {SPORT} opened for sessionId")
        # print(f"before: {pfw_session._child.before}")
        # print(f"after: {pfw_session._child.after}")
        pfw_session._child.interact()
    except (botocore.exceptions.BotoCoreError,
            botocore.exceptions.ClientError) as e:
        logger.error(e)

    finally:
        if pfw_session:
            pfw_session.exit()
        if socat_session:
            socat_session.exit()

if __name__ == "__main__":
    main()

print('the end')

