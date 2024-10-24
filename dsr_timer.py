import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import pytz
import asyncio

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Variáveis de controle
timer_active = False
selected_text_channel = None  # Canal de texto selecionado para envio das mensagens
custom_times = {  # Dicionário para armazenar os horários customizados dos timers
    "pumpkinmon1": datetime.datetime.now(tz=pytz.timezone('America/Sao_Paulo')).replace(hour=7, minute=30, second=0, microsecond=0),
    "pumpkinmon2": datetime.datetime.now(tz=pytz.timezone('America/Sao_Paulo')).replace(hour=9, minute=30, second=0, microsecond=0),
    "pumpkinmon3": datetime.datetime.now(tz=pytz.timezone('America/Sao_Paulo')).replace(hour=11, minute=0, second=0, microsecond=0),
    "gotsumon": datetime.datetime.now(tz=pytz.timezone('America/Sao_Paulo')).replace(hour=13, minute=0, second=0, microsecond=0),
    "seraphmon": datetime.datetime.now(tz=pytz.timezone('America/Sao_Paulo')).replace(hour=12, minute=0, second=0, microsecond=0) + datetime.timedelta((5 - datetime.datetime.now(tz=pytz.timezone('America/Sao_Paulo')).weekday()) % 7)  # Sábados às 12:00
}
chain_timers = {}  # Dicionário para armazenar os temporizadores em cadeia

# Definindo o fuso horário de Brasília
brasilia_tz = pytz.timezone('America/Sao_Paulo')

# Ajuste inicial para o alarme de 07:00
next_7am_time = datetime.datetime.now(tz=brasilia_tz).replace(
    hour=7, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)

@bot.event
async def on_ready():
    print(f'Bot logged in as {bot.user}')

    # Sincroniza os comandos de barra
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Error syncing commands: {e}')

    # Procura o canal de texto com o nome 'comandos' e envia a mensagem de boas-vindas
    guild = bot.guilds[0]
    text_channel = discord.utils.get(guild.text_channels, name='comandos')

    if text_channel:
        await text_channel.send(
            "Olá, meu nome é Clockmon e te ajudarei a saber quando aparecerão digimons fortes."
        )
        # Enviar a lista de comandos em seguida
        commands_list = (
            "/timerstart - Inicia o temporizador e envia uma mensagem de teste no canal selecionado.\n"
            "/timerstop - Para o temporizador.\n"
            "/timerchannel - Permite selecionar o canal de texto para enviar as mensagens de notificação.\n"
            "/timerremain - Exibe quanto tempo falta para o próximo disparo do bot.\n"
            "/timerset - Permite ajustar o horário de um temporizador específico.\n"
            "/timerchain - Agende um temporizador que se repete a cada dia com uma hora a mais.\n"
            "/timer - Lista todos os comandos disponíveis do bot."
        )
        await text_channel.send(f"Lista de comandos:\n{commands_list}")

    check_timer.start()

@tasks.loop(minutes=1)
async def check_timer():
    if not timer_active or not selected_text_channel:
        return

    # Obter o horário atual em Brasília
    now = datetime.datetime.now(tz=brasilia_tz)

    # Verificar os timers customizados
    for timer_name, timer_datetime in custom_times.items():
        if isinstance(timer_datetime, datetime.datetime):
            # Verificar se o horário do timer coincide com o horário atual
            if now >= timer_datetime and now.hour == timer_datetime.hour and now.minute == timer_datetime.minute:
                await trigger_event(timer_name)

    # Verifica o alarme ajustável das 07:00
    global next_7am_time
    if now >= next_7am_time:
        await trigger_event("kuwagamon")
        next_7am_time += datetime.timedelta(hours=24)

    # Verificar os timers em cadeia
    for chain_name, chain_datetime in list(chain_timers.items()):
        if now >= chain_datetime and now.hour == chain_datetime.hour and now.minute == chain_datetime.minute:
            await trigger_event(chain_name)
            # Atualizar o próximo disparo com uma hora a mais no próximo dia
            chain_timers[chain_name] = chain_datetime + datetime.timedelta(days=1, hours=1)

