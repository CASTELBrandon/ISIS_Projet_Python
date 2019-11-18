import MQTT
#from /home/pi/Desktop/MQTT/libMQTT/src/paho/mqtt/client.py as mqtt
import fonctions_de_fichier as fdf
import time, random, os
import serial
#import pause as p
import struct
import threading

# Serial Setup for DMX transmission
ser = serial.Serial(
    port='/dev/ttyS0',
    baudrate = 250000,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=0
   )



# Initialize variable
universize = 512
dmxbuffer = [0] * universize
master = 0

################################################################################
#                                   FONCTIONS                                  #
################################################################################

# Send Channels through DMX
def dmxfonction(dmxbuffer):
    global universize
    global master
    while True:
        tosend=dmxbuffer
        dmxbuffer[1] = master
        #print(tosend)
        ser.break_condition = True
        time.sleep(0.001)               # Send Break
        ser.break_condition = False
        #ser.write(struct.pack('<B', 0)) # Start Code
        for i in range(0, universize, 1):
            ser.write(struct.pack('<B', tosend[i]))


processThread = threading.Thread(target=dmxfonction, args=(dmxbuffer,))
processThread.start()


def envoyeur_dmx(matricule, valeur, identification):
    """if idenfication == "master":
        valeur = deformateur_de_valeur(valeur)

        dmxbuffer[1] = valeur
        print(dmxbuffer[1])"""

    #if identification == "fader":
    def_matricule = deformateur_de_valeur(matricule[1]+matricule[2]+matricule[3])
    def_valeur = deformateur_de_valeur(valeur)
    dmxbuffer[def_matricule+1] = def_valeur


"""
    Cette fonction demande a l'utilisateur s'il veut charger ou non les anciennes configurations enregistrees.
    -------------------------------------------------------------------------------------------------------------
    @param client : pour pouvoir utiliser les fonctions propres a la librairire MQTT dans les fonctions rattachees uniquement a celle-ci.
"""
def initialisation_configuration():
    global configurations_remplies
    global configuration_actuelle
    configurations_remplies = fdf.test_taille_fichier("initialisation", 0) #On regarde quelles configurations sont remplies ou vides.

    if len(configurations_remplies) != 0: #Si le tableau n'est pas vide
        print("\n Le systeme vient de demarrer, voulez vous recuperer les anciennes configurations ? [1 = Oui, 2 = Non]")
        reponse = int(input())

        #/*** SI L'UTILISATEUR VEUT RECUPERER LES CONFIGURATION ***/
        if reponse == 1:
            print("\nVoici les configurations qui ont ete enregistrees :")
            for i in range(len(configurations_remplies)):
                    print(configurations_remplies[i])

            print("\nLaquelle de ces configurations voulez vous generer ?")
            numero_configuration = int(input())
            if numero_configuration in configurations_remplies:
                print("\nVous voulez generer l'ancienne configuration numero ", numero_configuration, ", est-ce exact ? [1 = Oui, 2 = Non]")
                reponse = int(input())
                if reponse == 1:
                    print("Configuration numero", numero_configuration, "chargee !")
                    #envoi_fichier_page(numero_configuration, client)
                    enregistreur_configuration(numero_configuration)



    #/*** SI L'UTILISATEUR VEUT CREER UNE CONFIGURATION ***/
    print("\nQuelle configuration voulez vous creer ? (1, 2, 3, 4, 5, 6)")
    numero_configuration = int(input())
    if numero_configuration != 7:
        print("\nVous voulez creer la configuration numero", numero_configuration, "est-ce exact ? [1 = Oui, 2 = Non]")
        reponse = int(input())
        if reponse == 1:
            configuration_actuelle = numero_configuration        #on met a jour le numero de la configuration actuelle


