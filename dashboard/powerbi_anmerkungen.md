# Dashboard Anmerkungen:

## Wichtig für die Extraktion

* Es gibt Mitglieder, die ihre Partei gewechselt haben => die Wahlperiode muss mit extrahiert werden, um eine korrekte Parteizuteilung zu ermöglichen
* Manche Mitglieder sind mit unterschiedlichen Ortszusätzen mehrfach vertreten (sowohl unterschiedliche Personen als auch ein und die selbe) => der Ortszusatz muss mit extrahiert werden, um die richtige ID mit allen dazugehörigen Daten zuzuteilen


## Ausgeführte Schritte
### Stammdaten-Datensatz
* Für relevant erachtete Spalten:
	- ID
	- Nachname
	- Vorname
	- Ortszusatz
	- Geschlecht
	- Partei_kurz
	- Wahlperiode
	
* Wahlperiode 20 wurde herausgefiltert
* Parteivereinheitlichung (CDU und CSU => CDU/CSU | GRÜNE + DIE GRÜNEN/BÜNDNIS 90 => BÜNDNIS 90/DIE GRÜNEN) | PDS + PDS/LL => DIE LINKE.
* Dimensionstabellen für Wahlperiode, Geschlecht und Partei, bei m:n Verbindungen im Datenmodell würden sonst Filterungen und Abhängigkeiten zerspringen

### output.csv (Testdaten)
* Extraktion von Ortszusatz und Partei aus der Spalte "Name"
* Extraktion der Protokoll-Nummer aus der Spalte "Nr" (10/1 => 1)
* Anpassung der Datentypen
* Parteivereinheitlichung (CDU und CSU => CDU/CSU | GRÜNE + DIE GRÜNEN/BÜNDNIS 90 => BÜNDNIS 90/DIE GRÜNEN)
* Zusammenführung der Testdaten mit den Stammdaten (left join on 1.Nachname, 2.Wahlperiode, 3.Partei_kurz, 4.Ortszusatz) 
* Personen, die nicht in dem Stammdatensatz aufgeführt wurden, wurden herausgefiltert
	
## Offene Fragen	
* Es sind 30 verschiedene Parteien aufgelistet, auch welche die so gar nicht mehr existieren => Wollen wir alle betrachten oder nur die "Größten"? 
* Es gibt Parteien, die gar keine Frauen beinhalten, wie gehen wir mit denen um?
* Farbpalette (Ist rosa für Frauen und blau für Männer zu stereotypical oder würde das als visual aid helfen?) => rot und blau
* Es gibt Daten zu dem Wahlkreis bzw. auf welcher Landesliste die Mitglieder standen. Sind das Informationen, die wir ebenfalls betrachten wollen?
