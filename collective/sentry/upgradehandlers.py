from collective.sentry.config import IS_PLONE_5


def upgrade_default_from_1_to_2(portal_setup):
    portal_setup.runImportStepFromProfile('profile-collective.sentry:default',
            'skins')


def upgrade_from_3_to_4(portal_setup):
    if IS_PLONE_5:
        profile = "profile-collective.sentry:plone5"
        portal_setup.runImportStepFromProfile(profile, 'plone.app.registry')
