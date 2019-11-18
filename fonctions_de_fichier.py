import os
import test


"""Ce code regroupe les fonctions qui s'occupent de la gestion des fichiers.
Ces fichiers servent a enregistrer les differentes configurations de fader, il y en a 6 au total."""


"""Cette fonction vide completement un fichier en l'ouvrant en mode ecriture, puis en le refermant.
---------------------------------------------------------------------------------------------------
@param configuration : le numero de la configuration correspondant au fichier que nous voulons vider."""
def raz_fichier(configuration):
    chemin = "config/config" + str(configuration) + ".txt"
    with open(chemin, "w") as file:
        pass


#TODO il se peut que cette fonction n'existe plus dans le futur
def maj_fichier(configuration, nom):
    chemin = "config/config" + str(configuration) + ".txt"
    with open(chemin, "a") as file:
        file.write(nom)


"""Cette fonction ecrit une chaine de caracteres dans un fichier A UNE POSITION PRECISE.
Elle sert a mettre a jour la valeur d'un fader precis quand celui a change de place.
#TODO Cela fonctionne egalement quand nous voulons changer le nom d'un fader precis.
----------------------------------------------------------------------------------
@param configuration : numero de la configuration que l'on veut changer.
@param a_ecrire : la chaine de caracteres a inserer dans le fichier.
@param numero_fader : le numero du fader qui a change de valeur.
@param identification : quelle type de reecriture on va faire"""
def ecriture_fichier(configuration, a_ecrire, matricule_fader, identification):    
    chemin = "config/config" + str(configuration) + ".txt"
    with open(chemin, "r+") as file:                                           #on ouvre le fichier de la configuration
        texte = file.read()                                                    #on lit ce fichier


        indice_fader = texte.index(str(matricule_fader))                       #on cherche l'emplacement du nom du fader dans le fichier
                                                                               #car grace a ca on peut trouver l'emplacement de l'ancienne valeur

        file.seek(0)                                                           #on retourne au debut du fichier
        if identification == "Master":                                         #adaptation pour ecrire le master
            file.write(texte[:indice_fader+1] + str(a_ecrire) + texte[indice_fader+4:])

        elif identification == "Nom":
            file.write(texte[:indice_fader+7] + str(a_ecrire) + texte[indice_fader+11:])

        elif identification == "Valeur":
            file.write(texte[:indice_fader+4] + str(a_ecrire) + texte[indice_fader+7:]) #on remplace l'ancienne valeur par la nouvelle


"""Cette fonction test la taille d'un fichier de configuration afin de bien voir s'il est possible a charger.
Il renvoit configurations_remplies au programme fonctions_annexes, un tableau qui regroupe les numero des 
configurations ayant quelque chose dans leur fichier.
----------------------------------------------------
@param identification: la fonction possede plusieurs usages, une a l'initialisation et une autre pour les autres cas.
@param configuration: le numero du fichier de configuration qui doit etre teste"""
def test_taille_fichier(identification, configuration):
    if identification == "initialisation":
        configurations_remplies = []
        for i in range(1, 7):
            if os.path.getsize("config/config" + str(i) + ".txt") != 0:
                configurations_remplies.append(i)
        return(configurations_remplies)
    else:
        taille_fichier = os.path.getsize("config/config" + str(configuration) + ".txt")
        if taille_fichier == 0:
            with open("config/defaut.txt", "r") as defaut_file:
                with open("config/config" + str(configuration) + ".txt", "w") as file:
                    defaut_fichier = defaut_file.read()
                    for i in range(len(defaut_fichier)):
                        file.write(defaut_fichier[i])
        return(taille_fichier)


"""Cette fonction est appelee quand l'utilisateur change de configuration sur la page web.
Elle envoit alors les informations du fichier de la configuration demandee, s'il n'est pas vide.
-----------------------------------------------------------------------------------------------
@param config: numero de la configuration chargee.
@param client: pour pouvoir communiquer avec envoyeur_message_page()"""
def changement_fichier(config, client):    
    chemin = "config/config" + str(config) + ".txt"

    test.envoyeur_message_page("C0.Conf.C:"+str(config), client)                          #on envoit le numero de configuration qui est changee
    with open(chemin, "r") as file :
        texte = file.read()
        
        univers = int(texte[0] + texte[1] + texte[2])                                      #on recupere dans le fichier la taille de l'univers
        message = "C0.Init.U:" + str(univers)                                              #puis prepare son message
        test.envoyeur_message_page(message, client)                                        #et on l'envoit
        for i in range(len(texte)):
            if texte[i] == "C" and texte[i+1] == "0":
                message = "C0.Init.N:" + texte[i+7] + texte[i+8] + texte[i+9] + texte[i+10]   #on recupere le nom d'un fader
                test.envoyeur_message_page(message, client)                                   #et on l'envoit


                message = "C0.Init.V:" + texte[i+4] + texte[i+5] + texte[i+6]               #on recupere la valeur de ce fader
                test.envoyeur_message_page(message, client)                                 #puis on l'envoit


        test.envoyeur_message_page("C0.Init.E", client)                             #on previent comme quoi l'initialisation est terminee
        
        file.seek(0)                                                                #on revient au debut du fichier
        valeur_master = texte[4] + texte[5] + texte[6]                              #on recupere la valeur du master
        message = "C0.Mast.V:" + valeur_master                                      #puis on prepare son message        
        test.envoyeur_message_page(message, client)                                 #et on l'envoit        
    return(univers)


"""Cette fonction est appellee si l'utilisateur decide de charger une configuration au fichier vide.
 Elle remplit alors ce fichier de 64 faders, tous a 0."""
def fichier_par_defaut(configuration):
    chemin = "config/config" + str(configuration) + ".txt"
    with open(chemin, "w") as file:
        file.write("064M000")
        for i in range(1, 65):
            if i < 10:
                file.write("C00" + str(i)+ "000" + "F00" + str(i))
            else:
                file.write("C0" + str(i) + "000" + "F0" + str(i))