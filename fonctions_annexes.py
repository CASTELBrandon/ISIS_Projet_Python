from libMQTT.src.paho.mqtt import client as mqtt

import fonctions_de_fichier as fdf
import time, random, serial, struct
import smbus
import RPi.GPIO as GPIO
import os


"""Ici sont ecrites les interruptions qui vont reagir a l'evenement : ''le pin que j'observe a change d'etat''."""
#declaration et initialisation des gpios
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT) #fader 1
GPIO.setup(27, GPIO.OUT) #fader 2
#GPIO.setup(3, GPIO.IN)
#GPIO.setup(4, GPIO.IN)
#GPIO.setup(5, GPIO.IN)
#GPIO.setup(6, GPIO.IN)
#GPIO.setup(7, GPIO.IN)
#GPIO.setup(8, GPIO.IN)
#GPIO.setup(9, GPIO.IN)
#GPIO.setup(10, GPIO.IN)
#GPIO.setup(11, GPIO.IN)
#GPIO.add_event_detect(17, GPIO.RISING, callback=my_callback1, bouncetime=0) #fader 1
#GPIO.add_event_detect(27, GPIO.RISING, callback=my_callback2, bouncetime=0) #fader 2
#GPIO.add_event_detect(3, GPIO.RISING, callback=my_callback3, bouncetime=0)
#GPIO.add_event_detect(4, GPIO.RISING, callback=my_callback4, bouncetime=0)
#GPIO.add_event_detect(5, GPIO.RISING, callback=my_callback5, bouncetime=0)
#GPIO.add_event_detect(6, GPIO.RISING, callback=my_callback6, bouncetime=0)
#GPIO.add_event_detect(7, GPIO.RISING, callback=my_callback7, bouncetime=0)
#GPIO.add_event_detect(8, GPIO.RISING, callback=my_callback8, bouncetime=0)
#GPIO.add_event_detect(9, GPIO.RISING, callback=my_callback9, bouncetime=0)
GPIO.add_event_detect(10, GPIO.RISING, callback=my_callback10, bouncetime=300) #page_up
GPIO.add_event_detect(11, GPIO.RISING, callback=my_callback11, bouncetime=300) #page_down


#TODO Mettre a jour ce commentaire
"""Cette fonction demande a l'utilisateur toutes les informations necessaires a la connection soit : 
            - l'adresse du serveur,
            - le port (qui sera toujours 1883 car nous causons en MQTT),
            - le login de l'utilisateur,
            - le mot de passe correspondant.
Toutes ces informations seront enregistrees dans l'objet serveurTest de la classe Serveur (ecrite en bas de la page)"""
def saisieCoordonnes():
    print("Adresse du serveur :")
    serveurTest.saisie_serveur("127.0.0.1")
    print("\nPort (1883 est le port MQTT) :")
    serveurTest.saisie_port(int(1883))
    print("\nLogin :")
    serveurTest.saisie_login("root")
    print("\nMot de passe :")
    serveurTest.saisie_mdp("root")
    print("\n")
    print(serveurTest.get_serveur(), serveurTest.get_port(), serveurTest.get_login(), serveurTest.get_mdp())


#TODO Mettre a jour ce commentaire
"""Cette fonction cree une instance client et etablit une laison entre lui et le serveur.
Elle recupere les informations dans l'objet serveurTest de la classe Serveur.
Les messages ont une nomenclature specifique :

                            expediteur.type du message.parametre:valeur

    Expediteur :
            - 00 : le serveur lui meme,
            - 01 : la page web.

    Type du message :
            - Clr : reglage couleur,
            - Mtr : reglage intensite generale,
            - Sys : message de systeme.
        
    parametre : 
            - Clr.R : reglage couleur rouge,
            - Clr.G : reglage couleur verte,
            - Clr.B : reglage couleur bleue,
            
            - Mtr.V : reglage valeur intensite,
                
            - Sys.R : demande de recuperation des valeurs en cas de deconnection inopinee de la page web."""
