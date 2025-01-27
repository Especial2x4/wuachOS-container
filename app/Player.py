
class Player:
    def __init__(self, user_id, username, first_name):
        self.user_id = user_id
        self.username = username
        self.first_name = first_name
        self.activo = True
        self.fichitas = 6

    def get_name(self):
        return self.username if self.username else self.first_name

    def get_status(self):
        return "Activo" if self.activo else "Hibernando"

    def get_fichitas(self):
        return self.fichitas

    def espiar(self):
        return f"Informe de {self.get_name()}:\nEstado: {self.get_status()}\nFichitas: {self.get_fichitas()}"

    
    def reducir_fichita(self):
        if self.fichitas > 0:
            self.fichitas -= 1

    def aumentar_fichita(self):
        self.fichitas += 1

    
    def hibernar(self):
        self.activo = False