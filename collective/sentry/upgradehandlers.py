
def upgrade_default_from_1_to_2(portal_setup):
    portal_setup.runImportStepFromProfile('profile-collective.sentry:default',
            'skins')

