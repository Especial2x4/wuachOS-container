
class Player:
    def __init__(self, user_id, username, first_name):
        self.user_id = user_id
        self.username = username
        self.first_name = first_name
        self.activo = True
        self.fichitas = 6

    def get_name(self):
        return self.username if self.username else self.first_name