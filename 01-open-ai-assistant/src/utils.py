# gmail
from email.message import EmailMessage
import smtplib

# google sheets
import pandas as pd
import pygsheets

# whatsapp 
from heyoo import WhatsApp

# openai
from openai import OpenAI

# utils
from time import sleep
import json
from dotenv import load_dotenv, find_dotenv
import os
from datetime import datetime

# Obtener el api key
# load_dotenv()
# load_dotenv(find_dotenv())
# _ = load_dotenv(find_dotenv())
env_file = find_dotenv('.env')
load_dotenv(env_file)

# credenciales
OPENAI_API_KEY      = os.getenv("OPENAI_API_KEY")

CORREO_REMITENTE    = os.getenv("EMAIL_REMITENTE")
APP_PASSWORD_GMAIL  = os.getenv("APP_PASSWORD_GMAIL")

WHATSAPP_API_TOKEN  = os.getenv("WHATSAPP_API_TOKEN")
PHONE_NUMBER_ID     = os.getenv("PHONE_NUMBER_ID")

GOOGLE_SHEETS_ID    = os.getenv("GOOGLE_SHEETS_ID")
GOOGLE_SHEETS_NAME  = os.getenv("GOOGLE_SHEETS_NAME")

#----------------------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------------
#------------------------------------------------ App ----------------------------------------------------

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=OPENAI_API_KEY)

#----------------------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------------
#------------------------------------------------ conexion a email ----------------------------------------------------

def enviar_correo(nombre_lead, correo_lead, mensaje_para_lead):
  try:
    remitente = CORREO_REMITENTE
    destinatario = correo_lead
    mensaje = mensaje_para_lead

    email = EmailMessage()
    email["From"] = remitente
    email["To"] = destinatario
    email["Subject"] = "Mensaje importante para ti " + nombre_lead
    email.set_content(mensaje)

    smtp = smtplib.SMTP_SSL("smtp.gmail.com")
    smtp.login(remitente, APP_PASSWORD_GMAIL)
    smtp.sendmail(remitente, destinatario, email.as_string())
    smtp.quit()
    return True
  
  except:
    return False

#----------------------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------------
#-------------------------------------------- conexion a google sheets ------------------------------------------------

def registrar_google_sheets(nombre_lead, correo_lead, producto_de_interes, celular_lead):
  # obtener los datos de google sheets
  url=f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEETS_ID}/gviz/tq?tqx=out:csv&sheet={GOOGLE_SHEETS_NAME}"
    
  # añadimos el nuevo registro al dataframe
  df = pd.read_csv(url)
  print('Base Inicial')
  print(df)
  print('\n')

  # df = agregar_cliente(df, nombre_lead, correo_lead, producto_de_interes, celular_lead)

  # Generar el nuevo ID
  if len(df) == 0:
      nuevo_id = 1  # Si el DataFrame está vacío, empezamos con 1
  else:
      # Tomamos el máximo ID existente y le sumamos 1
      nuevo_id = df['ID'].astype(int).max() + 1
  
  # Generar Fecha de Registro
  fecha_registro = datetime.today()
  
  # Agregar el nuevo registro
  df.loc[len(df.index)] = [fecha_registro, nuevo_id, 
    nombre_lead, correo_lead, producto_de_interes, celular_lead]
  
  print('Base Actualizada')
  print(df)

  try:
    # cargamos a google sheets
    service_account_path='src/agr-asistente-openai.json'       # Actualizar
    gc = pygsheets.authorize(service_file=service_account_path)

    # open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
    sh = gc.open_by_url(url)

    # select the first sheet
    wks = sh[0]
    # update the first sheet with df, starting at cell B2.
    wks.set_dataframe(df, (1,1)) # fila columna
    return True
  except TypeError:
    print(TypeError)
    return False

#----------------------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------------
#------------------------------------------- enviar mensaje por whatsapp ----------------------------------------------

def enviar_whatsapp(numero_whatsapp_asesor, mensaje_asesor):
  """para enviar mensaje a a whatsapp"""
  try:
    messenger = WhatsApp(
      token=WHATSAPP_API_TOKEN,
      phone_number_id=PHONE_NUMBER_ID
    )
    # For sending a Text messages
    messenger.send_message(message=mensaje_asesor, recipient_id=numero_whatsapp_asesor)
    return True
  except:
    return False

#----------------------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------------
#------------------------------------------- Ejecutar el RUN ----------------------------------------------

def run_excecuter(run):
  while True:

    run_status=client.beta.threads.runs.retrieve(
        thread_id=run.thread_id,
        run_id=run.id
    )

    if run_status.status =="completed":
      print("accion terminada")
      break

    elif run_status.status=="requires_action":
      print("requiere accion")

      list_of_actions=run_status.required_action.submit_tool_outputs.tool_calls

      print("-----"*20)
      print(list_of_actions)
      print("-----"*20)

      tools_output_list=[] # guardo las salidas de las funciones/tools

      for accion in list_of_actions:

        if accion.function.name =="registrar_google_sheets":

          nombre=accion.function.name
          argumentos=json.loads(accion.function.arguments)

          print("Nombre de la funcion a ejecutar: ", nombre)
          print("Argumentos de la función: ", argumentos)

          interesado_agregado=registrar_google_sheets(
            nombre_lead=argumentos["nombre_lead"], 
            correo_lead=argumentos["correo_lead"], 
            producto_de_interes=argumentos["producto_de_interes"], 
            celular_lead=argumentos["celular_lead"]
          )

          tools_output_list.append(
              {
                  "tool_call_id": accion.id,
                  "output": str(interesado_agregado)
              }
          )

        elif accion.function.name =="enviar_correo":

          nombre=accion.function.name
          argumentos=json.loads(accion.function.arguments)

          print("Nombre de la funcion a ejecutar: ", nombre)
          print("Argumentos de la funcion: ", argumentos)

          correo_enviado=enviar_correo(
            nombre_lead=argumentos["nombre_lead"], 
            correo_lead=argumentos["correo_lead"], 
            mensaje_para_lead=argumentos["mensaje_para_lead"]
          )

          tools_output_list.append(
              {
                  "tool_call_id": accion.id,
                  "output": str(correo_enviado)
              }
          )

        elif accion.function.name =="enviar_whatsapp":

          nombre=accion.function.name
          argumentos=json.loads(accion.function.arguments)

          print("Nombre de la funcion a ejecutar: ", nombre)
          print("Argumentos de la funcion: ", argumentos)

          whatsapp_enviado=enviar_whatsapp(
            numero_whatsapp_asesor=argumentos["numero_whatsapp_asesor"], 
            mensaje_asesor=argumentos["mensaje_asesor"]
          )

          tools_output_list.append(
              {
                  "tool_call_id": accion.id,
                  "output": str(whatsapp_enviado)
              }
          )

        else:
          return "No se encontró la accion"

      print("ejecucion de acciones ha terminado")
      print(tools_output_list)

      client.beta.threads.runs.submit_tool_outputs(
          thread_id=run.thread_id,
          run_id=run.id,
          tool_outputs=tools_output_list
      )

    else:
      print("Esperando respuesta del Asistente")
      sleep(3)

# if __name__=="__main__":
#   print(OPENAI_API_KEY)
  # enviar_correo(correo_lead="", mensaje_para_lead="", nombre_lead="")
  # registrar_google_sheets(
  #     nombre_lead="Persona 2",
  #     correo_lead="persona2@gmail.com",
  #     producto_de_interes="MLE",
  #     celular_lead=234567890
  # )