#
# Copyright (c) 2018-2025 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#


import ipaddress
import sys
import subprocess  # nosec B404

import eventlet
from oslo_config import cfg
from oslo_log import log as logging
from oslo_service import systemd
from oslo_service import wsgi

import logging as std_logging

from fm.common.i18n import _
from fm.api import app
from fm.api import config

api_opts = [
    cfg.StrOpt('bind_host',
               default="0.0.0.0",
               help=_('IP address for fm api to listen')),
    cfg.IntOpt('bind_port',
               default=18002,
               help=_('listen port for fm api')),
    cfg.IntOpt('api_workers', default=2,
               help=_("number of api workers")),
    cfg.IntOpt('limit_max',
               default=2000,
               help='the maximum number of items returned in a single '
                    'response from a collection resource')
]


CONF = cfg.CONF


LOG = logging.getLogger(__name__)
eventlet.monkey_patch(os=False)


def _resolve_host_once(host, record_type):

    try:
        result = subprocess.run(  # nosec B603
            ["/usr/bin/dig", "+short", record_type, host],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
            check=False
        )
    except Exception as e:
        # Ignore IPv6 errors in IPv4 scenarios
        LOG.debug("Unexpected error resolving (%s) %s: %s", record_type, host, e)
        return None

    if result.returncode != 0:
        LOG.warning(
            "dig error for (%s) %s (code=%d): %s",
            record_type,
            host,
            result.returncode,
            (result.stderr.strip() if result.stderr else "")
        )
        return None

    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ipaddress.ip_address(line)
            return line
        except ValueError:
            continue
    return None


def _wait_for_host_dns_resolution(host, interval=1, retries=90):

    # just execute the DNS resolution for FQDN
    # i.e: ( controller-0.internal )
    if not host.endswith(".internal"):
        return

    LOG.info("Waiting for DNS resolution of %s (%d retries)...", host, retries)

    for attempt in range(1, retries + 1):
        ip = _resolve_host_once(host, "A")
        if not ip:
            ip = _resolve_host_once(host, "AAAA")
        if ip:
            LOG.info("DNS resolved %s -> %s", host, ip)
            return

        LOG.info("Attempt %d/%d failed to resolve %s", attempt, retries, host)

        if attempt < retries:
            eventlet.sleep(interval)

    LOG.warning("DNS did not resolve %s after %d retries", host, retries)


def main():

    config.init(sys.argv[1:])
    config.setup_logging()

    application = app.load_paste_app()

    CONF.register_opts(api_opts, 'api')

    host = CONF.api.bind_host
    port = CONF.api.bind_port
    workers = CONF.api.api_workers

    if workers < 1:
        LOG.warning("Wrong worker number, worker = %(workers)s", workers)
        workers = 1

    LOG.info("Server on http://%(host)s:%(port)s with %(workers)s",
             {'host': host, 'port': port, 'workers': workers})
    _wait_for_host_dns_resolution(host)
    systemd.notify_once()
    service = wsgi.Server(CONF, CONF.prog, application, host, port)

    app.serve(service, CONF, workers)

    LOG.debug("Configuration:")
    CONF.log_opt_values(LOG, std_logging.DEBUG)

    app.wait()


if __name__ == '__main__':
    main()
