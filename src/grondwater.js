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
  mapTime,
  mapMethodeXY,
  mapMethodeZ,
  mapStatus,
  hasRequiredProperties,
  readCsv,
  mapStartTovMaaiveld,
} from './utils.js';

const xmlObjects = [];
const skippedCounter = {
  grondwaterlocaties: 0,
  grondwatermonsters: 0,
  grondwaterobservaties: 0,
};

export function createGrondwaterXML() {
  // Grondwaterlocaties
  if (fs.existsSync('./data/grondwaterlocaties.csv')) {
    generateGrondwaterLocaties();
  } else {
    console.log('Geen bestand grondwaterlocaties.csv gevonden in de `data` folder. Grondwaterlocaties worden overgeslagen in de XML.');
  }

  // Grondwaterfilters
    if (fs.existsSync('./data/grondwaterfilters.csv')) {
    generateGrondwaterFilters();
  } else {
    console.log('Geen bestand grondwaterfilters.csv gevonden in de `data` folder. Grondwaterfilters worden overgeslagen in de XML.');
  }

  // Grondwatermonsters
  if (fs.existsSync('./data/grondwatermonsters.csv')) {
    generateGrondwaterMonsters();
  } else {
    console.log('Geen bestand grondwatermonsters.csv gevonden in de `data` folder. Grondwatermonsters worden overgeslagen in de XML.');
  }

  // Grondwaterobservaties
  if (fs.existsSync('./data/grondwaterobservaties.csv')) {
    generateGrondwaterObservaties();
  } else {
    console.log('Geen bestand grondwaterobservaties.csv gevonden in de `data` folder. Grondwaterobservaties worden overgeslagen in de XML.');
  }

  // Write XML file

  console.log('Creating grondwater XML...');

  const resultString = xmlObjects.join('\n');
  const gwXmlString = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<ns3:dov-schema xmlns:ns3="http://kern.schemas.dov.vlaanderen.be">\n${resultString}\n</ns3:dov-schema>`;

  fs.writeFile('./dist/grondwater.xml', gwXmlString, { flag: 'w+' }, (err) => {
    if (err) {
      console.error(err);
    }
  });

  console.log('Done! You can find the grondwater XML file in the dist folder.');
}

function generateGrondwaterLocaties() {
  // Read csv file
  console.log('Reading grondwaterlocaties...');

  const gwLocatieData = readCsv('./data/grondwaterlocaties.csv');

  const gwLocatieHeader = mapHeader(gwLocatieData[0]);

  // Remove excess lines at the top
  gwLocatieData.splice(0, 1);

  gwLocatieData.forEach((row, index) => {
    if (
      !hasRequiredProperties(row, index, gwLocatieHeader, [
        'grondwaterlocatie',
        'x (m l72)',
        'y (m l72)',
      ])
    ) {
      skippedCounter.grondwaterlocaties++;
      return;
    }

    const object = {
      grondwaterlocatie: {
        identificatie: findValue(row, gwLocatieHeader, 'grondwaterlocatie'),
        grondwaterlocatieType: 'PUT',
        puntligging: {
          xy: {
            x: mapNumber(findValue(row, gwLocatieHeader, 'x (m l72)')),
            y: mapNumber(findValue(row, gwLocatieHeader, 'y (m l72)')),
            betrouwbaarheid: mapBetrouwbaarheid(findValue(row, gwLocatieHeader, 'betrouwbaarheid XY')),
            methode_opmeten: mapMethodeXY(findValue(row, gwLocatieHeader, 'methode XY')),
            origine_opmeten: {
              naam: findValue(row, gwLocatieHeader, 'origine XY'),
            },
          },
          oorspronkelijk_maaiveld: {
            waarde: mapNumber(findValue(row, gwLocatieHeader, 'Z - maaiveld (mtaw)')),
            betrouwbaarheid: mapBetrouwbaarheid(findValue(row, gwLocatieHeader, 'betrouwbaarheid Z')),
            methode_opmeten: mapMethodeXY(findValue(row, gwLocatieHeader, 'methode Z')),
            origine_opmeten: {
              naam: findValue(row, gwLocatieHeader, 'origine Z'),
            },
          },
          start_tov_maaiveld: {
            gestart_op: mapStartTovMaaiveld(findValue(row, gwLocatieHeader, 'start tov maaiveld (m)')),
            verschil: mapNumber(findValue(row, gwLocatieHeader, 'start tov maaiveld (m)'))
              ? Math.abs(mapNumber(findValue(row, gwLocatieHeader, 'start tov maaiveld (m)')))
              : null,
          },
        },
        diepte: mapNumber(findValue(row, gwLocatieHeader, 'diepte (m)')) ? Math.abs(mapNumber(findValue(row, gwLocatieHeader, 'diepte (m)'))) : null,
        datum_ingebruikname: mapDate(findValue(row, gwLocatieHeader, 'datum ingebruikname')),
        putsoort: findValue(row, gwLocatieHeader, 'putsoort') ?? 'onbekend',
        beheer: {
          beheerder: {
            naam: findValue(row, gwLocatieHeader, 'beheerder'),
          },
        },
        status: mapStatus(findValue(row, gwLocatieHeader, 'status')),
      },
    };

    const json = JSON.stringify(removeEmptyProperties(object));
    const xml = json2xml(json, { compact: true, spaces: 4 });

    xmlObjects.push(xml);
  });

  if (skippedCounter.grondwaterlocaties) {
    console.log('\x1b[33m%s\x1b[0m', 'Opgelet: rijen met fouten werden overgeslagen.');
    console.log('\x1b[33m%s\x1b[0m', 'Grondwaterlocaties: ' + skippedCounter.grondwaterlocaties + ' rijen met fouten');
    if (!verbose) {
      console.log('\x1b[33m%s\x1b[0m', 'Run het script opnieuw met de `-v` parameter om meer informatie te verkrijgen per ongeldige rij.');
    }
  } else {
    console.log('Grondwaterlocaties foutloos verwerkt!');
  }
}

function generateGrondwaterFilters() {
  // Read csv file
  console.log('Reading grondwaterfilters...');

  const gwFilterData = readCsv('./data/grondwaterfilters.csv');

  const gwFilterHeader = mapHeader(gwFilterData[0]);

  // Remove excess lines at the top
  gwFilterData.splice(0, 1);

  gwFilterData.forEach((row, index) => {
    if (
      !hasRequiredProperties(row, index, gwFilterHeader, [
        'grondwaterlocatie',
        'filter identificatie',
        'filtertype',
      ])
    ) {
      skippedCounter.grondwaterfilters++;
      return;
    }

    const object = {
      filter: {
        identificatie: findValue(row, gwFilterHeader, 'filter identificatie'),
        filtertype: findValue(row, gwFilterHeader, 'filtertype'),
        grondwaterlocatie: findValue(row, gwFilterHeader, 'grondwaterlocatie'),
        meetnet: mapNumber(findValue(row, gwFilterHeader, 'meetnet')),
        datum_ingebruikname: mapDate(findValue(row, gwFilterHeader, 'datum ingebruikname')),
        ligging: {
          aquifer: findValue(row, gwFilterHeader, 'aquifer'),
          regime: findValue(row, gwFilterHeader, 'regime'),
        },
        status: mapStatus(findValue(row, gwFilterHeader, 'status')),
      },
    };

    const json = JSON.stringify(removeEmptyProperties(object));
    const xml = json2xml(json, { compact: true, spaces: 4 });

    xmlObjects.push(xml);
  });

  if (skippedCounter.grondwaterfilters) {
    console.log('\x1b[33m%s\x1b[0m', 'Opgelet: rijen met fouten werden overgeslagen.');
    console.log('\x1b[33m%s\x1b[0m', 'Grondwaterfilters: ' + skippedCounter.grondwaterfilters + ' rijen met fouten');
    if (!verbose) {
      console.log('\x1b[33m%s\x1b[0m', 'Run het script opnieuw met de `-v` parameter om meer informatie te verkrijgen per ongeldige rij.');
    }
  } else {
    console.log('Grondwaterfilters foutloos verwerkt!');
  }
}

function generateGrondwaterMonsters() {
  // Read csv file
  console.log('Reading grondwatermonsters...');

  const gwMonsterData = readCsv('./data/grondwatermonsters.csv');

  const gwMonsterHeader = mapHeader(gwMonsterData[0]);

  // Remove excess lines at the top
  gwMonsterData.splice(0, 1);

  gwMonsterData.forEach((row, index) => {
    if (!hasRequiredProperties(row, index, gwMonsterHeader, ['grondwaterlocatie', 'filter', 'identificatie watermonster', 'datum monstername'])) {
      skippedCounter.grondwatermonsters++;
      return;
    }

    const object = {
      filtermeting: {
        grondwaterlocatie: findValue(row, gwMonsterHeader, 'grondwaterlocatie'),
        filter: {
          identificatie: findValue(row, gwMonsterHeader, 'filter'),
          filtertype: findValue(row, gwMonsterHeader, 'filtertype'),
        },
        watermonster: {
          identificatie: findValue(row, gwMonsterHeader, 'identificatie watermonster'),
          monstername: {
            datum: mapDate(findValue(row, gwMonsterHeader, 'datum monstername')),
            tijd: mapTime(findValue(row, gwMonsterHeader, 'tijdstip monstername')),
            labo: {
              naam: findValue(row, gwMonsterHeader, 'naam labo monstername'),
            },
          },
          laboanalyse: {
            datum: mapDate(findValue(row, gwMonsterHeader, 'datum laboanalyse')),
            labo: {
              naam: findValue(row, gwMonsterHeader, 'naam labo laboanalyse'),
            },
          },
        },
      },
    };

    const json = JSON.stringify(removeEmptyProperties(object));
    const xml = json2xml(json, { compact: true, spaces: 4 });

    xmlObjects.push(xml);
  });

  if (skippedCounter.grondwatermonsters) {
    console.log('\x1b[33m%s\x1b[0m', 'Opgelet: rijen met fouten werden overgeslagen.');
    console.log('\x1b[33m%s\x1b[0m', 'Grondwatermonsters: ' + skippedCounter.grondwatermonsters + ' rijen met fouten');
    if (!verbose) {
      console.log('\x1b[33m%s\x1b[0m', 'Run het script opnieuw met de `-v` parameter om meer informatie te verkrijgen per ongeldige rij.');
    }
  } else {
    console.log('Grondwatermonsters foutloos verwerkt!');
  }
}

function generateGrondwaterObservaties() {
  // Read csv file
  console.log('Reading grondwaterobservaties...');
  const gwObservatieData = readCsv('./data/grondwaterobservaties.csv');

  const gwObservatieHeader = mapHeader(gwObservatieData[0]);

  // Remove excess lines at the top
  gwObservatieData.splice(0, 1);

  gwObservatieData.forEach((row, index) => {
    if (!hasRequiredProperties(row, index, gwObservatieHeader, ['grondwaterlocatie', 'filter', 'identificatie watermonster'])) {
      skippedCounter.grondwaterobservaties++;
      return;
    }

    const object = {
      filtermeting: {
        grondwaterlocatie: findValue(row, gwObservatieHeader, 'grondwaterlocatie'),
        filter: {
          identificatie: findValue(row, gwObservatieHeader, 'filter'),
          filtertype: findValue(row, gwObservatieHeader, 'filtertype'),
        },
        watermonster: {
          identificatie: findValue(row, gwObservatieHeader, 'identificatie watermonster'),
          observatie: {
            parameter: findValue(row, gwObservatieHeader, 'parameter'),
            waarde_numeriek: mapNumber(findValue(row, gwObservatieHeader, 'waarde_numeriek')),
            eenheid: findValue(row, gwObservatieHeader, 'eenheid'),
            detectieconditie: mapDetectieDonditie(findValue(row, gwObservatieHeader, 'detectieconditie')),
            betrouwbaarheid: mapBetrouwbaarheid(findValue(row, gwObservatieHeader, 'betrouwbaarheid')),
            veld_labo: ['VELD', 'LABO'].includes(findValue(row, gwObservatieHeader, 'veld/labo')?.toUpperCase())
              ? findValue(row, gwObservatieHeader, 'veld/labo').toUpperCase()
              : 'VELD',
          },
        },
      },
    };

    const json = JSON.stringify(removeEmptyProperties(object));
    const xml = json2xml(json, { compact: true, spaces: 4 });

    xmlObjects.push(xml);
  });

  if (skippedCounter.grondwaterobservaties) {
    console.log('\x1b[33m%s\x1b[0m', 'Opgelet: rijen met fouten werden overgeslagen.');
    console.log('\x1b[33m%s\x1b[0m', 'Grondwaterobservaties: ' + skippedCounter.grondwaterobservaties + ' rijen met fouten');
    if (!verbose) {
      console.log('\x1b[33m%s\x1b[0m', 'Run het script opnieuw met de `-v` parameter om meer informatie te verkrijgen per ongeldige rij.');
    }
  } else {
    console.log('Grondwaterobservaties foutloos verwerkt!');
  }
}
