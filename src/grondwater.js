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
  filters: 0,
  filtermetingen: 0
};

export function createGrondwaterXML() {
  // Grondwaterlocaties
  if (fs.existsSync('./data/grondwaterlocaties.txt')) {
    generateGrondwaterLocaties();
  } else {
    console.log('Geen bestand grondwaterlocaties.txt gevonden in de `data` folder. Grondwaterlocaties worden overgeslagen in de XML.');
  }

  // Filters
    if (fs.existsSync('./data/filters.txt')) {
    generateFilters();
  } else {
    console.log('Geen bestand filters.txt gevonden in de `data` folder. Filters worden overgeslagen in de XML.');
  }

  // Filtermetingen
    if (fs.existsSync('./data/filtermetingen.txt')) {
    generateFilterMetingen();
  } else {
    console.log('Geen bestand filtermetingen.txt gevonden in de `data` folder. Filtermetingen worden overgeslagen in de XML.');
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

  const gwLocatieData = readCsv('./data/grondwaterlocaties.txt');

  const gwLocatieHeader = mapHeader(gwLocatieData[0]);

  // Remove excess lines at the top
  gwLocatieData.splice(0, 7);

  gwLocatieData.forEach((row, index) => {
    if (
      !hasRequiredProperties(row, index, gwLocatieHeader, [
        'datum_ingebruikname',
        'identificatie',
        'putsoort',
        'beheer_vanaf',
        'beheer_beheerder_contact_naam',
        'puntligging_xy_x',
        'puntligging_xy_y',
        'puntligging_xy_betrouwbaarheid',
        'puntligging_xy_methode_opmeten',
        'puntligging_xy_origine_opmeten_contact_naam',
        'puntligging_oorspronkelijk_maaiveld_waarde',
        'puntligging_oorspronkelijk_maaiveld_origine_opmeten_contact_naam',
        'puntligging_oorspronkelijk_maaiveld_betrouwbaarheid',
        'puntligging_oorspronkelijk_maaiveld_methode_opmeten'
      ])
    ) {
      skippedCounter.grondwaterlocaties++;
      return;
    }

    const object = {
      grondwaterlocatie: {
        identificatie: findValue(row, gwLocatieHeader, 'identificatie'),
        grondwaterlocatieType: 'PUT',
        puntligging: {
          xy: {
            x: mapNumber(findValue(row, gwLocatieHeader, 'puntligging_xy_x')),
            y: mapNumber(findValue(row, gwLocatieHeader, 'puntligging_xy_y')),
            betrouwbaarheid: mapBetrouwbaarheid(findValue(row, gwLocatieHeader, 'puntligging_xy_betrouwbaarheid')),
            methode_opmeten: mapMethodeXY(findValue(row, gwLocatieHeader, 'puntligging_xy_methode_opmeten')),
            origine_opmeten: {
              naam: findValue(row, gwLocatieHeader, 'puntligging_xy_origine_opmeten_contact_naam'),
            },
          },
          oorspronkelijk_maaiveld: {
            waarde: mapNumber(findValue(row, gwLocatieHeader, 'puntligging_oorspronkelijk_maaiveld_waarde')),
            betrouwbaarheid: mapBetrouwbaarheid(findValue(row, gwLocatieHeader, 'puntligging_oorspronkelijk_maaiveld_betrouwbaarheid')),
            methode_opmeten: mapMethodeXY(findValue(row, gwLocatieHeader, 'puntligging_oorspronkelijk_maaiveld_methode_opmeten')),
            origine_opmeten: {
              naam: findValue(row, gwLocatieHeader, 'puntligging_oorspronkelijk_maaiveld_origine_opmeten_contact_naam'),
            },
          },
          //start_tov_maaiveld: {
          //  gestart_op: findValue(row, gwLocatieHeader, 'puntligging_start_tov_maaiveld_contact_gestart_op'),
          //:  verschil: mapNumber(findValue(row, gwLocatieHeader, 'puntligging_start_tov_maaiveld_verschil'))
          //    ? Math.abs(mapNumber(findValue(row, gwLocatieHeader, 'puntligging_start_tov_maaiveld_verschil')))
          //    : null,
          //},
        },
        //diepte: mapNumber(findValue(row, gwLocatieHeader, 'diepte (m)')) ? Math.abs(mapNumber(findValue(row, gwLocatieHeader, 'puntligging_start_tov_maaiveld_verschil'))) : null,
        datum_ingebruikname: mapDate(findValue(row, gwLocatieHeader, 'datum_ingebruikname')),
        putsoort: findValue(row, gwLocatieHeader, 'putsoort'),
        beheer: {
          vanaf: mapDate(findValue(row, gwLocatieHeader, 'beheer_vanaf')),
          beheerder: {
            naam: findValue(row, gwLocatieHeader, 'beheer_beheerder_contact_naam'),
          },
        },
        //status: mapStatus(findValue(row, gwLocatieHeader, 'status')),
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

function generateFilters() {
  // Read csv file
  console.log('Reading filters...');

  const gwFilterData = readCsv('./data/filters.txt');

  const gwFilterHeader = mapHeader(gwFilterData[0]);

  // Remove excess lines at the top
  gwFilterData.splice(0, 4);

  gwFilterData.forEach((row, index) => {
    if (
      !hasRequiredProperties(row, index, gwFilterHeader, [
        'grondwaterlocatie',
        'identificatie',
        'datum_ingebruikname',
        'filtertype',
        'meetnet',
        'ligging_aquifer',
        'ligging_regime',
        'opbouw_onderdeel_van',
        'opbouw_onderdeel_tot'
      ])
    ) {
      skippedCounter.filters++;
      return;
    }

    const object = {
      filter: {
        identificatie: findValue(row, gwFilterHeader, 'identificatie'),
        filtertype: findValue(row, gwFilterHeader, 'filtertype'),
        grondwaterlocatie: findValue(row, gwFilterHeader, 'grondwaterlocatie'),
        meetnet: findValue(row, gwFilterHeader, 'meetnet'),
        datum_ingebruikname: mapDate(findValue(row, gwFilterHeader, 'datum_ingebruikname')),
        ligging: {
          aquifer: findValue(row, gwFilterHeader, 'ligging_aquifer'),
          regime: findValue(row, gwFilterHeader, 'ligging_regime'),
        },
        opbouw: {
          onderdeel: {
            van: mapNumber(findValue(row, gwFilterHeader, 'opbouw_onderdeel_van')),
            tot: mapNumber(findValue(row, gwFilterHeader, 'opbouw_onderdeel_tot')),
            filterelement: findValue(row, gwFilterHeader, 'opbouw_onderdeel_filterelement'),
          }
        }
        //status: mapStatus(findValue(row, gwFilterHeader, 'status')),
      },
    };

    const json = JSON.stringify(removeEmptyProperties(object));
    const xml = json2xml(json, { compact: true, spaces: 4 });

    xmlObjects.push(xml);
  });

  if (skippedCounter.filters) {
    console.log('\x1b[33m%s\x1b[0m', 'Opgelet: rijen met fouten werden overgeslagen.');
    console.log('\x1b[33m%s\x1b[0m', 'Filters: ' + skippedCounter.filters + ' rijen met fouten');
    if (!verbose) {
      console.log('\x1b[33m%s\x1b[0m', 'Run het script opnieuw met de `-v` parameter om meer informatie te verkrijgen per ongeldige rij.');
    }
  } else {
    console.log('Filters foutloos verwerkt!');
  }
}

function generateFilterMetingen() {
  // Read csv file
  console.log('Reading filtermetingen...');

  const gwFilterMeting = readCsv('./data/filtermetingen.txt');

  const gwFilterMetingHeader = mapHeader(gwFilterMeting[0]);

  // Remove excess lines at the top
  gwFilterMeting.splice(0, 8);

  gwFilterMeting.forEach((row, index) => {
    if (!hasRequiredProperties(row, index, gwFilterMetingHeader, [
      'grondwaterlocatie',
      'filter_identificatie',
      'watermonster_identificatie',
      'watermonster_monstername_datum',
      'watermonster_observatie_eenheid',
      'watermonster_observatie_parameter',
      'watermonster_observatie_parametergroep',
      'watermonster_observatie_detectieconditie',
      'watermonster_observatie_veld_labo',
      'watermonster_observatie_waarde_numeriek'])) {
      skippedCounter.filtermetingen++;
      return;
    }

    const object = {
      filtermeting: {
        grondwaterlocatie: findValue(row, gwFilterMetingHeader, 'grondwaterlocatie'),
        filter: {
          identificatie: findValue(row, gwFilterMetingHeader, 'filter_identificatie'),
          filtertype: findValue(row, gwFilterMetingHeader, 'filter_filtertype'),
        },
        watermonster: {
          identificatie: findValue(row, gwFilterMetingHeader, 'watermonster_identificatie'),
          monstername: {
            datum: mapDate(findValue(row, gwFilterMetingHeader, 'watermonster_monstername_datum')),
            labo: {
              naam: findValue(row, gwFilterMetingHeader, 'watermonster_monstername_labo_naam'),
            }
          },
          laboanalyse: {
            datum: mapDate(findValue(row, gwFilterMetingHeader, 'watermonster_laboanalyse_datum')),
            labo: {
              naam: findValue(row, gwFilterMetingHeader, 'watermonster_laboanalyse_labo_naam'),
            }
          },
          observatie: {
            parameter: findValue(row, gwFilterMetingHeader, 'watermonster_observatie_parameter'),
            parametergroep: findValue(row, gwFilterMetingHeader, 'watermonster_observatie_parametergroep'),
            waarde_numeriek: mapNumber(findValue(row, gwFilterMetingHeader, 'watermonster_observatie_waarde_numeriek')),
            eenheid: findValue(row, gwFilterMetingHeader, 'watermonster_observatie_eenheid'),
            detectieconditie: findValue(row, gwFilterMetingHeader, 'watermonster_observatie_detectieconditie'),
            veld_labo: findValue(row, gwFilterMetingHeader, 'watermonster_observatie_veld_labo'),
          }
        }
      }
    }
    const json = JSON.stringify(removeEmptyProperties(object));
    const xml = json2xml(json, { compact: true, spaces: 4 });

    xmlObjects.push(xml);
  });

  if (skippedCounter.filtermetingen) {
    console.log('\x1b[33m%s\x1b[0m', 'Opgelet: rijen met fouten werden overgeslagen.');
    console.log('\x1b[33m%s\x1b[0m', 'Filtermetingen: ' + skippedCounter.filtermetingen + ' rijen met fouten');
    if (!verbose) {
      console.log('\x1b[33m%s\x1b[0m', 'Run het script opnieuw met de `-v` parameter om meer informatie te verkrijgen per ongeldige rij.');
    }
  } else {
    console.log('Filtermetingen foutloos verwerkt!');
  }
}

function generateGrondwaterMonsters() {
  // Read csv file
  console.log('Reading grondwatermonsters...');

  const gwMonsterData = readCsv('./data/grondwatermonsters.txt');

  const gwMonsterHeader = mapHeader(gwMonsterData[0]);

  // Remove excess lines at the top
  gwMonsterData.splice(0, 1);

  gwMonsterData.forEach((row, index) => {
    if (!hasRequiredProperties(row, index, gwMonsterHeader, [
      'grondwaterlocatie',
      'identificatie watermonster',
      'datum monstername'])) {
      skippedCounter.grondwatermonsters++;
      return;
    }

    const object = {
      filtermeting: {
        grondwaterlocatie: findValue(row, gwMonsterHeader, 'grondwaterlocatie'),
        filter: {
          identificatie: findValue(row, gwMonsterHeader, 'filter'),
          //filtertype: findValue(row, gwMonsterHeader, 'filtertype'),
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
