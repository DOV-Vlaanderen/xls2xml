import * as fs from 'fs';
import { json2xml } from 'xml-js';

import {
  verbose,
  mapNumber,
  removeEmptyProperties,
  mapHeader,
  findValue,
  mapDate,
  mapTime,
  hasRequiredProperties,
  readCsv,
} from './utils.js';

const xmlObjects = [];
const skippedCounter = {
  opdracht: 0,
};

export function createOpdrachtXML() {
  // Opdracht
  if (fs.existsSync('./data/opdracht.txt')) {
    generateOpdracht();
  } else {
    console.log('Geen bestand opdracht.txt gevonden in de `data` folder. Opdrachten worden overgeslagen in de XML.');
  }


  // Write XML file

  console.log('Creating opdracht XML...');

  const resultString = xmlObjects.join('\n');
  const gwXmlString = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<ns3:dov-schema xmlns:ns3="http://kern.schemas.dov.vlaanderen.be">\n${resultString}\n</ns3:dov-schema>`;

  fs.writeFile('./dist/opdracht.xml', gwXmlString, { flag: 'w+' }, (err) => {
    if (err) {
      console.error(err);
    }
  });

  console.log('Done! You can find the opdracht XML file in the dist folder.');
}

function generateOpdracht() {
  // Read csv file
  console.log('Reading opdracht...');

  const OpdrachtData = readCsv('./data/opdracht.txt');

  const OpdrachtHeader = mapHeader(OpdrachtData[0]);

  // Remove excess lines at the top
  OpdrachtData.splice(0, 6);

  OpdrachtData.forEach((row, index) => {

    if (
      !hasRequiredProperties(row, index, OpdrachtHeader, [
        'naam',
        'opdrachtgever-choice_1-naam',
        'opdrachtnemer-choice_1-naam',
        'dataleverancier-choice_1-naam',
        'locatie-coordinatenstelsel',
        'locatie-wkt'])
    ) {
      skippedCounter.opdracht++;
      return;
    }

    const object = {
      opdracht: {
        naam: findValue(row, OpdrachtHeader, 'naam'),
        omschrijving: null,
        opdrachtgever: {
            naam: findValue(row, OpdrachtHeader, 'opdrachtgever-choice_1-naam')
        },
        opdrachtnemer: {
            naam: findValue(row, OpdrachtHeader, 'opdrachtnemer-choice_1-naam')
        },
        dataleverancier: {
            naam: findValue(row, OpdrachtHeader, 'dataleverancier-choice_1-naam')
        },
        einddatum: null,
        locatie: {
            coordinatenstelsel: findValue(row, OpdrachtHeader, 'locatie-coordinatenstelsel'),
            wkt: findValue(row, OpdrachtHeader, 'locatie-wkt')
        },
        kwaliteit: null
      }
    };




    if (hasRequiredProperties(row, index, OpdrachtHeader, ['einddatum'])) {
      object['opdracht']['einddatum'] = mapDate(findValue(row, OpdrachtHeader, 'einddatum'))
    }

    if (hasRequiredProperties(row, index, OpdrachtHeader, ['beschrijving'])) {
      object['opdracht']['omschrijving'] = findValue(row, OpdrachtHeader, 'beschrijving')
    }

    var kwaliteit = {
    origine: null,
    aard: null
    }

    if (hasRequiredProperties(row, index, OpdrachtHeader, ['origine'])) {
      kwaliteit['origine'] = findValue(row, OpdrachtHeader, 'origine')
    }
    if (hasRequiredProperties(row, index, OpdrachtHeader, ['aard'])) {
      kwaliteit['aard'] = findValue(row, OpdrachtHeader, 'aard')
    }


    kwaliteit = removeEmptyProperties(kwaliteit)
    if (!(JSON.stringify(kwaliteit).length == '{}')) {
        object['opdracht']['kwaliteit'] = kwaliteit
    }

    const json = JSON.stringify(removeEmptyProperties(object));
    const xml = json2xml(json, { compact: true, spaces: 4 });

    xmlObjects.push(xml);
  });

  if (skippedCounter.opdracht) {
    console.log('\x1b[33m%s\x1b[0m', 'Opgelet: rijen met fouten werden overgeslagen.');
    console.log('\x1b[33m%s\x1b[0m', '<Opdracht>>: ' + skippedCounter.opdracht + ' rijen met fouten');
    if (!verbose) {
      console.log('\x1b[33m%s\x1b[0m', 'Run het script opnieuw met de `-v` parameter om meer informatie te verkrijgen per ongeldige rij.');
    }
  } else {
    console.log('Opdrachten foutloos verwerkt!');
  }
}
