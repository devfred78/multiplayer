import pytest
import time
from multiplayer import GameServer, GameClient, ServerAdmin, GroupAdmin, Player, AuthenticationError, exceptions

def test_group_admin_set_persistent_players_enabled():
    server = GameServer(port=65455, admin_password="server_admin")
    server.start()
    time.sleep(1)
    try:
        admin = ServerAdmin(port=65455, admin_password="server_admin")
        res = admin.create_group('AdminGroup', admin_password='group_secret')
        group_id = res.group_id
        
        group_admin = GroupAdmin(group_id=group_id, port=65455, group_admin_password="group_secret")
        client = GameClient(port=65455)
        
        # 1. Par défaut, c'est activé (ou devrait l'être)
        res_create = client.create_account("Persist1", "pass1")
        assert res_create['name'] == "Persist1"
        
        # 2. Désactiver via GroupAdmin
        res_disable = group_admin.set_persistent_players_enabled(False)
        assert 'disabled' in res_disable['message']
        
        # 3. Tenter de créer un compte (devrait échouer)
        with pytest.raises(exceptions.ServerError) as excinfo:
            client.create_account("Persist2", "pass2")
        assert 'disabled' in str(excinfo.value)
        
        # 4. Réactiver via GroupAdmin
        res_enable = group_admin.set_persistent_players_enabled(True)
        assert 'enabled' in res_enable['message']
        
        # 5. Tenter de créer un compte (devrait réussir)
        res_create2 = client.create_account("Persist2", "pass2")
        assert res_create2['name'] == "Persist2"
            
    finally:
        server.stop()
