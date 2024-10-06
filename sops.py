'''
sops renderer for saltstack
https://github.com/jwestfall69/saltstack-sops-renderer
'''
import logging
import os
import salt.utils.path
from salt.exceptions import SaltRenderError, TimedProcTimeoutError
from salt.utils.timed_subprocess import TimedProc
from subprocess import PIPE

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 5

__virtualname__ = "sops"

def _get_sops_cmd() -> list:
    '''
    return the sops command to run or raise an error
    '''
    sops_exec = salt.utils.path.which('sops')
    if not sops_exec:
        raise SaltRenderError('sops binary not found')

    sops_args = __salt__['config.get']('sops_args')
    if not sops_args:
        raise SaltRenderError('sops_args setting missing in salt-master\'s config')

    cmd = [sops_exec] + sops_args.split()
    return cmd

def _get_sops_env() -> dict:
    '''
    returns the environment variables to pass to sops or None
    '''
    sops_env = __salt__['config.get']('sops_env')
    if not sops_env:
        return None

    if not isinstance(sops_env, dict):
       raise SaltRenderError(f'sops_env setting is expected to be a dict, but it was a {type(sops_env)}')

    return sops_env

def render(sops_data, saltenv='base', sls='', argline='', **kwargs):

    if not isinstance(sops_data, str):
        sops_data = sops_data.read()

    cmd = _get_sops_cmd()
    proc = TimedProc(
        cmd,
        stdin=sops_data,
        stdout=PIPE,
        stderr=PIPE,
        timeout=__salt__['config.get']('sops_timeout', DEFAULT_TIMEOUT),
        with_communicate=True,
        env=_get_sops_env()
    )

    sops_error = proc.run()
    if sops_error:
        log.warning(f'sops rendering failed with exit code: {sops_error}')
        raise SaltRenderError(proc.stderr.decode(__salt_system_encoding__))

    return  proc.stdout.decode(__salt_system_encoding__)
