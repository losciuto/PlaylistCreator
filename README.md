[![License](https://img.shields.io/badge/License-GPLv3-green.svg)](https://github.com/losciuto/vlcremote/blob/master/LICENSE)
# Playlist Creator

Raccoglie i video presenti nelle unità disco o chiavette USB (non consigliato), ne memorizza le informazioni, prendendo dai file <nome del video>.nfo style Kodi, se presenti, i metadati in un file SQLite. Una volta memorizzati i dati, è possibile creare delle playlist secondo diversi criteri. 

* Playlist casuali
sceglie, dopo averne stabilito il numero, una serie di video scelti secondo il criterio RANDOM() di SQLite.
* Playlist manuale:
si scelgono i video voluti manualmente.
* Playlist degli ultimi video scaricati:
ha la funzione di riprodurre gli ultimi video scaricati nelle unità oppure gli ultimi a cui sono stati modificati i metadati.
* Playlist filtrate:
i filtri sono per genere, per anno, per attore, per regista ed infine per il mino di 'rating'
