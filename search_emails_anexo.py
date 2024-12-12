import os
import base64
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

# Escopo necessário para acessar Gmail e Google Drive
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/drive'
]

def authenticate_service():
    """Autentica e retorna os serviços do Gmail e do Google Drive."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    gmail_service = build('gmail', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)
    return gmail_service, drive_service

def search_emails_with_subject(service, subject_keyword):
    """Busca e-mails com uma palavra específica no assunto."""
    try:
        query = f"subject:{subject_keyword}"
        results = service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])
        matched_messages = []
        for message in messages:
            message_detail = service.users().messages().get(userId='me', id=message['id']).execute()
            matched_messages.append(message_detail)
        return matched_messages
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []

def upload_to_drive(service, file_path, folder_id=None):
    """Faz upload de um arquivo para o Google Drive."""
    file_metadata = {'name': os.path.basename(file_path)}
    if folder_id:
        file_metadata['parents'] = [folder_id]

#PARA CORRIGIR/BUG: precisa fazer que seja comparado se o arquivo que ja tem na pasta é repetido e se for ignorar o upload dele
    media = MediaFileUpload(file_path, resumable=True)
    uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    
def download_and_upload_attachments(gmail_service, drive_service, messages, drive_folder_id=None):
    """Faz download de anexos e faz upload para o Google Drive."""
    temp_dir = 'pasta_temporaria'
    os.makedirs(temp_dir, exist_ok=True)

    for message in messages:
        parts = message.get('payload', {}).get('parts', [])
        for part in parts:
            if part.get('filename') and part['body'].get('attachmentId'):
                attachment_id = part['body']['attachmentId']
                attachment = gmail_service.users().messages().attachments().get(
                    userId='me', messageId=message['id'], id=attachment_id
                ).execute()
                file_data = base64.urlsafe_b64decode(attachment['data'])
                file_path = os.path.join(temp_dir, part['filename'])
                with open(file_path, 'wb') as file:
                    file.write(file_data)

                # Upload para o Google Drive
                upload_to_drive(drive_service, file_path, drive_folder_id)
                #mensagem de finalizacao do envio ao drive
                print(f"Arquivo(s) enviado(s) com sucesso a pasta escolhida com sucesso!")

    # Limpar arquivos temporários e exclui a pasta com os arquivos antes de finalizar o script
    for file_name in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, file_name))
    os.rmdir(temp_dir)

def main():
    """Função principal."""
    gmail_service, drive_service = authenticate_service()
    #palavra que tem no assunto para pesquisar
    subject_keyword = input('Copie e cole o assunto do email para fazer o upload para o google drive: ')

    # subject_keyword = 'Petro foto 2'
    #pasta "DOWNLOADS-LOOPAR-GMAIL"
    drive_folder_id = '1hiNvdy7UuGgV55ra2JpaJbnAWkMewCkj'
    messages = search_emails_with_subject(gmail_service, subject_keyword)

    if messages:
        print(f"{len(messages)} e-mail(s) encontrado(s) com o assunto contendo '{subject_keyword}'.")
        download_and_upload_attachments(gmail_service, drive_service, messages, drive_folder_id)
        print("Arquivos salvos e programa finalizado!")
    else:
        print(f"Nenhum e-mail encontrado com o assunto '{subject_keyword}'.")

if __name__ == '__main__':
    main()



# import os
# import base64
# from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError
# from google_auth_oauthlib.flow import InstalledAppFlow
# from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials

# # Escopo necessário para acessar o Gmail
# SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# def authenticate_gmail():
#     """Autentica e retorna o serviço do Gmail."""
#     creds = None
#     # Arquivo de token armazenado localmente
#     if os.path.exists('token.json'):
#         creds = Credentials.from_authorized_user_file('token.json', SCOPES)
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(
#                 'credentials.json', SCOPES)
#             creds = flow.run_local_server(port=0)
#         with open('token.json', 'w') as token:
#             token.write(creds.to_json())
#     return build('gmail', 'v1', credentials=creds)

# def search_emails_with_subject(service, subject_keyword):
#     """Busca e-mails com uma palavra específica no assunto."""
#     try:
#         query = f"subject:{subject_keyword}"
#         results = service.users().messages().list(userId='me', q=query).execute()
#         messages = results.get('messages', [])
#         matched_messages = []
#         for message in messages:
#             message_detail = service.users().messages().get(userId='me', id=message['id']).execute()
#             matched_messages.append(message_detail)
#         return matched_messages
#     except HttpError as error:
#         print(f"An error occurred: {error}")
#         return []

# def download_attachments(service, messages, output_dir):
#     """Faz download dos anexos de mensagens especificadas."""
#     if not os.path.exists(output_dir):
#         os.makedirs(output_dir)
#     for message in messages:
#         parts = message.get('payload', {}).get('parts', [])
#         for part in parts:
#             if part.get('filename') and part['body'].get('attachmentId'):
#                 attachment_id = part['body']['attachmentId']
#                 attachment = service.users().messages().attachments().get(
#                     userId='me', messageId=message['id'], id=attachment_id
#                 ).execute()
#                 file_data = base64.urlsafe_b64decode(attachment['data'])
#                 file_path = os.path.join(output_dir, part['filename'])
#                 with open(file_path, 'wb') as file:
#                     file.write(file_data)
                

# def main():
#     """Função principal."""
#     service = authenticate_gmail()
#     subject_keyword = 'BAIXAR'
#     output_dir = 'Anexos_emails'
#     messages = search_emails_with_subject(service, subject_keyword)
#     if messages:
#         print(f"{len(messages)} e-mail(s) encontrado(s) com o assunto contendo '{subject_keyword}'.")
#         download_attachments(service, messages, output_dir)
#         print("Arquivos salvos e programa finalizado!")
#     else:
#         print(f"Nenhum e-mail encontrado com o assunto '{subject_keyword}'.")

# if __name__ == '__main__':
#     main()
