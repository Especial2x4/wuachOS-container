import asyncio
import telegram.error

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


# (Otras funciones aquí...)

async def load_bar_interna(query, context, mensaje, player, extractor):
    """Función interna que realiza la tarea y actualiza la barra de progreso."""
    total_pasos = 10
    for i in range(total_pasos + 1):
        progreso = int(i / total_pasos * 100)
        barra = "█" * i + "░" * (total_pasos - i)
        try:
            await mensaje.edit_text(f"Cargando... [{barra}] {progreso}%")
        except telegram.error.BadRequest:
            # Manejar el error si el mensaje ha sido eliminado
            print(f"Mensaje eliminado por el usuario: {query.from_user.id}")
            return  # Salir de la función si el mensaje ya no existe
        await asyncio.sleep(0.5)  # Simula un trabajo que tarda 0.5 segundos por paso (para que sea más rápido)
    try:
        await mensaje.edit_text("¡Carga completada! ✅")
    except telegram.error.BadRequest:
        print(f"Mensaje eliminado por el usuario: {query.from_user.id}")
        return

    # Realizar la extracción de fichitas después de completar la carga
    player.reducir_fichita()
    extractor.aumentar_fichita()
    await query.message.reply_text(text=f"Has extraído una fichita de {player.get_name()}. Ahora tienes {extractor.get_fichitas()} fichitas.")
    await context.bot.send_message(chat_id=player.user_id, text=f"Te han extraído una fichita. Ahora tienes {player.get_fichitas()} fichitas.")


async def load_bar(query, context, player, extractor):
    """Función principal que inicia la tarea en una tarea separada."""
    try:
        mensaje = await query.message.reply_text("Cargando... [ ] 0%")
        # Crear una tarea para ejecutar la función interna de forma concurrente
        asyncio.create_task(load_bar_interna(query, context, mensaje, player, extractor))
        await query.message.reply_text("Puedes seguir usando el bot mientras se realiza la carga.")
    except telegram.error.BadRequest:
        print(f"Error al enviar el mensaje inicial: {query.from_user.id}")
        return

async def load_bar(query, context, player, extractor):
    """Función principal que inicia la tarea en una tarea separada."""
    try:
        mensaje = await query.message.reply_text("Cargando... [ ] 0%")
        # Crear una tarea para ejecutar la función interna de forma concurrente
        asyncio.create_task(load_bar_interna(query, context, mensaje, player, extractor))
        await query.message.reply_text("Puedes seguir usando el bot mientras se realiza la carga.")
    except telegram.error.BadRequest:
        print(f"Error al enviar el mensaje inicial: {query.from_user.id}")
        return


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'crear_sala':
        await query.message.reply_text(text="Por favor, proporciona un ID de sala usando /crear_sala <ID>", reply_markup=query.message.reply_markup)
    elif query.data == 'unirse_sala':
        await query.message.reply_text(text="Por favor, proporciona un ID de sala usando /unirse_sala <ID>", reply_markup=query.message.reply_markup)
    elif query.data == 'listar_salas':
        await list_rooms(query, context)
    elif query.data.startswith('listar_players'):
        await listar_players(update, context)
    elif query.data.startswith('estado_sala'):
        await estado_sala(update, context)
    elif query.data.startswith('run'):
        await run(update, context)
    elif query.data.startswith('listar_para_espiar'):
        await listar_para_espiar(update, context)
    elif query.data.startswith('espiar_player'):
        await espiar_player(update, context)
    elif query.data.startswith('listar_para_extraer'):
        await listar_para_extraer(update, context)
    elif query.data.startswith('extraer_player'):
        await extraer_player(update, context)



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
        
        # Enviar mensaje a todos los jugadores en la sala
        keyboard_game_options = [
            [InlineKeyboardButton("Listar Players", callback_data=f'listar_players_{room_id}')],
            [InlineKeyboardButton("👁️ Espiar", callback_data=f'listar_para_espiar_{room_id}')],
            [InlineKeyboardButton("⚒️ Extraer", callback_data=f'listar_para_extraer_{room_id}')],
            [InlineKeyboardButton("🤝 Ceder", callback_data=f'ceder_{room_id}')],
            [InlineKeyboardButton("🧊 Hibernar", callback_data=f'hibernar_{room_id}')]
        ]
        
        reply_markup_game_options = InlineKeyboardMarkup(keyboard_game_options)
        
        for player_id in sala.get_player_ids():
            await context.bot.send_message(chat_id=player_id, text=f"El juego en la sala {room_id} ha comenzado. Elige una opción:", reply_markup=reply_markup_game_options)
        
    except KeyError:
        await query.message.reply_text(text="La sala no existe.", reply_markup=query.message.reply_markup)



async def listar_para_espiar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    room_id = query.data.split('_')[3]  # Esto varia en base a la callback anterior en este caso viene del teclado de run
    sala = rooms[room_id]
    players = sala.get_players()
    print(f"la sala es la {room_id} y la query {query}")
    keyboard = [[InlineKeyboardButton(player, callback_data=f'espiar_player_{room_id}_{player}')] for player in players]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(text="Selecciona un jugador para espiar:", reply_markup=reply_markup)



async def espiar_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.split('_')
    room_id = data[2]  # Asegurarse de que el índice sea correcto
    player_name = data[3]
    
    sala = rooms[room_id]
    player = next((p for p in sala.players if p.get_name() == player_name), None)
    
    if player:
        informe = player.espiar()
        await query.message.reply_text(text=informe)
    else:
        await query.message.reply_text(text="Jugador no encontrado.")



async def listar_para_extraer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    room_id = query.data.split('_')[3]  # Esto varia en base a la callback anterior en este caso viene del teclado de run
    sala = rooms[room_id]
    players = sala.get_players()
    
    keyboard = [[InlineKeyboardButton(player, callback_data=f'extraer_player_{room_id}_{player}')] for player in players]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(text="Selecciona un jugador para extraer una fichita:", reply_markup=reply_markup)


async def extraer_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.split('_')
    room_id = data[2]  # Asegurarse de que el índice sea correcto
    player_name = data[3]

    sala = rooms[room_id]
    player = next((p for p in sala.players if p.get_name() == player_name), None)
    user = update.callback_query.from_user
    extractor = next((p for p in sala.players if p.user_id == user.id), None)

    if player and extractor:
        # Mostrar la barra de carga antes de la extracción
        await load_bar(query, context, player, extractor)
    else:
        await query.message.reply_text(text="Jugador no encontrado.")



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
