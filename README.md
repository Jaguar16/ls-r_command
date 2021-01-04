# RECHERCHE PARALLÈLE DE FICHIERS

Version parallèle de la commande : 
```sh
$ ls -r
```
Affiche tous les fichiers du répertoire courant et de ses sous-répertoires dont le nom vérifie
un motif donné.
La recherche est parallèlisée pour gagner en efficacité (un proccesus par sous-répertoires)

### Utilisation

```sh
$ python3 rls.py FILENAME [OPTIONS] ...
```
- FILENAME : motif recherché (gère les wildcards)
- option : `-first_match` ou `-server` ou `-debug`

| option | description |
| ------ | ------ |
| first_match | La commande arrête la recherche au premier fichier touvé par un processus |
| server | Se met en attente des requêtes sur le port 5000, une entrée du client est prise en compte comme FILENAME, le serveur envoie au client tous les chemins trouvés |
| debug | Affiche sur la sortie standard un message lorsqu'un processus entre et sort d'un répertoires |

### Exemple

Avec les dossiers test du repo :

```sh
$ python3 rls.py toto*
test2/fichier2/toto2_2.txt
test1/fichier1/toto1.txt
test3/fichier1/toto3_1.txt
test3/fichier3/toto3_3.txt
test2/fichier1/toto2_1.txt
test2/fichier3/toto2_3.txt
test1/fichier3/toto3.txt
test3/fichier2/toto3_2.txt
test1/fichier2/toto2.txt
```
```sh
$ python3 rls.py toto* -first_match
test1/fichier3/toto3.txt
```
