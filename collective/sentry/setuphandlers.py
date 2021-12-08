# -*- coding: utf-8 -*-
import logging
from collective.sentry.config import IS_PLONE_4
from collective.sentry.config import IS_PLONE_5
from Products.CMFPlone.interfaces import INonInstallable

from zope.interface import implementer


logger = logging.getLogger('collective.sentry.setuphandlers')


@implementer(INonInstallable)
class HiddenProfiles(object):  # pragma: no cover
    def getNonInstallableProfiles(self):
        """Do not show on Plone's list of installable profiles."""
        return [
            u"collective.sentry:plone4",
            u"collective.sentry:plone5",
        ]


def import_various(context):
    """
    Install the PwExpiryPlugin
    """
    if context.readDataFile("collective.sentry_various.txt") is None:
        return
    portal = context.getSite()
    ps = portal.portal_setup

    if IS_PLONE_4:
        profile = "profile-collective.sentry:plone4"
        ps.runAllImportStepsFromProfile(profile)

    if IS_PLONE_5:
        profile = "profile-collective.sentry:plone5"
        ps.runAllImportStepsFromProfile(profile)