def connectionEtEnvoi():
    port = serveurTest.get_port()
    serveur = serveurTest.get_serveur()
    login = serveurTest.get_login()
    mdp = serveurTest.get_mdp()

    #/*** CReATION DE L'INSTANCE CLIENT ***/
    client = mqtt.Client(login)

    #/*** CONNECTION ***/
    client.username_pw_set(login, mdp)
    client.connect(serveur, port)
    client.loop_start()
    client.on_message = on_message #Appel de la fonction permettant d'effectuer des actions lors de l'evenement : "reception de message"

    #/*** DEFINITION DU SUJET ***/
    client.subscribe("general")

    #/*** BOUCLE DE CONNECTION ***/
    # time.sleep(4)
    i = "Initialisation"
    flag_initialisation = True

    #/*** INITIALISATION DE L'UNIVERS ET DES CANAUX***/
    global flag_univers
    while flag_univers != True:
        flag_univers = initialisation_univers(client)
    flag_univers = False

    while flag_univers != True:
        flag_univers = initialisation_canaux(client)

    #/*** INITIALISATION DE LA CONNECTION DMX ***/
    #ser.send_break(duration=0.001)
    #ser.write(struct.pack('<H', 0))

   #/*** INITIALISATION DU BUS ***/
    global bus
    bus = smbus.SMBus(1)

	#adresses i2c des attinys
	add1 = 0x28
	add2 = 0x29
	add3 = 0x30
	
	#initialisation des variables servant a comparer la valeur du fader avec la valeur precedemment relevee
	rep_add1 = 0
	rep_add2 = 0
	
    while i != "stop":
        global flag_callback1, flag_callback2, flag_callback3, flag_callback4, flag_callback5, flag_callback6, \
               flag_callback7, flag_callback8, flag_callback9, flag_callback10, flag_callback11, numero_page
        #///**** CONDITIONS D'INTERRUPTIONS ****///# TODO mettre en commentaire ou commence la fonction my_callback et les interruptions
        #/*** FADER 1 ***/
		GPIO.output(17, GPIO.LOW)
        bus.write_byte(add1, int(33)) #On previent la table comme quoi ona detecte l'interruption
        valeur = bus.read_byte(add1) #On recupere la valeur
		canal_DMX = 8 * numero_page + 1 #On calcul le canal DMX correspondant
        message = creation_message("canal", canal_DMX, valeur)#creation du message
        client.publish("general", message) #Envoi du message
        derniere_position[canal_DMX] = valeur  #On stocke la valeur
        dmx() #On appelle la fonction pour envoyer les valeurs vers les projecteurs
		if valeur != rep_add1 + 1 or valeur != rep_add1 - 1 or valeur != rep_add1:
			rep_add1 = valeur
		GPIO.output(17, GPIO.HIGH)

        # /*** FADER 2 ***/
		GPIO.output(27, GPIO.LOW)
        bus.write_byte(add2, int(33)) #On previent la table comme quoi ona detecte l'interruption
        valeur = bus.read_byte(add2) #On recupere la valeur
		canal_DMX = 8 * numero_page + 1 #On calcul le canal DMX correspondant
        message = creation_message("canal", canal_DMX, valeur)#creation du message
        client.publish("general", message) #Envoi du message
        derniere_position[canal_DMX] = valeur  #On stocke la valeur
        dmx() #On appelle la fonction pour envoyer les valeurs vers les projecteurs
		if valeur != rep_add2 + 1 or valeur != rep_add2 - 1 or valeur != rep_add2:
			rep_add2 = valeur
		GPIO.output(27, GPIO.HIGH)

        # /*** FADER 3 ***/
        if flag_callback3 == True:
            bus.write_byte(0x93, int(33))
            canal_DMX = 8 * numero_page + 3
            valeur = bus.read_byte(0x93)
            message = creation_message("canal", canal_DMX, valeur)
            client.publish("general", message)
            derniere_position[canal_DMX] = valeur
            flag_callback3 = False

        # /*** FADER 4 ***/
        if flag_callback4 == True:
            bus.write_byte(0x94, int(33))
            canal_DMX = 8 * numero_page + 4
            valeur = bus.read_byte(0x94)
            message = creation_message("canal", canal_DMX, valeur)
            client.publish("general", message)
            derniere_position[canal_DMX] = valeur
            flag_callback4 = False

        # /*** FADER 5 ***/
        if flag_callback5 == True:
            bus.write_byte(0x95, int(33))
            canal_DMX = 8 * numero_page + 5
            valeur = bus.read_byte(0x95)
            message = creation_message("canal", canal_DMX, valeur)
            client.publish("general", message)
            derniere_position[canal_DMX] = valeur
            flag_callback5 = False

        # /*** FADER 6 ***/
        if flag_callback6 == True:
            bus.write_byte(0x96, int(33))
            canal_DMX = 8 * numero_page + 6
            valeur = bus.read_byte(0x96)
            message = creation_message("canal", canal_DMX, valeur)
            client.publish("general", message)
            derniere_position[canal_DMX] = valeur
            flag_callback6 = False

        # /*** FADER 7 ***/
        if flag_callback7 == True:
            bus.write_byte(0x97, int(33))
            canal_DMX = 8 * numero_page + 7
            valeur = bus.read_byte(0x97)
            message = creation_message("canal", canal_DMX, valeur)
            client.publish("general", message)
            derniere_position[canal_DMX] = valeur
            flag_callback7 = False

        # /*** FADER 8 ***/
        if flag_callback8 == True:
            bus.write_byte(0x98, int(33))
            canal_DMX = 8 * numero_page + 8
            valeur = bus.read_byte(0x98)
            message = creation_message("canal", canal_DMX, valeur)
            client.publish("general", message)
            derniere_position[canal_DMX] = valeur
            flag_callback8 = False

        #/*** MASTER ***/
        if flag_callback9 == True:
            bus.write_byte(0x99, int(33))
            valeur = bus.read_byte(0x99)
            message = "C0.Mast.V:", valeur
            client.publish("general", message)
            global master
            master = valeur
            flag_callback9 = False
			
		#on affiche les valeurs des faders dans la console
		print "Fader 1 = ", rep_add1
		print "Fader 2 = ", rep_add2
		os.system("clear")
			
        # /*** BOUTON PAGE PRECEDENTE ***/
        if flag_callback10 == True:
            if numero_page >= 0:  # Page minimum = 0
                numero_page -= 1
                for j in range(1, 8):
                    sauvegarde[j] = derniere_position[8 * numero_page + j]
                    if j == 1:
                        bus.write_byte(add1, sauvegarde[j])
                    elif j == 2:
                        bus.write_byte(add2, sauvegarde[j])
                    elif j == 3:
                        bus.write_byte(0x93, sauvegarde[j])
                    elif j == 4:
                        bus.write_byte(0x94, sauvegarde[j])
                    elif j == 5:
                        bus.write_byte(0x95, sauvegarde[j])
                    elif j == 6:
                        bus.write_byte(0x96, sauvegarde[j])
                    elif j == 7:
                        bus.write_byte(0x97, sauvegarde[j])
                    elif j == 8:
                        bus.write_byte(0x98, sauvegarde[j])
            else:
                numero_page = 8
                for j in range(1, 8):
                    sauvegarde[j] = derniere_position[8 * numero_page + j]
                    if j == 1:
                        bus.write_byte(add1, sauvegarde[j])
                    elif j == 2:
                        bus.write_byte(add2, sauvegarde[j])
                    elif j == 3:
                        bus.write_byte(0x93, sauvegarde[j])
                    elif j == 4:
                        bus.write_byte(0x94, sauvegarde[j])
                    elif j == 5:
                        bus.write_byte(0x95, sauvegarde[j])
                    elif j == 6:
                        bus.write_byte(0x96, sauvegarde[j])
                    elif j == 7:
                        bus.write_byte(0x97, sauvegarde[j])
                    elif j == 8:
                        bus.write_byte(0x98, sauvegarde[j])
            flag_callback10 = False

            #/*** BOUTON PAGE SUIVANTE ***/
            if flag_callback11 == True:
                if numero_page <= 7: #Page maximum = 8
                    numero_page += 1
                    for j in range(1, 8):
                        sauvegarde[j] = derniere_position[8*numero_page + j]
                        if j == 1:
                            bus.write_byte(add1, sauvegarde[j])
                        elif j == 2:
                            bus.write_byte(add2, sauvegarde[j])
                        elif j == 3:
                            bus.write_byte(0x93, sauvegarde[j])
                        elif j == 4:
                            bus.write_byte(0x94, sauvegarde[j])
                        elif j == 5:
                            bus.write_byte(0x95, sauvegarde[j])
                        elif j == 6:
                            bus.write_byte(0x96, sauvegarde[j])
                        elif j == 7:
                            bus.write_byte(0x97, sauvegarde[j])
                        elif j == 8:
                            bus.write_byte(0x98, sauvegarde[j])
                else:
                    numero_page = 0
                    for j in range(1, 8):
                        sauvegarde[j] = derniere_position[8*numero_page + j]
                        if j == 1:
                            bus.write_byte(add1, sauvegarde[j])
                        elif j == 2:
                            bus.write_byte(add2, sauvegarde[j])
                        elif j == 3:
                            bus.write_byte(0x93, sauvegarde[j])
                        elif j == 4:
                            bus.write_byte(0x94, sauvegarde[j])
                        elif j == 5:
                            bus.write_byte(0x95, sauvegarde[j])
                        elif j == 6:
                            bus.write_byte(0x96, sauvegarde[j])
                        elif j == 7:
                            bus.write_byte(0x97, sauvegarde[j])
                        elif j == 8:
                            bus.write_byte(0x98, sauvegarde[j])
                flag_callback11 = False

    print("Fin de la connection")
    client.loop_stop()


