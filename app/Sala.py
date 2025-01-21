
class Sala:
    def __init__(self, room_id):
        self.room_id = room_id
        self.active = False  # O el estado inicial que desees
        self.players = []

    def get_id(self):
        return self.room_id

    def get_active(self):
        return self.active

    def set_active(self, active):
        self.active = active

    def add_player(self, player_name):
        if player_name:  # Verificar que player_name no sea None
            self.players.append(player_name)

    def get_players(self):
        return self.players