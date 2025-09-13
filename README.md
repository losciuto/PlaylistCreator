[![License](https://img.shields.io/badge/License-GPLv3-green.svg)](https://github.com/losciuto/vlcremote/blob/master/LICENSE)
# Playlist Creator

Raccoglie, con il Tab 'Scansione', i video presenti nelle unità disco o chiavette USB (non consigliato), ne memorizza le informazioni, prendendo dai file <nome del video>.nfo style Kodi, se presenti, i metadati in un file SQLite. Una volta memorizzati i dati, è possibile creare delle playlist secondo diversi criteri, nel Tab 'Genera Playlist'. 

## Playlist casuali
sceglie, dopo averne stabilito il numero, una serie di video scelti secondo il criterio RANDOM() di SQLite.
## Playlist manuale:
si scelgono i video voluti manualmente.
## Playlist degli ultimi video scaricati:
ha la funzione di riprodurre gli ultimi video scaricati nelle unità oppure gli ultimi a cui sono stati modificati i metadati.
## Playlist filtrate:
i filtri sono per genere, per anno, per attore, per regista ed infine per il minimo di 'rating'. Ogni filtro, tranne il rating, è multi-selezione.

> Dopo aver generato una playlist e scelto il numero di video da riprodurre, vengono visualizzati i poster e cliccando sui poster ne fa vedere la locandina. Tutto questo se sono presenti i file .nfo. Chiudendo la finestra dei poster, inizia automaticamente la riproduzione che è prevista solo con VLC, al momento. Per cui è necessartio che VLC sia già installato prima dell'esecuzione.
>
> C'e' la possibilità di gestire il database, con il Tab 'Gestione DB', tranne l'inserimento manuale e la modifica.
>
> Mettento il check sulla voce 'Attiva controllo remoto', è possibile utilizzare il controllo remoto in rete: [vclremote] (https://github.com/losciuto/vlcremote).
