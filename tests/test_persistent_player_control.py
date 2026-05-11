import pytest
import time
from multiplayer import GameServer, GameClient, ServerAdmin, GroupAdmin, Player, AuthenticationError, exceptions

def test_server_admin_control_persistent_players():
    server = GameServer(port=65455, admin_password="server_admin")
    server.start()
    time.sleep(1)
    try:
        admin = ServerAdmin(port=65455, admin_password="server_admin")
        res = admin.create_group('AdminGroup', admin_password='group_secret')
        group_id = res.group_id
        
        client = GameClient(port=65455)
        
        # 1. Par défaut, c'est activé
        res_create = client.create_account("Persist1", "pass1")
        assert res_create['name'] == "Persist1"
        
        # 2. Désactiver globalement via ServerAdmin
        admin.set_persistent_players_enabled(False)
        with pytest.raises(exceptions.ServerError) as excinfo:
            client.create_account("PersistGlobalFail", "pass")
        assert 'disabled' in str(excinfo.value)
        
        # 3. Réactiver globalement
        admin.set_persistent_players_enabled(True)
        
        # 4. Désactiver pour le groupe via ServerAdmin
        res_disable = admin.set_persistent_players_enabled(False, group_id=group_id)
        assert 'disabled' in res_disable['message']
        
        # 5. Tenter de créer un compte pour ce groupe (devrait échouer)
        with pytest.raises(exceptions.ServerError) as excinfo:
            client.create_account("PersistGroupFail", "pass2", group_id=group_id)
        assert 'disabled' in str(excinfo.value)
        
        # 6. Vérifier que la création hors groupe fonctionne toujours
        res_create_outside = client.create_account("PersistOutside", "pass")
        assert res_create_outside['name'] == "PersistOutside"
        
        # 7. Réactiver pour le groupe via ServerAdmin
        res_enable = admin.set_persistent_players_enabled(True, group_id=group_id)
        assert 'enabled' in res_enable['message']
        
        # 8. Tenter de créer un compte pour ce groupe (devrait réussir)
        res_create2 = client.create_account("PersistGroupSuccess", "pass2", group_id=group_id)
        assert res_create2['name'] == "PersistGroupSuccess"
        
        # 9. Vérifier que GroupAdmin n'a plus la méthode (ou qu'elle échoue si appelée via _send_command directement)
        group_admin = GroupAdmin(group_id=group_id, port=65455, group_admin_password="group_secret")
        assert not hasattr(group_admin, 'set_persistent_players_enabled')
            
    finally:
        server.stop()
