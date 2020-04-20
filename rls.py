#!/usr/bin/env python3

import sys, os, time, random, argparse, signal, socket, select


# NOM : BAROUDI
# PRENOM : AYMEN
# NUM ETUDIANT : 21500891




###### OPTIONS ET PARAMETRES DE LA LIGNE DE COMMANDE  ##############

FILENAME = ''   # le nom du fichier à rechercher
                # contient éventuellement des wildcards
DEBUG = False   # option -debug : pour activer les messages de debug
FIRST = False   # option -first-match : on s'arrête au premier fichier trouve
SERVER = False  # option -server




###### FONCTIONS AUXILIAIRES : NE PAS MODIFIER ####################

def debug(msg) :
    """affiche un message de debug sur la sortie d'erreur"""
    if DEBUG :
        sys.stderr.write("[{}] {}\n".format(os.getpid(), msg))
    

def change_dir(directory) :
    """change le répertoire dans lequel le processus s'exécute"""
    t = random.randint(1, 2)
    debug('entre dans le répertoire {} et dort {} sec'.format(directory, t))
    if DEBUG :
        time.sleep(t)
    os.chdir(directory)


def subdirs() :
    """renvoie la liste des sous-répertoires du répertoire courant"""
    return [x for x  in os.listdir() if os.path.isdir(x)]
    
def sys_exit(code) :
    debug('termine avec le code de sortie {}'.format(code))
    sys.exit(code)


def load_options() :
    """initialise les variables globales par rapport aux options saisies sur la ligne de commande"""
    global FILENAME, DEBUG, FIRST, SERVER
    parser = argparse.ArgumentParser()
    parser.add_argument('-debug', action='store_true', help='active le mode debug')
    parser.add_argument('-server', action='store_true', help='active le mode serveur')
    parser.add_argument('-first_match', action='store_true', help="s'arrête au premier fichier trouvé")
    parser.add_argument('FILENAME', type=str, nargs='?', help='le(s) fichier(s) à chercher')
    args = parser.parse_args()
    FILENAME = args.FILENAME
    SERVER = args.server
    DEBUG = args.debug
    FIRST = args.first_match
    if FILENAME == None and not SERVER :
        parser.error('FILENAME doit être spécifié')
        
    

####### FONCTIONS A MODIFIER  #####################################


 # Tableau des pids
# Il va servir pour l'options -first_match
# On pourra envoyer grace au ce tableau
# le signal SIGUSR1 aux processus qui sont encores actifs
# lorsqu'un processus a deja trouve (renvoie le code de sortie 0)


def lire_pipe(fdr) :
    """ Lit et renvoie TOUT ce qu'il y a dans un pipe et le renvoie (il faut que le fd soit deja ouvert en lecture)"""
    c = os.read(fdr,1)
    lu = b""
    while c:
        lu += c
        c = os.read(fdr,1)
    return lu



def local_ls() :
    """renvoie la liste des fichiers du répertoire courant qui correspondent à FILENAME"""
    # A MODIFIER : lancer un sous-processus ls pour autoriser les wildcards dans FILENAME
    r,w = os.pipe()
    pid = os.fork()
    if pid != 0 :
        # Le Pere : ferme w, lit dans le pipe.
        # Met dans L le resultat de la commande ls FILENAME
        os.close(w)
        p,s = os.wait()
        res_cmd = lire_pipe(r)
        L = [x for x in res_cmd.decode().split('\n') if x !='']
    else :
        # Le Fils
        os.close(1)   # On ferme stdout
        os.dup2(w,1)  # On redirige stdout vers le pipe
        os.close(2)   # On ferme stderr
        out = os.open('/dev/null',os.O_WRONLY) # On ouvre /dev/null
        os.dup2(out,2) # On redirige stdout vers /dev/null
        os.close(r)
        os.execv("/bin/sh", ["sh", "-c", "ls {}".format(FILENAME)])
        # On execute la commande, elle va alors mettre dans le pipe le resultat de la commande
        # et les erreurs (fichier ou dossier de type FILENAME inexistant) dans /dev/null
        #sys.exit(0)
    return L




def explorer(dirname,relative_path) :
    """explorateur"""
    global FIRST    # On en a besoin pour savoir si l'options -first_match est active
    global tab_pids
    tab_pids = []# On en a besoin si -first_match est active

    change_dir(dirname)
    code_de_sortie = 1 # Code de sortie par defaut est 1. 
                       # local_ls() renvoie [] i.e FILENAME n'est pas dans le dossier local (dirname) 
    res_ls = local_ls() # resultat de l'appel à local_ls
    sous_rep = subdirs() # Listes des sous rep du rep courant

    for x in res_ls :
        print(os.path.join(relative_path, x))
        code_de_sortie = 0  # Si on est dans le for c'est que local_ls() n'est pas vide donc on trouve un FILENAME. 
        if FIRST :
            sys_exit(0) # Si first_match est active on peut exit ici. Plus besoin de chercher...
    
    for subdir in sous_rep :
        pid = os.fork()
        if not pid : 
            #On est dans le ps fils
            explorer(subdir, os.path.join(relative_path, subdir))
            #change_dir('..')
            #print("valeur du code de sortie %d dans %d" % (code_de_sortie, os.getpid()))
            #sys_exit(code_de_sortie)

        else :
            tab_pids.append(pid)

    for d in sous_rep :
        p,s = os.wait()
        tab_pids.remove(p)
        if os.WIFEXITED(s) :
            if os.WEXITSTATUS(s) == 0 :
                code_de_sortie = 0
                if FIRST : break

    if  code_de_sortie == 0 and FIRST :
        for process in tab_pids :
            os.kill(process,signal.SIGUSR1)

        for p in tab_pids :
            os.wait()
        sys_exit(0)

    #print("PROCESS [{}] TAB_PID {}".format(os.getpid(),tab_pids))
    sys_exit(code_de_sortie)




def handler(dentifrice, ignore):
    """ Traitant pour le signal SIGUSR1 """
    #print("SIGNAL SIGUSR1 BIEN RECU")
    global tab_pids

    for p in tab_pids :
        os.kill(p,signal.SIGUSR1)

    for p in tab_pids :
        os.wait()

    sys_exit(2)



def serveur():
    global FILENAME
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM,0)
    addr_server = ("", 50000)
    sock.bind(addr_server)
    sock.listen(5)
    inputs = [sock]
    outputs,err = [],[]
    
    while inputs :
        
        lectures,ecriture,erreur = select.select(inputs,outputs,err,60)
        
        for i in lectures :

            if i == sock :
                conn,(addr,port) = sock.accept()
                inputs.append(conn)
                print("%s port %d Connecté"% (addr,port))
                p,s = os.fork()

                if p : #pere
                    conn.close()
                    inputs.remove(i)

            else :
                filename = i.recv(1024)
                    
                if (len(filename)) == 0:
                    print("Message vide")

                if filename == 'exit':
                    conn.close()
                    
                else :
                    FILENAME = filename
                    dup2(sock,1)
                    dup2(sock,2)
                    explorer('.','')

    sock.close()
                    



def main() :
    """fonction principale"""
    load_options()
    if FIRST :
        signal.signal(signal.SIGUSR1, handler)
    if SERVER :
        serveur()
    else:
        explorer('.','')


if __name__ == "__main__" :
    main()










