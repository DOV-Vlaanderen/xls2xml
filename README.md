# Script voor conversie van Excel data naar DOV XML-formaat

## Stap 1: Download en installeer Node.js

Het script is geschreven in javascript en gebruikt Node.js als runtime. Om dit op jouw computer te kunnen uitvoeren, moet je Node.js geïnstalleerd hebben staan. Geen zorgen, dit is een simpele procedure, en je zal er verder niks van merken.

Ga naar de downloadpagina van Node.js: https://nodejs.org/en/download/

Download de LTS versie voor jouw besturingsstysteem. Kies voor de .msi versie (voor Windows gebruikers) of de .pkg versie (voor MacOS gebruikers). Installeer vervolgens Node op je computer door de stappen van de installer te volgen. Je mag bij alle mogelijke tussenstappen op het standaard antwoord laten staan en op Volgende klikken. 

Let wel op: mogelijks heb je voor de installatie wel de hulp of rechten nodig van je systeembeheerder.  
<br>

## Stap 2: Download het script

Klik op de github pagina rechtsboven op download en download de bestanden in een zip formaat. Pak vervolgens het zip bestand uit op je computer.
Ben je meer gevorderd met git en github, dan kan je ook altijd de repo forken.

Heb je het script reeds aangeleverd gekregen als zip bestand? Kijk dan zeker op de githubpagina naar de datum van de laatste update. Indien het script recent geupdated is geweest, download je best de nieuwste versie van het script.  
<br>

## Stap 3: Data voorbereiden

Het script vergt aangeleverde data in het juiste csv-formaat. In de map van het script zit een map 'data'. Hierin vind je de excel template die gebruikt wordt voor elk object.

Vul het excel bestand in met de data die je in DOV wenst to te voegen. Als je klaar bent sla je elk blad van de excel die je wenst toe te voegen op als csv. De naam van dit csv bestand moet de naam van het excel blad zijn (bv. grondwaterlocaties.csv, bodemlocaties.csv, bodemobservaties.csv, ...). Sla de csv bestanden op in de map 'data'.  LET OP: gebruik steeds een ; (puntkomma) als scheidingsteken, en geen , (komma). 
<br> 

## Stap 4: Het script uitvoeren

Het script kan uitgevoerd worden met een commando in de terminal. Dit kan op verschillende manieren:
<br>

### Stap 4.1a: Een terminal openen voor Windows gebruikers

Open je Windows verkenner. Houdt de `SHIFT` toets ingedrukt en rechtermuisklik op de map met het script. Er verschijnt een menu, en kies voor de optie 'Open PowerShell venster'.

### Stap 4.1b: Een terminal openen voor MacOS gebruikers

Open Finder. Rechtermuisklik op de map met het script. Er verschijnt een menu, en kies voor de optie 'Nieuwe terminal op Map'.  
<br>

### Stap 4.2: Packages installeren

Om het script uit te kunnen voeren moeten er nog een aantal extensies geïnstallerd worden. Dit kan je eenvoudigweg doen door in de terminal die hebt openstaan het volgende commando uit te voeren (typ het commando en druk op Enter):
```
npm install
```
<br>

### Stap 4.3: Het script uitvoeren

Nu je een terminal hebt open staan, kan je een van volgende commando's uitvoeren (typ het commando en druk op Enter):

```
node main -bodem
```

voor bodemdata of

```
node main -grondwater
```

voor grondwaterdata.

<br>
Wanneer het script gedaan is, worden de xml bestanden toegevoegd aan de map 'dist'. Indien er zich errors voordoen, krijg je die te zien.

Wanneer er rijen ongeldig waren werden die overgeslagen in het script. Om meer informatie te krijgen waarom de rijen ongeldig waren, voeg `-v` toe aan je commando en voer het script op nieuw uit.