async def trigger_event(message):
    # Envia mensagem em um canal de texto selecionado
    if selected_text_channel:
        await selected_text_channel.send(f"HORA DA RAID PESSOAL: {message}")

# Define o comando de barra /timerstart
@bot.tree.command(
    name="timerstart",
    description="Inicia o temporizador e envia uma mensagem de teste no canal selecionado."
)
async def timer_start(interaction: discord.Interaction):
    global timer_active, custom_times
    timer_active = True

    # Reconfigura os horários para os valores padrões ao iniciar
    custom_times = {
        "pumpkinmon1": datetime.datetime.now(tz=brasilia_tz).replace(hour=7, minute=30, second=0, microsecond=0) + datetime.timedelta(days=1 if datetime.datetime.now(tz=brasilia_tz).hour >= 7 else 0),
        "pumpkinmon2": datetime.datetime.now(tz=brasilia_tz).replace(hour=9, minute=30, second=0, microsecond=0) + datetime.timedelta(days=1 if datetime.datetime.now(tz=brasilia_tz).hour >= 9 else 0),
        "pumpkinmon3": datetime.datetime.now(tz=brasilia_tz).replace(hour=11, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1 if datetime.datetime.now(tz=brasilia_tz).hour >= 11 else 0),
        "gotsumon": datetime.datetime.now(tz=brasilia_tz).replace(hour=13, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1 if datetime.datetime.now(tz=brasilia_tz).hour >= 13 else 0),
        "seraphmon": datetime.datetime.now(tz=brasilia_tz).replace(hour=12, minute=0, second=0, microsecond=0) + datetime.timedelta((5 - datetime.datetime.now(tz=brasilia_tz).weekday()) % 7)  # Sábados às 12:00
    }

    await interaction.response.send_message("Temporizador iniciado com horários padrão.", ephemeral=True)

    # Teste de envio de mensagem no canal de texto selecionado
    if selected_text_channel:
        await selected_text_channel.send("Teste de mensagem no canal selecionado.")

# Define o comando de barra /timerstop
@bot.tree.command(name="timerstop", description="Para o temporizador.")
async def timer_stop(interaction: discord.Interaction):
    global timer_active
    timer_active = False
    await interaction.response.send_message("Temporizador parado.", ephemeral=True)

# Define o comando de barra /timerchannel
@bot.tree.command(
    name="timerchannel",
    description="Escolha o canal de texto para enviar as mensagens de notificação."
)
async def timer_channel(interaction: discord.Interaction, channel_name: str):
    global selected_text_channel
    # Procura o canal de texto pelo nome fornecido
    selected_text_channel = discord.utils.get(interaction.guild.text_channels, name=channel_name)
    if selected_text_channel:
        await interaction.response.send_message(
            f"Canal de texto '{channel_name}' selecionado para envio de mensagens.",
            ephemeral=True)
        # Testa o envio de mensagem no canal selecionado
        await selected_text_channel.send("Este é um teste de mensagem neste canal.")
    else:
        await interaction.response.send_message(
            f"Canal de texto '{channel_name}' não encontrado. Verifique o nome e tente novamente.",
            ephemeral=True)

# Define o comando de barra /timerset
@bot.tree.command(name="timerset", description="Ajusta o horário de um timer específico.")
async def timerset(interaction: discord.Interaction, timer_name: str, new_datetime: str):
    global custom_times

    try:
        # Converte a string de data e hora para um objeto datetime em fuso horário de Brasília
        new_time = datetime.datetime.strptime(new_datetime, "%d/%m/%Y %H:%M")
        new_time = brasilia_tz.localize(new_time)

        # Verifica se o horário configurado é no futuro para o timer especificado
        if new_time <= datetime.datetime.now(tz=brasilia_tz):
            await interaction.response.send_message(
                "A data e hora devem ser no futuro.",
                ephemeral=True)
            return

        # Armazena a nova data e hora no dicionário de horários customizados
        custom_times[timer_name] = new_time
        await interaction.response.send_message(
            f"Timer '{timer_name}' ajustado para {new_time.strftime('%d/%m/%Y %H:%M')} (horário de Brasília).",
            ephemeral=True)
    except ValueError:
        await interaction.response.send_message(
            "Formato de data/hora inválido. Use o formato: dd/mm/yyyy hh:mm",
            ephemeral=True)