"""Cette fonction cree ecrit les messages en fonction de des parametres qu'elle a en entree."""
def creation_message(identification, condition, valeur):
    if identification == "canal":
        global message
        if condition < 10:
            message = "C0.C00", condition, ".V:", valeur
        if condition >=10 and condition < 100:
            message = "C0.C0", condition, ".V:", valeur
        else:
            message = "C0.C", condition, ".V:", valeur

    if identification == "initialisation":

        if condition < 10:
            message = "C0.Init.N:C00", valeur
        if condition >=10 and condition < 100:
            message = "C0.Init.N:C0", valeur
        else:
            message = "C0.Init.N:C", valeur

    return (message)


"""Voici les fonctions qui seront appelees quand le programme aura detecte une interruption.
    Ces fonctions sont tres sujettes aux freez de programme si elles durent trop longtemps.
    Ainsi, on se contente de changer la valeur du booleen global correspondant a la pin GPIO,
    afin de prevenir le programme principal qu'il y a eu une interruption."""
def my_callback1():
    global flag_callback1
    flag_callback1 = True


def my_callback2():
    global flag_callback2
    flag_callback2 = True


def my_callback3():
    global flag_callback3
    flag_callback3 = True


def my_callback4():
    global flag_callback4
    flag_callback4 = True


