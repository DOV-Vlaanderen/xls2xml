# xls2xml: Van Excel data naar DOV XML-formaat

Het doel van xls2xml is om data eerst klaar te zetten in Excel, waarbij u gebruik kunt maken van alle handige tools die Excel aanbiedt. Dit gebeurt aan de hand van templates die wij reeds hebben gegenereerd.
Vervolgens kunt u deze Excel-data makkelijk omzetten naar het DOV XML-formaat, waarna u deze data kunt aanleveren aan DOV.
Het proces bestaat dus zoals eerder gezegd uit twee stappen:
* Stap 1: Voorbereiden van de data
* Stap 2: Converteren naar XML

## Stap 1: Data voorbereiden

Het script vergt aangeleverde data in het juiste formaat. In de map templates vind je de Excel-templates kun je de templates vinden, eerst gecategoriseerd naar de gewenste omgeving, en vervolgens volgens thema.


Vul het Excel-bestand in met de data die je in DOV wenst toe te voegen. 
In het excel bestand zijn enkele gegevensvalidaties aanwezig. Zo zijn enkel datums later dan 01/01/1900 toegelaten in velden waar een datum wordt verwacht.
Ook zijn er enkele velden waar de optie uit een codelijst moet komen. Deze zijn makkelijk zichtbaar aan de verwijzing in de kolomnamen, die rechtstreeks verwijzen naar de relevante codelijst op het Excel-blad "Codelijsten".

Wanneer over een bepaald object meerdere rijen aan gegevens moeten ingevuld worden, dan kan dit door de gegevens in de verplichte velden te dupliceren naar de onderstaande rijen en vervolgens de gegevens in de corresponderende kolom toe te voegen.
Een voorbeeld van dit proces wordt weergegeven in onderstaande afbeelding:
![data_voorbeeld](docs/data_voorbeeld.png)



## Stap 2: Converteren naar XML

### Uitvoeren via `xls2xml.exe`

In de map app kunt u het bestand `xls2xml.exe` vinden.
Door deze executable uit te voeren, kun je makkelijk en zonder verdere technische kennis de conversie uit voeren.
![app](docs/app.png)

De parameters die nog geconfigureerd moeten worden zijn:

* Input file: Het excel-bestand dat u wenst te converteren.
* Output file: De filename/opslaglocatie van de XML die gegenereerd zal worden.
* Environment (omgeving): De omgeving naar waar u het XML-bestand wil uploaden
* Sheets: Welke sheets van het Excel geconverteerd moeten worden. U kan hier gewoon voor de optie automatisch gaan, tenzij u om de een of andere reden toch enkele specifieke sheets wil converteren.

U kan nu de conversie starten.

### Alternatieve methode:

Deze methode is eerder bedoeld voor mensen die deze methode verder willen aanpassen/automatiseren

#### Download en installeer Python

Het script is geschreven in python. Om dit op jouw computer te kunnen uitvoeren, moet je Python geïnstalleerd hebben staan. Geen zorgen, dit is een simpele procedure, en je zal er verder niks van merken.

Als je nog geen Python hebt geïnstalleerd op je systeem, volg dan deze stappen:

1.  Ga naar de officiële Python-website op [python.org](python.org).
2.  Klik op de "Downloads" knop in het menu.
3. Kies de versie van Python die overeenkomt met je besturingssysteem (meestal wordt de nieuwste stabiele versie aanbevolen).
4. Download het installatiebestand en voer het uit.
5. Volg de installatie-instructies op het scherm.

Alternatief kan je als je Windows 10 gebruikt, Python eenvoudig installeren via de Microsoft Store:

1. Open de Microsoft Store-app op je Windows 10-computer.
2. Zoek naar "Python" in de zoekbalk van de Microsoft Store.
3. Klik op de recentste versie van Python die wordt weergegeven in de zoekresultaten.
4. Klik op de knop "Installeren" om de installatie te starten.
5. Volg de instructies op het scherm om de installatie te voltooien.

#### Download het script

Klik op de [github pagina](https://github.com/DOV-Vlaanderen/xls2xml) rechtsboven op download en download de bestanden in een zip formaat. Pak vervolgens het zip bestand uit op je computer.
Ben je meer gevorderd met git en github, dan kan je ook altijd de repo forken.

Heb je het script reeds aangeleverd gekregen als zip bestand? Kijk dan zeker op de githubpagina naar de datum van de laatste update. Indien het script recent geupdated is geweest, download je best de nieuwste versie van het script.  
<br>



#### Het script uitvoeren

Het script kan uitgevoerd worden met een commando in de terminal. Dit kan op verschillende manieren:
<br>

#### Een terminal openen voor Windows gebruikers

Open je Windows verkenner. Houdt de `SHIFT` toets ingedrukt en rechtermuisklik op de map met het main script. Er verschijnt een menu, en kies voor de optie 'Open PowerShell venster'.

#### Een terminal openen voor MacOS gebruikers

Open Finder. Rechtermuisklik op de map met het main script. Er verschijnt een menu, en kies voor de optie 'Nieuwe terminal op Map'.  
<br>

#### Packages installeren

Om het script uit te kunnen voeren moeten er nog een aantal extensies geïnstalleerd worden. Dit kan je eenvoudigweg doen door in de terminal die hebt openstaan de volgende commando's uit te voeren (typ het commando en druk op Enter):
```
python.exe -m pip install --upgrade pip
pip install -r requirements.txt
```
<br>

#### Het script uitvoeren

Nu je een terminal hebt open staan, kan je een van volgende commando's uitvoeren (typ het commando en druk op Enter):

```
python xls2xml.py 
```

of 

```
py xls2xml.py 
```




<br>
Wanneer het script klaar is, worden de xml bestanden toegevoegd aan de map 'results'. Indien er zich errors voordoen, krijg je die te zien.

#### Geavanceerd gebruik

Het is mogelijk om enkele opties aan deze functie toe te voegen:

```
usage: xls2xml [-h] [-i INPUT_FILE] [-o OUTPUT_FILE] [-m MODE] [-omg OMGEVING] [-s SHEETS [SHEETS ...]]

Function to parse data from xlsx-files to XML ready to be uploaded in DOV

options:
  -h, --help            show this help message and exit
  -i INPUT_FILE, --input_file INPUT_FILE
                        Input xlsx file that will be parsed to XML, default: data/template.xlsx
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        Output file to which the parsed XML-file is outputted, default: dist/dev.xml
  -m MODE, --mode MODE  Run in local or online mode, options are 'local' and 'online', default: local
  -omg OMGEVING, --omgeving OMGEVING
                        Determines which xsd-schema is used, options are 'ontwikkel','oefen' and 'productie', default:
                        productie
  -s SHEETS [SHEETS ...], --sheets SHEETS [SHEETS ...]
                        Sheet(s) from excel file that needs to be parsed, by default all sheets will be parsed
```