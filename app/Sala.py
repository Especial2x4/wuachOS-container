
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

    def add_player(self, player):
        if player and player.user_id not in [p.user_id for p in self.players]:  # Verificar que player no sea None y no esté duplicado
            self.players.append(player)

    def get_players(self):
        return [player.get_name() for player in self.players]