def my_callback5():
    global flag_callback5
    flag_callback5 = True


def my_callback6():
    global flag_callback6
    flag_callback6 = True


def my_callback7():
    global flag_callback7
    flag_callback7 = True


def my_callback8():
    global flag_callback8
    flag_callback8 = True


def my_callback9():
    global flag_callback9
    flag_callback9 = True


def my_callback10():
    global flag_callback10
    flag_callback10 = True


def my_callback11():
    global flag_callback11
    flag_callback11 = True


"""Cette fonction effectue plusieurs actions a la reception d'un message.
Si le message respecte la nomenclature, et provient de la page web (01.), alors on traite le message."""
def on_message(client, userdata, message):
    MESSAGE = str(message.payload.decode("utf-8"))
    if MESSAGE.find("C1.") != -1:
        traitement(client, MESSAGE)


"""Cette fonction permet d'analyser les messages recus des utilisateurs"""
def traitement(client, message):
    if message.find("F") != -1:
        global numero_page
        global master
        canal_DMX = message[4] + message[5] + message[6] #On extrait le numero du fader
        derniere_position[canal_DMX] = int(message[10] + message[11] + message[12]) #On ecrase la derniere position de ce fader par la nouvelle
        for j in range(1, 8):
            if sauvegarde[j] != derniere_position[8 * numero_page + j]:  # On regarde si le fader est bien dans la page actuelle de la table
                sauvegarde[j] = derniere_position[8 * numero_page + j]   #Si c'est le cas, on change alors la valeur des faders
                if j == 1:
                    bus.write_byte(add1, sauvegarde[j])
                elif j == 2:
                    bus.write_byte(add2, sauvegarde[j])
                elif j == 3:
                    bus.write_byte(0x93, sauvegarde[j])
                elif j == 4:
                    bus.write_byte(0x94, sauvegarde[j])
                elif j == 5:
                    bus.write_byte(0x95, sauvegarde[j])
                elif j == 6:
                    bus.write_byte(0x96, sauvegarde[j])
                elif j == 7:
                    bus.write_byte(0x97, sauvegarde[j])
                elif j == 8:
                    bus.write_byte(0x98, sauvegarde[j])

    if message.find("Mast") != -1:
        master = int(message[10] + message[11] + message[12])
        bus.write_byte(0x99, master)

    if message.find("Conf.C") !=1:
        global configuration_actuelle
        configuration_actuelle = int(message[10])
        raz_fichier(configuration_actuelle)

    if message.find("Conf.N") !=1 :

        nom = message[10] + message[11] + message[12] + message[13]
        maj_fichier_nom(configuration_actuelle, nom)

    if message.find("Conf.V") !=1:

        valeur = message[10] + message[11] + message[12]
        maj_fichier_valeur(configuration_actuelle, valeur)

    if message.find("Conf.E") !=1:

        envoi_fichier_table(configuration_actuelle, client)


    """Si nous detectons que le message possede une nomenclature de demande de rafraichessement,
    alors nous envoyons a la page web les faders qui etaient presents  les dernieres posiions connues des faders de la table.
    Cette demande est utile si la page web rencontre une deconnection inopinee et perd tous ses reglages.
    Ces valeurs pour le rafraichissement sont reprises dans le tableau derniere_position."""
    #TODO renvoyer la configuration actuelle
    if message.find("Syst") != -1:
        # /*** ENVOI DE L'UNIVERS ***/
        message = "C0.Init.P:" + str(taille_univers)
        client.publish("general", message)
        print("Ce message a ete envoye :", message)

        # /*** ENVOI DES NOMS DE PROJECTEURS ET DE LEUR NOMBRE DE CANAUX ***/
        for i in range(len(liste_projecteur)):
            client.publish("general", liste_projecteur[i])
            print("Ce message a ete envoye :", liste_projecteur[i])

        # /*** ENVOIS DE LA FIN DU RAPPEL INITIALISATION ***/
        message = "C0.Init.E"
        client.publish("general", message)
        print("Ce message a ete envoye : ", message)

        # /*** ENVOI DES DERNIERES POSITIONS DES FADERS AVANT DECONNECTION ***/
        for i in range(len(derniere_position)):
            if i < 9:
                message = "C0.C00" + str(i + 1) + ".V:" + str(derniere_position[i])
                client.publish("general", message)
                print("Ce message a ete envoye :", message)
            if i >= 9 and i < 100:
                message = "C0.C0" + str(i + 1) + ".V:" + str(derniere_position[i])
                client.publish("general", message)
                print("Ce message a ete envoye :", message)
            else:
                message = "C0.C" + str(i + 1) + ".V:" + str(derniere_position[i])
                client.publish("general", message)
                print("Ce message a ete envoye :", message)

        # /*** ENVOI DU MASTER ***/
        message = "C0.Mast.V:" + str(master)
        client.publish("general", message)
        print("Ce message a ete envoye : ", message)


