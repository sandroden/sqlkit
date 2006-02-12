** Specifiche modulo edit-sql

  Il modulo deve offrire alcune classi/funzioni che permettano un edit
  immediato e facile di una tabella ed in generale dell'output di una query
  sql

  * in formato tabellare (una riga,  una tupla)
  * in formato maschera (una tupla in una maschera)

  Un esempio di funzionamento è la libreria sdsql in tcl.

  Il risultato della query è la creazione di una opportuna finestra dove
  vengano rapresentati i dati. Per la forma tabellare si usa TreeView per la
  forma a maschera si usa una finestra generata al volo con opportune classi
  dal pacchetto parallelo 'layout?'

  Il pacchetto deve prevedere alcuni controlli per verificare

  1. se nella query ci sono tutte le chiavi primarie e quindi se è possibile
     aggiornare o se la tabella è aperta in read-only

  2. se sono soddisfatte le condizioni di validazione riga e cella che deve
     essere possibile dichiarare in modo semplice (ad esempio come funzioni
     o metodi aggiuntivi)

  3. le entry dell'interfaccia maschera e possibilmente TreeView dovranno
     avere collegati i controlli che verificano che i tipi siano corretti

  4. dovrà essere possibile dichiarare alcune colonne come non editabili e
     dovrà essere possibile dichiarare alcune condizioni come "obbligatorie"
     ovvero aggiunte a qualunque query sql. Un esempio è per evitare che una
     persona veda dati che non le devono essere visibili all'interno di una
     tabella di cui ha diritto a vederne altri.

  5. deve potere rappresentare anche delle join

  6. l'interfaccia grafica deve permettere di fare richerche, e quidni di
     visualizzare il risultato dell stesse. Le ricerche devono poter
     avvenire sullo stesso campo nel caso di ricerche singole o se su più
     campi tramite popup.

  7. Deve essere possibile interrogare in maniera efficace l'interfaccia (il
     db) per sapere quali sono i valori ammessi per un certo campo o come
     'select distinct' sui valori nel db o come risultato di un opportuno
     metodo/funzione.

  8. Per l'edit a Maschera deve essere possibile passare una descrizione del
     layout fra i parametri di costruzione

