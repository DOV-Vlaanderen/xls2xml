import * as fs from 'fs';
import { json2xml } from 'xml-js';

import {
  verbose,
  mapDetectieDonditie,
  mapNumber,
  removeEmptyProperties,
  mapHeader,
  findValue,
  mapBetrouwbaarheid,
  mapDate,
  mapMethodeXY,
  mapMethodeZ,
  mapStatus,
  hasRequiredProperties,
  readCsv,
} from './utils.js';

const xmlObjects = [];
const skippedCounter = {
  bodemlocaties: 0,
  bodemmonsters: 0,
  bodemobservaties: 0,
};

export function createBodemXML() {
  // Bodemlocaties
  if (fs.existsSync('./data/bodemlocaties.csv')) {
    generateBodemLocaties();
  } else {
    console.log('Geen bestand bodemlocaties.csv gevonden in de `data` folder. Bodemlocaties worden overgeslagen in de XML.');
  }

  // Bodemmonsters
  if (fs.existsSync('./data/bodemmonsters.csv')) {
    generateBodemMonsters();
  } else {
    console.log('Geen bestand bodemmonsters.csv gevonden in de `data` folder. Bodemmonsters worden overgeslagen in de XML.');
  }

  // Bodemobservaties
  if (fs.existsSync('./data/bodemobservaties.csv')) {
    generateBodemObservaties();
  } else {
    console.log('Geen bestand bodemobservaties.csv gevonden in de `data` folder. Bodemobservaties worden overgeslagen in de XML.');
  }

  // Write XML file
  if (xmlObjects.length) {
    console.log('\nGenereren bodem XML...');

    const resultString = xmlObjects.join('\n');
    const bodemXmlString = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<ns3:dov-schema xmlns:ns3="http://kern.schemas.dov.vlaanderen.be">\n${resultString}\n</ns3:dov-schema>`;

    fs.writeFile('./dist/bodem.xml', bodemXmlString, { flag: 'w+' }, (err) => {
      if (err) {
        console.error(err);
      }
    });

    console.log('\x1b[32m%s\x1b[0m', 'Klaar! Je kan de bodem.xml terugvinden in de `dist` folder.');
  } else {
    console.log('\x1b[33m%s\x1b[0m', 'Geen te verwerken bodemobjecten gevonden.');
  }
}

function generateBodemLocaties() {
  // Read csv file
  console.log('Inlezen bodemlocaties...');

  const bodemLocatieData = readCsv('./data/bodemlocaties.csv');

  const bodemLocatieHeader = mapHeader(bodemLocatieData[0]);

  // Remove excess lines at the top
  bodemLocatieData.splice(0, 1);

  // Loop through data rows and create bodemlocatie object
  bodemLocatieData.forEach((row, index) => {
    if (
      !hasRequiredProperties(row, index, bodemLocatieHeader, [
        'bodemlocatie',
        'type',
        'x (m l72)',
        'y (m l72)',
        'origine xy',
        'z - maaiveld (mtaw)',
        'origine z',
      ])
    ) {
      skippedCounter.bodemlocaties++;
      return;
    }

    const object = {
      bodemlocatie: {
        naam: findValue(row, bodemLocatieHeader, 'bodemlocatie'),
        type: findValue(row, bodemLocatieHeader, 'type'),
        waarnemingsdatum: mapDate(findValue(row, bodemLocatieHeader, 'waarnemingsdatum')),
        doel: findValue(row, bodemLocatieHeader, 'doel'),
        ligging: {
          beginpunt: {
            xy: {
              x: mapNumber(findValue(row, bodemLocatieHeader, 'x (m L72)')),
              y: mapNumber(findValue(row, bodemLocatieHeader, 'y (m L72)')),
              betrouwbaarheid: mapBetrouwbaarheid(findValue(row, bodemLocatieHeader, 'betrouwbaarheid XY')),
              methode_opmeten: mapMethodeXY(findValue(row, bodemLocatieHeader, 'methode XY')),
              origine_opmeten: {
                naam: findValue(row, bodemLocatieHeader, 'origine XY'),
              },
            },
            maaiveld: {
              waarde: mapNumber(findValue(row, bodemLocatieHeader, 'z - maaiveld (mtaw)')),
              betrouwbaarheid: mapBetrouwbaarheid(findValue(row, bodemLocatieHeader, 'betrouwbaarheid Z')),
              methode_opmeten: mapMethodeZ(findValue(row, bodemLocatieHeader, 'methode Z')),
              origine_opmeten: {
                naam: findValue(row, bodemLocatieHeader, 'origine Z'),
              },
            },
          },
        },
        status: mapStatus(findValue(row, bodemLocatieHeader, 'status')),
        dataleverancier: {
          bedrijf: {
            naam: findValue(row, bodemLocatieHeader, 'dataleverancier'),
          },
        },
      },
    };

    const json = JSON.stringify(removeEmptyProperties(object));
    const xml = json2xml(json, { compact: true, spaces: 4 });

    xmlObjects.push(xml);
  });

  if (skippedCounter.bodemlocaties) {
    console.log('\x1b[33m%s\x1b[0m', 'Opgelet: rijen met fouten werden overgeslagen.');
    console.log('\x1b[33m%s\x1b[0m', 'Bodemlocaties: ' + skippedCounter.bodemlocaties + ' rijen met fouten');
    if (!verbose) {
      console.log('\x1b[33m%s\x1b[0m', 'Run het script opnieuw met de `-v` parameter om meer informatie te verkrijgen per ongeldige rij.');
    }
  } else {
    console.log('Bodemlocaties foutloos verwerkt!');
  }
}

function generateBodemMonsters() {
  // Read csv file
  console.log('\nInlezen bodemmonsters...');

  const bodemMonsterData = readCsv('./data/bodemmonsters.csv');

  const bodemMonsterHeader = mapHeader(bodemMonsterData[0]);

  // Remove excess lines at the top
  bodemMonsterData.splice(0, 1);

  bodemMonsterData.forEach((row, index) => {
    if (!hasRequiredProperties(row, index, bodemMonsterHeader, ['identificatie bodemmonster', 'datum monstername', 'type'])) {
      skippedCounter.bodemmonsters++;
      return;
    }

    const object = {
      bodemmonster: {
        identificatie: findValue(row, bodemMonsterHeader, 'identificatie bodemmonster'),
        datum_monstername: mapDate(findValue(row, bodemMonsterHeader, 'datum monstername')),
        type: findValue(row, bodemMonsterHeader, 'type'),
        monsternamedoor: {
          naam: findValue(row, bodemMonsterHeader, 'naam labo monstername'),
        },
        status: mapStatus(findValue(row, bodemMonsterHeader, 'status')),
        van: mapNumber(findValue(row, bodemMonsterHeader, 'van (cm)')),
        tot: mapNumber(findValue(row, bodemMonsterHeader, 'tot (cm)')),
        labo: {
          datum: mapDate(findValue(row, bodemMonsterHeader, 'datum laboanalyse')),
          labo: {
            naam: findValue(row, bodemMonsterHeader, 'naam labo laboanalyse'),
          },
        },
        laboreferentie: findValue(row, bodemMonsterHeader, 'laboreferentie'),
        ref_bodemlocatie: {
          naam: findValue(row, bodemMonsterHeader, 'bodemlocatie'),
        },
      },
    };

    const json = JSON.stringify(removeEmptyProperties(object));
    const xml = json2xml(json, { compact: true, spaces: 4 });

    xmlObjects.push(xml);
  });

  if (skippedCounter.bodemmonsters) {
    console.log('\x1b[33m%s\x1b[0m', 'Opgelet: rijen met fouten werden overgeslagen.');
    console.log('\x1b[33m%s\x1b[0m', 'Bodemmonsters: ' + skippedCounter.bodemmonsters + ' rijen met fouten');
    if (!verbose) {
      console.log('\x1b[33m%s\x1b[0m', 'Run het script opnieuw met de `-v` parameter om meer informatie te verkrijgen per ongeldige rij.');
    }
  } else {
    console.log('Bodemmonsters foutloos verwerkt!');
  }
}

function generateBodemObservaties() {
  // Read csv file
  console.log('\nInlezen bodemobservaties...');

  const bodemObservatieData = readCsv('./data/bodemobservaties.csv');

  const bodemObservatieHeader = mapHeader(bodemObservatieData[0]);

  // Remove excess lines at the top
  bodemObservatieData.splice(0, 1);

  bodemObservatieData.forEach((row, index) => {
    if (
      !hasRequiredProperties(row, index, bodemObservatieHeader, [
        'parameter',
        'waarde_numeriek',
        'eenheid',
        'observatiedatum',
        'identificatie bodemmonster',
        'identificatie bodemlocatie',
      ])
    ) {
      skippedCounter.bodemobservaties++;
      return;
    }

    // const bodemMonster = bodemMonsterData.find(
    //   (x) => findValue(x, bodemMonsterHeader, 'identificatie bodemmonster') === findValue(row, bodemObservatieHeader, 'identificatie bodemmonster')
    // );

    // if (!bodemMonster) {
    //   if (verbose) {
    //     console.log(
    //       '\x1b[33m%s\x1b[0m',
    //       'Geen link met bodemmonsters.csv gevonden voor identificatie bodemmonster: ' +
    //         findValue(row, bodemObservatieHeader, 'identificatie bodemmonster')
    //     );
    //   }
    //   skippedCounter.bodemobservaties++;
    //   return;
    // }

    const object = {
      bodemobservatie: {
        parameter: findValue(row, bodemObservatieHeader, 'parameter'),
        parametergroep: 'bodem_chemisch_PFAS',
        waarde_numeriek: mapNumber(findValue(row, bodemObservatieHeader, 'waarde_numeriek')),
        eenheid: findValue(row, bodemObservatieHeader, 'eenheid'),
        detectieconditie: mapDetectieDonditie(findValue(row, bodemObservatieHeader, 'detectieconditie')),
        betrouwbaarheid: mapBetrouwbaarheid(findValue(row, bodemObservatieHeader, 'betrouwbaarheid')),
        veld_labo: ['VELD', 'LABO'].includes(findValue(row, bodemObservatieHeader, 'veld/labo')?.toUpperCase())
          ? findValue(row, bodemObservatieHeader, 'veld/labo').toUpperCase()
          : 'VELD',
        observatiedatum: mapDate(findValue(row, bodemObservatieHeader, 'observatiedatum')),
        status: mapStatus(findValue(row, bodemObservatieHeader, 'status')),
        ref_bodemmonster: {
          ref_bodemlocatie: {
            naam: findValue(row, bodemObservatieHeader, 'identificatie bodemlocatie'),
          },
          identificatie: findValue(row, bodemObservatieHeader, 'identificatie bodemmonster'),
        },
      },
    };

    const json = JSON.stringify(removeEmptyProperties(object));
    const xml = json2xml(json, { compact: true, spaces: 4 });

    xmlObjects.push(xml);
  });

  if (skippedCounter.bodemobservaties) {
    console.log('\x1b[33m%s\x1b[0m', 'Opgelet: rijen met fouten werden overgeslagen.');
    console.log('\x1b[33m%s\x1b[0m', 'Bodemobservaties: ' + skippedCounter.bodemobservaties + ' rijen met fouten');
    if (!verbose) {
      console.log('\x1b[33m%s\x1b[0m', 'Run het script opnieuw met de `-v` parameter om meer informatie te verkrijgen per ongeldige rij.');
    }
  } else {
    console.log('Bodemobservaties foutloos verwerkt!');
  }
}