"""Cette fonction demande a l'utilisateur la taille de son univers.
Elle retourne une valeur booleenne suivant ses reponses.
Si True, alors l'initialisation est reussie.
Si False, alors on recommence cette initialisation grace a la boucle while dans la fonction parente."""
def initialisation_univers(client):
    global nb_projecteur

    # /*** On demande d'abord si l'utilisateur veut reprendre les anciennes configurations stockees dans les fichiers ***/
    print("\n Le systeme vient de demarrer, voulez vous recuperer les anciennes configurations ? [O = Oui, N = Non]")
    reponse = input()
    if reponse == "O":
        flag_configuration = True
        while flag_configuration == True:
            print("\nQuelle configuration voulez vous generer ? (0, 1, 2, 3, 4, 5)")
            numero_configuration = input()
            print("\nVous voulez generer l'ancienne configuration numero ", numero_configuration, ", est-ce exact ? [O = Oui, N = Non]")
            reponse = input()
            if reponse == "O":
                envoi_fichier_page(numero_configuration, client)
                envoi_fichier_table(numero_configuration, client)
                return (True)


    print("\n ---- Creation des nouvelles configurations. ----")
    print("\n Vous avez combien de projecteur ? \n")
    nb_projecteur = input()

    print("\n Vous avez donc\033[1m", nb_projecteur, "\033[0m est ce exact ? [O = Oui, N = Non] \n")
    reponse = str(input())
    if reponse == "O":
        return(True)
    else:
        return(False)


"""Cette fonction prend les valeurs enregistrees dans le tableau derniere_position pour les envoyer vers les projecteurs
 via le protocol DMX."""