"""
    Cette fonction est appellee quand l'utilisateur doit entierement creer une configuration.
    -------------------------------------------------------------------------------------------
    @param configuration: pour savoir quelle configuration on veut creer.
    @param client: pour pouvoir envoyer des messages.
"""
def initialisation_univers(configuration, client):
    #envoyeur_message_page("C0.Conf.C:" + str(configuration), client) #On previent la page comme quoi on va toucher la configuration choisie.

    fdf.raz_fichier(configuration) #Remise a zero du fichier de la configuration choisie.

    flag_initialisation = True
    while flag_initialisation == True:
        global univers
        global taille_univers

        flag_limite_univers = True
        while flag_limite_univers == True:
            print("\nQuelle est la taille de votre univers DMX ? \n")
            taille_univers = int(input())
            if taille_univers > 64:
                print("\nMince! Attention, votre univers ne doit pas depasser 64. :/")
            else:
                break

        print("\nVous avez donc un univers de taille ", taille_univers, " est ce exact ? [1 = Oui, 2 = Non] \n")
        reponse = int(input())
        if reponse == 1:
            univers = createur_nom("univers", taille_univers)                   #On adapte le format de taille_univers pour qu'il ait toujours 3caracteres.
            envoyeur_message_page("C0.Init.U:" + str(univers), client)
            fdf.maj_fichier(configuration, str(univers))                        #On ecrit AU DEBUT DU FICHIER, le taille de l'univers de la configuration.
            fdf.maj_fichier(configuration, "M000")                              #On ecrit JUSTE APRES la valeur du master
            for j in range(taille_univers):
                matricule_fader = createur_nom("initialisation", j+1)           #On cree les messages pour la table.
                envoyeur_message_page("C0.Init.N:" + matricule_fader, client)   #On envoit a la page les faders qui sont crees.
                liste_fader.append(matricule_fader)
                fdf.maj_fichier(configuration, matricule_fader)                 #On met a jour le fichier de la configuration correspondante.

                client.publish("general", "C0.Init.V:000")                      #On envoit a la page la valeur par defaut des faders
                fdf.maj_fichier(configuration, "000")                           #On met a jour le fichier de configuration correspondante.

                nom_fader = createur_nom("NOM", j+1)                            #on cree le nom du fader par defaut
                fdf.maj_fichier(configuration, nom_fader)                       #puis on met a jour le fichier de la configuration correspondante.


            envoyeur_message_page("C0.Init.E", client) #On previent la table que l'initialisation est terminee.
            enregistreur_configuration(configuration)
            return (True)
    else:
        return(False)


def enregistreur_configuration(configuration):
    global master
    chemin = ("config/config" + str(configuration) + ".txt")
    with open(chemin, "r") as file:
            texte = file.read()
            master = deformateur_de_valeur(texte[4]+texte[5]+texte[6])
            informations_config[0] = master
            for i in range(len(texte)):
                if texte[i] == "C" and texte[i+1] == "0":
                    matricule = deformateur_de_valeur(texte[i+1]+texte[i+2]+texte[i+3])
                    valeur = deformateur_de_valeur(texte[i+4]+texte[i+5]+texte[i+6])
                    informations_config[matricule]= valeur
            for i in range(len(informations_config)):
                dmxbuffer[i+1] = informations_config[i]


################################################################################
#                       FONCTIONS DE CONNEXION                                 #
################################################################################

"""
    Cette fonction connecte la rpi a la page web.
    Cette page web est stockee dans la rpi grace a Apache. L'adresse est donc 127.0.0.1.
    On parle a cette page grace un serveur Mosquitto, avec des messages MQTT.
"""
def saisieCoordonnes():

    serveurTest.saisie_serveur("127.0.0.1")   #ici est ecrit l'adresse de la page
    serveurTest.saisie_port(int(1883))        #ici est ecrit le port MQTT (1883)
    serveurTest.saisie_login("root")          #ici le login...
    serveurTest.saisie_mdp("root")            #... et son mot de passe


################################################################################
#                               INITIALISATION                                 #
################################################################################





################################################################################
#                            LANCEMENT DU PROGRAMME                            #
################################################################################

if __name__ == "__main__":
    #Objet du serveur MQTT
    serveurTest = MQTT.Serveur("serveur", 0, "message", "login", "mdp")
    liste_fader = []
    taille_univers = 0
    derniere_position = []
    stockage_message = []
    configuration_actuelle = 1
    configurations_remplies = []
    informations_config = [0]*64

    saisieCoordonnes()
    serveurTest.connection()
    initialisation_configuration()
