import pytest
import time
from multiplayer import GameServer, GameClient, ServerAdmin, GroupAdmin, exceptions

def test_server_admin_control_persistent_players_global():
    server = GameServer(port=65455, admin_password="server_admin")
    server.start()
    time.sleep(1)
    try:
        admin = ServerAdmin(port=65455, admin_password="server_admin")
        client = GameClient(port=65455)
        
        # 1. Par défaut, c'est activé
        res_create = client.create_account("Persist1", "pass1")
        assert res_create['name'] == "Persist1"
        
        # 2. Désactiver globalement via ServerAdmin
        res_disable = admin.set_persistent_players_enabled(False)
        assert 'disabled' in res_disable['message']
        assert 'globally' in res_disable['message']
        
        # 3. Tenter de créer un compte (devrait échouer)
        with pytest.raises(exceptions.ServerError) as excinfo:
            client.create_account("PersistFail", "pass")
        assert 'disabled' in str(excinfo.value)
        
        # 4. Réactiver globalement
        res_enable = admin.set_persistent_players_enabled(True)
        assert 'enabled' in res_enable['message']
        assert 'globally' in res_enable['message']
        
        # 5. Tenter de créer un compte (devrait réussir)
        res_create2 = client.create_account("PersistSuccess", "pass")
        assert res_create2['name'] == "PersistSuccess"
        
        # 6. Vérifier que GroupAdmin n'a pas la méthode
        group_res = admin.create_group('TestGroup')
        group_id = group_res.group_id
        group_admin = GroupAdmin(group_id=group_id, port=65455)
        assert not hasattr(group_admin, 'set_persistent_players_enabled')
            
    finally:
        server.stop()