def dmx():
    for j in range(len(derniere_position)):
        ser.write(struct.pack('<H', derniere_position[j] / 255 * master))


"""Cette fonction demande a l'utilisateur le nombre de canaux que demande chaque projecteur.
Elle cree des messages (respectant la nomenclature) destines a etre envoyes a la page web pour etre traites.
Ces messages sont stockes dans le tableau liste_projecteur en guise de sauvegarde pour une eventuelle demande de rafraichissement.
Puis elle envoie ces messages a la page web."""
def initialisation_canaux(client):
    global nb_projecteur
    global taille_univers
    global boucle
    boucle = ""
    i = 1
    memoire = 1
    # /*** CREATION DES CANAUX ***/
    while boucle != "fin":
        global taille_univers
        print("\n Combien de canaux prend le projecteur numero\033[1m ", i, " \033[0m ?\n")
        canaux = input()
        CANAUX = int(canaux)
        taille_univers += CANAUX
        print("Le projecteur numero\033[1m ", i, "\033[0m prend\033[1m ", canaux,
              "\033[0m canaux, est ce exact ? [O = Oui, N = Non]")
        reponse = str(input())
        # /*** CREATION ET STOCKAGE DES MESSAGES ***/
        if reponse == "O":
            for j in range(CANAUX):
                message = creation_message("initialisation", memoire, memoire) #creation
                liste_projecteur.append(message)  #stockage
            i += 1
            if i > int(nb_projecteur):
                # /*** ENVOIS DU MESSAGE DE FIN D INITIALISATION ***/
                message = "C0.Init.E"  # creation
                client.publish("general", message)  #envoi
                boucle = "fin"
    for i in range(taille_univers):
        derniere_position.append(0)
    init_fichier()
    return (True)

#TODO maj ce commentaire
"""Cette fonction a pour but de mettre a jour les fichiers de configs.
Ces fichiers (au nombre de 6) sauvegardent une configuration de fader chacun."""
def init_fichier():
    #/*** INITIALISATION DES FICHIERS ***/
    fichier = open("config/config0.txt", "w")
    for i in range(len(liste_projecteur)):
        message = liste_projecteur[i]  # recuperation du message indiquant le nom du fader
        nom_projecteur = message[11] + message[12] + message[13] + message[14]  # extraction du nom
        fichier.write(nom_projecteur)  # ecriture du nom dans le fichier
        for j in range(len(derniere_position)):
            fichier.write(str(derniere_position[j]))  # ecriture de la valeur du fader dans le fichier
    fichier.close()

    fichier = open("config/config1.txt", "w")
    for i in range(len(liste_projecteur)):
        message = liste_projecteur[i]
        nom_projecteur = message[11] + message[12] + message[13] + message[14]
        fichier.write(nom_projecteur)
        fichier.write(nom_projecteur)
        for j in range(len(derniere_position)):
            fichier.write(str(derniere_position[j]))
    fichier.close()

    fichier = open("config/config2.txt", "w")
    for i in range(len(liste_projecteur)):
        message = liste_projecteur[i]
        nom_projecteur = message[11] + message[12] + message[13] + message[14]
        fichier.write(nom_projecteur)
        fichier.write(nom_projecteur)
        for j in range(len(derniere_position)):
            fichier.write(str(derniere_position[j]))
    fichier.close()

    fichier = open("config/config3.txt", "w")
    for i in range(len(liste_projecteur)):
        message = liste_projecteur[i]
        nom_projecteur = message[11] + message[12] + message[13] + message[14]
        fichier.write(nom_projecteur)
        fichier.write(nom_projecteur)
        for j in range(len(derniere_position)):
            fichier.write(str(derniere_position[j]))
    fichier.close()

    fichier = open("config/config4.txt", "w")
    for i in range(len(liste_projecteur)):
        message = liste_projecteur[i]
        nom_projecteur = message[11] + message[12] + message[13] + message[14]
        fichier.write(nom_projecteur)
        fichier.write(nom_projecteur)
        for j in range(len(derniere_position)):
            fichier.write(str(derniere_position[j]))
    fichier.close()

    fichier = open("config/config5.txt", "w")
    for i in range(len(liste_projecteur)):
        message = liste_projecteur[i]
        nom_projecteur = message[11] + message[12] + message[13] + message[14]
        fichier.write(nom_projecteur)
        fichier.write(nom_projecteur)
        for j in range(len(derniere_position)):
            fichier.write(str(derniere_position[j]))
    fichier.close()
    #TODO envoyer les changements de configuration à la table


