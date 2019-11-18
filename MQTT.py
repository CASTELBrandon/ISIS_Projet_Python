from libMQTT.src.paho.mqtt import client as mqtt


class Serveur():
    def __init__(self, _serveur, _port, _message, _login, _mdp):
        self.serveur = _serveur
        self.port = _port
        self.message = _message
        self.login = _login
        self.mdp = _mdp

    def get_serveur(self):
        return self.serveur

    def get_port(self):
        return self.port

    def get_message(self):
        return self.message

    def get_login(self):
        return self.login

    def get_mdp(self):
        return self.mdp

    def saisie_serveur(self, saisie):
        self.serveur = saisie

    def saisie_port(self, saisie):
        self.port = saisie

    def saisie_message(self, saisie):
        self.message = saisie

    def saisie_login(self, saisie):
        self.login = saisie

    def saisie_mdp(self, saisie):
        self.mdp = saisie

    """
        Cette fonction cree la connection entre la page et le serveur MQTT.
        Elle appelle la fonction d'initialisation avant de lancer la boucle de connection.
    """
    def connection(self):
        #/*** CREATION DE L'INSTANCE CLIENT ***/
        client = mqtt.Client(self.login)

        #/*** CONNECTION ***/
        client.username_pw_set(self.login, self.mdp)
        client.connect(self.serveur, self.port)
        client.loop_start()
        client.on_message = self.on_message                            #appel de la fonction on_message() qui se lancera quand on recevra un message

        #/*** DEFINITION DU SUJET ***/
        client.subscribe("general")

    """
        Cette fonction s'active quand nous recevons un message MQTT de la part de la page web.
        Elle envoit ensuite le message vers la fonction traitement() pour agir en consequence de sa nomenclature.
        ---------------------------------------------------------------------------------------------------------
        @param client : le parametre qui nous permet d'utiliser les fonctions de la librairie MQTT.
        @param userdata : ? nous n'avons pas eu le temps de trop se pencher sur sa fonction. Il n'a cependant pas l'air d'etre tres utile ici.
        @param message : le message recu, que l'on va tout de suite envoyer vers traitement().
    """
    def on_message(self, client, userdata, message):
        MESSAGE = str(message.payload.decode("utf-8")) #on convertit le message en string car la librairie MQTT le code.

        if MESSAGE.find("C1.") != -1:                  #si le message est envoye par la page (mot code C1), alors...
            #print("Ce message a ete recu", MESSAGE)
            traitement(client, MESSAGE)                #... on l'envoit au traitement.

    """
        Cette fonction traite les messages recus. Ils proviennent directement de la fonction on_message().
        Elle effectue des actions suivant la nomenclature du message.
        Le message commence toujours pas C0 ou C1.
        C0 quand c'est le code python qui est l'expediteur, C1 quand c'est la page.
        Voici les differentes actions :
                    - Mast = action sur le master
                    - Syst = demande de rafraichissement
                    - Rese = demande de reset
                    - Conf = action sur une configuration
                    - Cxxx.V = action sur un fader (valeur)
                    - Cxxx.N = action sur un fader (nom)
                    - Init = pracision a la page que l'information envoyee fait partie d'un cycle d'initialisation
        ------------------------------------------------------------------------------------------------------
        @param client : pour pouvoir utiliser les fonctions propres a la librairire MQTT.
        @param message : le message qui provient directement de la fonction on_message.
    """
    def traitement(client, message):
        global configuration_actuelle
        global univers

        # /*** MESSAGE CHANGEMENT VALEUR DU MASTER ***/
        #ecriture de la nouvelle valeur du master dans le fichier de la configuration correspondante
        if message.find("Mast") != -1:
            nouvelle_valeur = recuperateur_valeur(message)
            fdf.ecriture_fichier(configuration_actuelle, nouvelle_valeur, "M", "Master")
            envoyeur_dmx("0", valeur, "master")


        #/*** MESSAGE DEMANDE DE RAFRAICHISSEMENT ***/
        #lecture du fichier de la configuration demandee et envoit de son contenu
        elif message.find("Syst") != -1:
            univers = fdf.changement_fichier(configuration_actuelle, client)


        #/*** MESSAGE DEMANDE DE RESET ***/
        #reinitialisation de la configuration demandee
        elif message.find("Rese") != -1:
            numero_config = message[8]
            initialisation_univers(numero_config, client)



        #/*** MESSAGE CHANGEMENT DE VALEUR DE FADER ***/
        #ecriture de la nouvelle valeur du fader dans le fichier de la configuration correspondante
        elif message.find(".V:") != -1 and message.find("C1.C") != 1:
            nom_fader = recuperateur_nom(message)                                              #on recupere le matricule du fader dans le message
            nouvelle_valeur = recuperateur_valeur(message)                                     #on recupere la nouvelle valeur du fader dans le message
            fdf.ecriture_fichier(configuration_actuelle, nouvelle_valeur, nom_fader, "Valeur") #on va ecrire cette nouvelle valeur dans le fichier de configuration
            envoyeur_dmx(nom_fader, nouvelle_valeur, "fader")




        #/*** MESSAGE CHANGEMENT CONFIGURATION ***/
        #chargement du fichier de la nouvelle configuration et envoi de son contenu
        elif message.find("C1.Conf.C") != -1:                                                  #on recupere le numero de la configuration demandee
            configuration_actuelle = int(message[10]) +1
            configuration = str(configuration_actuelle)
            taille_fichier = fdf.test_taille_fichier("autre", configuration)                   #on regarde si le fichier de la configuration demandee est vierge

            if taille_fichier == 0:                                                            #si pas de chance, il est vide
                print("\nLa configuration numero ", configuration,
                      " est vide. Chargement d'une version par defaut...")
                fdf.fichier_par_defaut(configuration_actuelle)                                 #on rempli le fichier d'une version par defaut
                fdf.changement_fichier(configuration_actuelle, client)                         #on envoit a la table les informations dans le fichier
            else:                   #S'il y a des choses dedans
                print("\nChargement de la configuration numero ", configuration, ".")          #si il y a quelque chose dans le fichier

                univers = fdf.changement_fichier(configuration_actuelle, client)               #alors on envoit ses informations a la table



        #/*** MESSAGE DE CHANGEMENT DE NOM FADER ***/
        #ecriture du nouveau nom du fader dans le fichier de la configuration correspondante
        elif message.find("C1.C") != -1 and message.find(".N:") != 1:
            ancien_nom = recuperateur_nom(message)                                             #on recupere le matricule du fader dans le message
            nouveau_nom = message[10] + message[11] + message[12] + message[13]                #on recupere le nouveau nom dans le message
            fdf.ecriture_fichier(configuration_actuelle, nouveau_nom, ancien_nom, "Nom")       #on ecrit dans le fichier le nouveau nom du fader

    """
        Cette fonction envoie les messages a la table.
        Puis met a jour le fichier de la configuration actuelle si la valeur d'un fader a ete changee.
        ----------------------------------------------------------------------------------------------
        @param message : le message a envoyer.
        @param client : pour pouvoir utiliser les fonctions propres a la librairire MQTT.
    """
    def envoyeur_message_page(message, client):
        client.publish("general", message)
        #print("Ce message a ete envoye", message)
        #/*** SI ON ENVOIT UN MESSAGE QUI CHANGE LA VALEUR D'UN FADER ***/
        if message.find(".V") != -1:
                enregistreur_configuration(configuration_actuelle)
                nom_fader = recuperateur_nom(message)                                                 #on recupere le matricule du fader
                nouvelle_valeur = recuperateur_valeur(message)                                        #on recupere sa valeur
                if message.find("Init") == -1:
                    fdf.ecriture_fichier(configuration_actuelle, nouvelle_valeur, nom_fader, "Valeur")#on met a jour le fichier

    def deformateur_de_valeur(valeur):
        deformatage = ""
        for i in range(len(valeur)):
            if valeur[i] != "0":
                deformatage = deformatage + valeur[i]

        if valeur[0] + valeur[1] + valeur[2] == "000":
            deformatage = "0"


        if valeur[0] == "0" and valeur[1] != "0" and valeur[2] == "0":
            deformatage = valeur[1] + "0"

        #print("le deformatage :", deformatage)
        return int(deformatage)

    """
        Cette fonction recupere le nom d'un fader dans un message.
        -------------------------------------------------------------
        @param message : le message qui doit etre traite.
    """
    def recuperateur_nom(message):
        nom_fader = message[3] + message[4] + message[5] + message[6]
        return(nom_fader)

    """
        Cette fonction recupere la valeur d'un fader dans un message.
        ---------------------------------------------------------------
        @param message : le message qui doit etre traite
    """
    def recuperateur_valeur(message):
        valeur_fader = message[10] + message[11] + message[12]
        return(valeur_fader)

    def envoi_fichier_table(configuration, client):
        chemin = "config/config" + str(configuration) + ".txt"
        fichier = open(chemin, "r")
        informations = fichier.read()
        for i in range(len(informations)): #On parcourt les informations du fichier
            if informations[i] == "C":
                nom = informations[i+1] + informations[i+2] + informations[i+3] #Recuperation du nom du fader
                valeur = informations[i+4] + informations[i+5] + informations [i+6] #Recuperation de la valeur du fader
                message = "C1.F" + nom + ".V:" + valeur
                traitement(client, message)

    def envoi_fichier_page(configuration, client):
        global nb_projecteur
        chemin = "config/config" + str(configuration) + ".txt"
        fichier = open(chemin, "r")
        informations = fichier.read()
        for i in range(len(informations)):
           if informations[i] == "C":
               nom = informations[i + 1] + informations[i + 2] + informations[i + 3]
               valeur = informations[i + 4] + informations[i + 5] + informations[i + 6]
               message = "C0.F" + nom + ".V:" + valeur
               client.publish("general", message)
               print("Ce message a ete envoye :", message)

    def createur_nom(identification, condition):
        global matricule_fader
        global nom_fader
        global univers

        #/*** SI ON DOIT CREER UN MATRICULE ***/
        if identification == "initialisation":
            if condition < 10:
                matricule_fader = "C00" + str(condition)
            if condition >= 10 and condition < 100:
                matricule_fader = "C0" + str(condition)
            print("matricule cree:", matricule_fader)
            return (matricule_fader)

        #/*** SI ON DOIT CREER UNE TAILLE D'UNIVERS ***/
        if identification == "univers":
            if condition < 10:
                univers = "00" + str(condition)
            if condition >= 10 and condition < 100:
                univers = "0" + str(condition)
            return(univers)

        #/*** SI ON DOIT CREER UN NOM ***/
        if identification == "NOM":
            if condition < 10:
                nom_fader = "F00" + str(condition)
            if condition >= 10 and condition < 100:
                nom_fader = "F0" + str(condition)
            return (nom_fader)
