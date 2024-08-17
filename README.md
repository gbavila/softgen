# SoftGen - Projeto Final de Graduação
Desenvolvimento de um sistema web assistido por IA para geração automática 
de software a partir de especificações em linguagem natural.

Desenvolvido por: Gabriel Almeida Avila e Silva

## DJANGO
Para realizar mudanças em modelos, siga essas 3 etapas:

1. Faça as mudanças no models.py.
2. Execute ```python manage.py makemigrations``` para criar as migrações dessas mudanças.
3. Execute ```python manage.py migrate``` para aplicar essas mudanças na base de dados.

Playground shell: ```python manage.py shell```

É recomendado utilizar um ambiente virtual para interagir e utilizar os comandos python.

Veja https://docs.python.org/3/library/venv.html para entender como montar esse ambiente.

## Execução com Docker
Para executar localmente, tenha o ambiente Docker instalado. 

Basta executar na raíz do projeto:
* ```docker-compose up --build``` para construir os containers.
* ```docker-compose up``` caso os containers já estejam contruídos com os arquivos mais recentes.
