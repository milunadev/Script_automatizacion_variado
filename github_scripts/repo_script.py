import requests, os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

ORG = os.getenv("ORG")
github_token = os.getenv("GITHUB_TOKEN")
headers = {
    'Accept': 'application/vnd.github+json',
    'Authorization': f'Bearer {github_token}',
    'X-GitHub-Api-Version': '2022-11-28'
}
url_base = 'https://api.github.com'
url_base_repo = f'{url_base}/orgs/{ORG}/repos'
url_base_branch = f'{url_base}/repos/{ORG}/'


def obtener_repos():
    repositorios = []
    page = 1
    per_page = 100

    while True:
        url = f"{url_base_repo}?page={page}&per_page={per_page}"
        response = requests.get(url, headers=headers)
        data = response.json()
        if not data:
            break
        repositorios.extend(data)
        page += 1
        print("Consultando")
    return repositorios

def consultar_ramas(repo):
    branch_list = []
    lista = []
    page = 1
    per_page = 100
    while True:
        url = f"{url_base_branch}{repo}/branches?page={page}&per_page={per_page}"
        response = requests.get(url, headers=headers)
        data = response.json()
        if not data:
            break
        lista.extend(data)
        page += 1
        print("Consultando")

    for branch in lista:
            branch_list.append(branch["name"])
    
    branch_number = len(lista)
 
    return [branch_number,branch_list]


def exportar_a_excel(repositorios):
    data_repos = []
    for repo in repositorios:
        [branch_number,branch_list] = consultar_ramas(repo["name"])
        data_repos.append([repo["id"], repo["name"], repo["language"], repo["created_at"], repo["pushed_at"], repo["html_url"], branch_number, branch_list])
        print("Repo actualizado: ", repo["name"])
    

    df = pd.DataFrame(data_repos, columns=['ID', 'Nombre', 'Lenguaje' , 'Creado', 'Actualizado', 'URL', 'Num branch', 'Branches'])
    df.to_excel("repos_github.xlsx", index=False)

repositorios = obtener_repos()
exportar_a_excel(repositorios)
  
        