# Define o comando de barra /timerchain
@bot.tree.command(name="timerchain", description="Agende um temporizador que se repete a cada dia com uma hora a mais.")
async def timer_chain(interaction: discord.Interaction, chain_name: str, start_datetime: str):
    global chain_timers

    try:
        # Converte a string de data e hora para um objeto datetime em fuso horário de Brasília
        chain_time = datetime.datetime.strptime(start_datetime, "%d/%m/%Y %H:%M")
        chain_time = brasilia_tz.localize(chain_time)

        # Verifica se o horário configurado é no futuro
        if chain_time <= datetime.datetime.now(tz=brasilia_tz):
            await interaction.response.send_message(
                "A data e hora devem ser no futuro.",
                ephemeral=True)
            return

        # Armazena o novo temporizador em cadeia
        chain_timers[chain_name] = chain_time
        await interaction.response.send_message(
            f"Timer em cadeia '{chain_name}' agendado para {chain_time.strftime('%d/%m/%Y %H:%M')} (horário de Brasília).",
            ephemeral=True)
    except ValueError:
        await interaction.response.send_message(
            "Formato de data/hora inválido. Use o formato: dd/mm/yyyy hh:mm",
            ephemeral=True)

# Define o comando de barra /timer
@bot.tree.command(name="timer", description="Lista os comandos disponíveis do bot.")
async def timer(interaction: discord.Interaction):
    commands_list = (
        "/timerstart - Inicia o temporizador e envia uma mensagem de teste no canal selecionado.\n"
        "/timerstop - Para o temporizador.\n"
        "/timerchannel - Permite selecionar o canal de texto para enviar as mensagens de notificação.\n"
        "/timerremain - Exibe quanto tempo falta para o próximo disparo do bot.\n"
        "/timerset - Permite ajustar o horário de um temporizador específico.\n"
        "/timerchain - Agende um temporizador que se repete a cada dia com uma hora a mais.\n"
        "/timer - Lista todos os comandos disponíveis do bot."
    )
    await interaction.response.send_message(f"Lista de comandos:\n{commands_list}", ephemeral=True)

# Define o comando de barra /timerremain
@bot.tree.command(
    name="timerremain",
    description="Mostra quanto tempo falta para o próximo disparo."
)
async def timer_remain(interaction: discord.Interaction):
    if not timer_active:
        await interaction.response.send_message("O temporizador não está ativo.", ephemeral=True)
        return

    # Obter o horário atual em Brasília
    now = datetime.datetime.now(tz=brasilia_tz)
    remaining_times = []

    # Horários fixos para a semana
    for timer_name, timer_datetime in custom_times.items():
        if isinstance(timer_datetime, datetime.datetime) and now < timer_datetime:
            remaining = timer_datetime - now
            days, seconds = remaining.days, remaining.seconds
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            remaining_times.append(
                f"{timer_name}; {timer_datetime.strftime('%d/%m/%Y %H:%M:%S')}; {days} dias, {hours} horas, {minutes} minutos, {seconds} segundos"
            )

    # Temporizadores em cadeia
    for chain_name, chain_datetime in chain_timers.items():
        if now < chain_datetime:
            remaining = chain_datetime - now
            days, seconds = remaining.days, remaining.seconds
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            remaining_times.append(
                f"{chain_name}; {chain_datetime.strftime('%d/%m/%Y %H:%M:%S')}; {days} dias, {hours} horas, {minutes} minutos, {seconds} segundos"
            )

    if remaining_times:
        await interaction.response.send_message("Próximos disparos:\n" + "\n".join(remaining_times), ephemeral=True)
    else:
        await interaction.response.send_message("Nenhum disparo programado para hoje.", ephemeral=True)

bot.run(
    '')
