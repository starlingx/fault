#
# Copyright (c) 2018, 2022 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#


import sys
import pbr.version
from oslo_config import cfg
from oslo_log import log as logging
from keystoneauth1 import loading as ks_loading
from fm.api import hooks

LOG = logging.getLogger(__name__)

sysinv_group = cfg.OptGroup(
    'sysinv',
    title='Sysinv Options',
    help="Configuration options for the platform service")

sysinv_opts = [
    cfg.StrOpt('catalog_info',
               default='platform:sysinv:internalURL',
               help="Service catalog Look up info."),
    cfg.StrOpt('os_region_name',
               default='RegionOne',
               help="Region name of this node. It is used for catalog lookup"),
]

version_info = pbr.version.VersionInfo('fm')

fm_opts = [
    cfg.StrOpt('event_log_max_size',
               default='4000',
               help="the max size of event_log"),
]

# Pecan Application Configurations
app = {
    'root': 'fm.api.controllers.root.RootController',
    'modules': ['fm.api'],
    'hooks': [
        hooks.ContextHook(),
        hooks.DBHook(),
        hooks.AuditLogging(),
    ],
    'acl_public_routes': [
        '/',
        '/v1',
    ],
}


def init(args, **kwargs):
    cfg.CONF.register_group(sysinv_group)
    cfg.CONF.register_opts(sysinv_opts, group=sysinv_group)
    ks_loading.register_session_conf_options(cfg.CONF,
                                             sysinv_group.name)
    logging.register_options(cfg.CONF)
    cfg.CONF.register_opts(fm_opts)
    cfg.CONF(args=args, project='fm',
             version='%%(prog)s %s' % version_info.release_string(),
             **kwargs)


def setup_logging():
    """Sets up the logging options for a log with supplied name."""
    extra_log_level_defaults = ['eventlet.wsgi.server=WARN']
    logging.set_defaults(default_log_levels=logging.get_default_log_levels() +
                         extra_log_level_defaults)
    logging.setup(cfg.CONF, "fm")
    LOG.debug("Logging enabled!")
    LOG.debug("%(prog)s version %(version)s",
              {'prog': sys.argv[0],
               'version': version_info.release_string()})
    LOG.debug("command line: %s", " ".join(sys.argv))


def get_max_event_log():
    return cfg.CONF.event_log_max_size