"""Cette fonction vide le fichier stockant les anciennes valeurs d'une configuration.
Elle prend en parametre la configuration courrante."""
def raz_fichier(configuration):
    chemin = "config/config" + str(configuration) + ".txt"
    fichier = open(chemin, "w")
    fichier.close()


"""Cette fonction remplit un fichier des nouvelles valeurs de la configuration actuelle de la page.
Son contenu alterne entre nom du projecteur - sa valeur.
Elle prend en parametre la configuraton courrante, et le nom du fader destine a etre sauvegarde."""
def maj_fichier_nom(configuration, nom):
    chemin = "config/config" + str(configuration) + ".txt"
    fichier = open(chemin, "a")
    fichier.write(nom)
    fichier.close()


"""Cette fonction fait la meme chose que maj_fichier_nom, mais pour les valeurs du fader."""
def maj_fichier_valeur(configuration, valeur):
    chemin = "config/config" + str(configuration) + ".txt"
    fichier = open(chemin, "a")
    fichier.write(valeur)
    fichier.close()

"""Une fois la mise a jour d'un fichier effectuee apres le changement d'une configuration,
 cette fonction envoie ses informations vers la table."""
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


"""Cette fonction fait la meme chose que envoi_fichier_table, mais a la place,
 elle envoie les donnees stockees dans les fichiers a la page."""
def envoi_fichier_page(configuration, client):
    global nb_projecteur
    chemin = "config/config" + configuration + ".txt"
    fichier = open(chemin, "r")
    informations = fichier.read()
    for i in range(len(informations)):
       pass






"""Voici la classe serveur qui est la pour enregistrer les informations necessaires a la connection."""
class Serveur():
    def __init__(self, serveur, port, message, login, mdp):
        self.serveur = serveur
        self. port = port
        self.message = message
        self.login = login
        self.mdp = mdp

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


"""Ici, l'initialisation de l'objet serveurTest de la classe Serveur."""
serveurTest = Serveur("serveur", 0, "message", "login", "mdp")

"""Ici, l'initialisation des booleens globaux qui serviront a prevenir le programme qu'une interruption a eu lieu, en la rendant 
 la plus courte possible (on change juste la valeur de ces flags)."""

flag_callback1 = flag_callback2 = flag_callback3 = flag_callback4 = flag_callback5 = flag_callback6 = \
flag_callback7 = flag_callback8 = flag_callback9 = flag_callback10 = flag_callback11 = False

"""Cette variable indique le numero de page actuelle sur la table."""
numero_page = 0

"""Ce booleen est juste la pour perpetuer la boucle d'initialisation jusqu'a ce que l'utilisateur donne un nombre correcte pour son univers. """
flag_univers = False

"""Cette variable sert a garder en memoire le nombre de projecteur qu'il y a dans l'univers de l'utilisateur."""
nb_projecteur = 0

"""Voici le tableau destine a enregistrer les messages (respectant la nomenclature) 
d'initialisation a envoyer a la page web pour son demarrage.
Il regroupe les messages par projecteur dans cet ordre:
    — le nom du premier projecteur,
    — le nombre de ''sous-canaux'' qu'il prend."""
liste_projecteur = []


"""Cette variable globale sert a stocker le nombre total de canaux que l'utilisateur utilise pour sa session"""
taille_univers = 0

#TODO commentaire a mettre a jour
"""Voici le tableau destine a enregistrer les dernieres positions connues des faders de la table.
On choisit de l'initialiser avec la valeur 128 pour la premiere connection avec la page web.
En effet, cette derniere envoie une commande refresg a chaque connection.
Il faut donc que le tableau soit comprehensible pour la page des la premiere connection."""
derniere_position = [0]*taille_univers

"""Voici le tableau destine a stocker les valeurs des faders de la page actuelle
afin de pouvoir les comparer aux valeurs recues."""
sauvegarde = [0]*8

"""Cette variable possede la meme fonction que le tableau derniere_position, mais juste pour la valeur du Master."""
master = 0

"""Cette variable stocke le numero de la configuration courrante."""
configuration_actuelle = 0

"""Voici l'initialisation de la connection DMX."""
ser = serial.Serial(port='/dev/ttyAMA0', baudrate=250000, parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS,
                    timeout=None)