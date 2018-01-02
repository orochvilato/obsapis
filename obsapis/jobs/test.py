definition = dict(
    name = __name__,
    active = True,
    type = 'cron',
    params = dict(hour=3,minute=33),
    description = "Test",
    notify_error = ['observatoireapi@yahoo.com'],
    notify_success = ['observatoireapi@yahoo.com']
    )

from obsapis.controllers.admin.updates.scrutins import updateScrutinsTexte
from obsapis.controllers.admin.updates.groupes import updateGroupesRanks
from obsapis.controllers.admin.updates.deputes import updateDeputesContacts,updateDeputesLieuNaissance
from obsapis.controllers.admin.imports.liensdossierstextes import import_liendossierstextes

def job(**kwargs):
    updateScrutinsTexte()
    updateGroupesRanks()
    updateDeputesContacts()
    updateDeputesLieuNaissance()
    import_liendossierstextes()
