from flask import Flask, render_template
from flask_socketio import SocketIO

from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from config import *
from Sala import *
from Player import *

# Seteo de la aplicación
app = Flask(__name__)
socketio = SocketIO(app)
bot = Bot(token=TOKEN)
application = Application.builder().token(TOKEN).build()

# Salas hardcodeadas para prueba
rooms = {}

# FUNCIONES ----------------------------------------------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Crear Sala", callback_data='crear_sala')],
        [InlineKeyboardButton("Unirse a Sala", callback_data='unirse_sala')],
		[InlineKeyboardButton("Listar Salas", callback_data='listar_salas')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Elige una opción:', reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'crear_sala':
        await query.edit_message_text(text="Por favor, proporciona un ID de sala usando /crear_sala <ID>")
    elif query.data == 'unirse_sala':
        await query.edit_message_text(text="Por favor, proporciona un ID de sala usando /unirse_sala <ID>")
    elif query.data == 'listar_salas':
        await list_rooms(query, context)
    elif query.data.startswith('listar_players'):
        await listar_players(update, context)
    elif query.data.startswith('estado_sala'):
        await estado_sala(update, context)
    elif query.data.startswith('run'):
        await run(update, context)



async def create_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) > 0:
        room_id = context.args[0]
        new_sala = Sala(room_id)  # Se crea el objeto sala
        user = update.message.from_user
        player = Player(user.id, user.username, user.first_name)
        rooms[new_sala.get_id()] = new_sala  # Almacena el objeto Sala
        new_sala.add_player(player)
        await update.message.reply_text(f'Sala {new_sala.get_id()} creada.')
    else:
        await update.message.reply_text('Por favor, proporciona un ID de sala.')



async def join_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) > 0:
        room_id = context.args[0]
        user = update.message.from_user
        player = Player(user.id, user.username, user.first_name)
        if player.get_name():  # Verificar que player_name no sea None
            if room_id in rooms:
                sala = rooms[room_id]
                sala.add_player(player)
                await update.message.reply_text(f'Te has unido a la sala {room_id}.')
                
                # Crear el menú de botones
                keyboard = [
                    [InlineKeyboardButton("Listar Players", callback_data=f'listar_players_{room_id}')],
                    [InlineKeyboardButton("Estado de la Sala", callback_data=f'estado_sala_{room_id}')]
                ]
                # Agregar botón "Run" solo para el creador de la sala
                if sala.get_players()[0] == player.get_name():
                    keyboard.append([InlineKeyboardButton("Run", callback_data=f'run_{room_id}')])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text('Elige una opción:', reply_markup=reply_markup)
            else:
                await update.message.reply_text('La sala no existe.')
        else:
            await update.message.reply_text('Error: nombre de usuario no válido.')
    else:
        await update.message.reply_text('Por favor, proporciona un ID de sala.')

async def list_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if rooms:
        room_list = "\n".join([f"- {room_id}" for room_id in rooms.keys()])
        if isinstance(update, Update):
            await update.message.reply_text(f"Salas creadas:\n{room_list}")
        else:
            await update.message.reply_text(f"Salas creadas:\n{room_list}", reply_markup=update.message.reply_markup)
    else:
        if isinstance(update, Update):
            await update.message.reply_text("No hay salas creadas.")
        else:
            await update.message.reply_text("No hay salas creadas.", reply_markup=update.message.reply_markup)



async def listar_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    room_id = query.data.split('_')[2]
    sala = rooms[room_id]
    players = sala.get_players()
    player_list = "\n".join(players)
    await query.message.reply_text(text=f"Jugadores en la sala {room_id}:\n{player_list}", reply_markup=query.message.reply_markup)



async def listar_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    room_id = query.data.split('_')[2]
    sala = rooms[room_id]
    players = sala.get_players()
    player_list = "\n".join(players)
    await query.message.reply_text(text=f"Jugadores en la sala {room_id}:\n{player_list}", reply_markup=query.message.reply_markup)


async def estado_sala(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    room_id = query.data.split('_')[2]
    try:
        sala = rooms[room_id]  # Asegúrate de que esto sea un objeto de la clase Sala
        if sala.get_active():
            await query.message.reply_text(text=f"Estado de la sala {room_id}: Activo", reply_markup=query.message.reply_markup)
        else:
            await query.message.reply_text(text=f"Estado de la sala {room_id}: En preparación", reply_markup=query.message.reply_markup)
    except KeyError:
        await query.message.reply_text(text="La sala no existe.", reply_markup=query.message.reply_markup)
    except AttributeError:
        await query.message.reply_text(text="Error al obtener el estado de la sala.", reply_markup=query.message.reply_markup)



async def run(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    room_id = query.data.split('_')[1]
    try:
        sala = rooms[room_id]
        sala.set_active(True)  # Activar la sala
        await query.message.reply_text(text=f"El juego en la sala {room_id} ha comenzado", reply_markup=query.message.reply_markup)
    except KeyError:
        await query.message.reply_text(text="La sala no existe.", reply_markup=query.message.reply_markup)




# MANEJADORES DE COMANDOS ----------------------------------------------------------------------------------------------------
application.add_handler(CommandHandler('start', start))
application.add_handler(CallbackQueryHandler(button))
application.add_handler(CommandHandler('crear_sala', create_room))
application.add_handler(CommandHandler('unirse_sala', join_room))
application.add_handler(CommandHandler('listar_salas', list_rooms))


# ROUTES ---------------------------------------------------------------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')


# INICIO DE LA APP -----------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    application.run_polling()
    socketio.run(app, debug=True)
