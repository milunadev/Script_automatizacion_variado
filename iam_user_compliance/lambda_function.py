# Script que valida el tiempo de inactividad de los usuarios IAM
# y los invalida en caso sea mayor a dos semanas

import boto3
import time
import requests
from tabulate import tabulate
from datetime import datetime, timedelta

iam = boto3.client('iam')
general_user_data = []
webhook_url = ''  ## USE SLACK U OTHER WEBHOOK URL to send message

def generate_last_user_activity(username, user_arn):
    response = iam.generate_service_last_accessed_details(
        Arn=user_arn,
        Granularity='SERVICE_LEVEL'
    )
    job_id = response["JobId"]
    return job_id
    

def get_last_service_access(user,job_id):
    services_accessed = []
    response = iam.get_service_last_accessed_details(
        JobId = job_id
    )

    for service in response["ServicesLastAccessed"]:
        if 'LastAuthenticated' in service:
            services_accessed.append({'servicio': service['ServiceNamespace'], 'lastaccess':service['LastAuthenticated']})
    
    #print(services_accessed) #Lista todos los servicios y datos de acceso
    
    if services_accessed != []:    #Si se registra algun acceso 
        service, last_access = sort_access_data(services_accessed)
        #print(f'\n {service}   {last_access}')
        return service, last_access, 'api_key'
    else:   #Si no se registra ningun acceso
        return None, None, None
   

def sort_access_data(data):
    # Ordena la lista por la fecha de acceso más reciente
    data_sorted = sorted(data, key=lambda x: x['lastaccess'], reverse=True) 
    return [data_sorted[0]['servicio'],data_sorted[0]['lastaccess'] ]


def print_access_tables(data):
    # Obtener la fecha actual
    current_date = datetime.now().date()

    # Filtrar usuarios por última actividad dentro de las últimas 2 semanas y más de 2 semanas
    recent_access = []
    older_access = []
    for user in data:
        if user['LastActivity'] is not None:
            last_access_date = user['LastActivity'].date()
            if current_date - last_access_date <= timedelta(weeks=2):
                recent_access.append([user['User'], last_access_date.strftime('%Y-%m-%d'), user.get('type', '')])
            else:
                older_access.append([user['User'], last_access_date.strftime('%Y-%m-%d'), user.get('type', '')])
        else:
            older_access.append([user['User'], 'Nunca', user.get('type', '')])

    # Imprimir la tabla de usuarios con acceso reciente
    print("USUARIOS CON ACCESO LAS ULTIMAS 2 SEMANAS:")
    print(tabulate(recent_access, headers=["Username", "Fecha de Último Acceso", "Tipo"]))

    # Imprimir la tabla de usuarios con acceso hace más de 2 semanas o nunca
    print("\nUSUARIOS QUE NUNCA ACCEDIERON O HACE MAS DE 2 SEMANAS")
    print(tabulate(older_access, headers=["Username", "Fecha de Último Acceso", "Tipo"]))
    
    formatted_recent_access = tabulate(recent_access, tablefmt='plain', headers=["Username", "Fecha de Último Acceso", "Tipo"])
    formatted_old_access = tabulate(older_access, tablefmt='plain', headers=["Username", "Fecha de Último Acceso", "Tipo"])
    
    message = {
    "text": "LISTA DE USUARIOS Y ACCESOS A AWS MEDIANTE CONSOLA O APIKEY",
    "attachments": [
        {
            "text": "Usuarios con acceso en las ultimas 2 semanas",
            "color": "#36a64f"
        },
        {
            "text": f"```{formatted_recent_access}```",
            "color": "#36a64f"
        },
        {
            "text": "Usuarios con acceso hace más de 2 semanas o nunca:",
            "color": "#ff0000"
        },
        {
            "text": f"```{formatted_old_access}```",
            "color": "#ff0000"
        }
        ]
    }


    return message

def send_to_slack(message):
    response = requests.post(webhook_url, json=message, verify=False)
    if response.status_code == 200:
        print("Mensaje enviado exitosamente a Slack.")
    else:
        print(f"Error al enviar mensaje a Slack. Código de estado: {response.status_code}")


def lambda_handler(event='', context=''):
    # Inicializa clientes de AWS
    iam = boto3.client('iam')
    # Obtiene la lista de usuarios
    users = iam.list_users()
    no_console_users = []
    user_job_ids = []

    for user in users['Users']:        
        if 'PasswordLastUsed' in user:
            #print(f'-------------------   USER   ----------------------')
            #print(f'USER: {user["UserName"]}  --  LAST LOGIN: {user["PasswordLastUsed"]}')
            general_user_data.append({'User':user["UserName"], 'LastActivity':user["PasswordLastUsed"], 'type':'console'})
        else:
            no_console_users.append({'UserName': user["UserName"], 'Arn': user["Arn"]})

    #print("Consultando no console_user: ")

    
    for user in no_console_users:
        job_id = generate_last_user_activity(user["UserName"],user["Arn"])
        user_job_ids.append({'UserName': user["UserName"], 'job_id': job_id})

    time.sleep(10)

    for user in user_job_ids:
        service, last_access, type = get_last_service_access(user["UserName"],user['job_id'])
        
        #print(f'-------------------   USER   ----------------------')
        #print(f'USER: {user["UserName"]} -- LAST LOGIN A \n {service} el {last_access}')
        general_user_data.append({'User':user["UserName"], 'LastActivity':
        last_access, 'type': type , 'service':service})

    message_slack = print_access_tables(general_user_data)
    send_to_slack(message_slack)



