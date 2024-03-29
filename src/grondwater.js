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
  mapBetrouwbaarheid,
  mapMethodeXY,
  hasRequiredProperties,
  readCsv,
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
  if (fs.existsSync('./data/grondwaterlocatie.txt')) {
    generateGrondwaterLocaties();
  } else {
    console.log('Geen bestand grondwaterlocatie.txt gevonden in de `data` folder. Grondwaterlocaties worden overgeslagen in de XML.');
  }

  // Filters
    if (fs.existsSync('./data/filter.txt')) {
    generateFilters();
  } else {
    console.log('Geen bestand filter.txt gevonden in de `data` folder. Filters worden overgeslagen in de XML.');
  }

  // Filtermetingen
    if (fs.existsSync('./data/filtermeting.txt')) {
    generateFilterMetingen();
  } else {
    console.log('Geen bestand filtermeting.txt gevonden in de `data` folder. Filtermetingen worden overgeslagen in de XML.');
  }


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

  const gwLocatieData = readCsv('./data/grondwaterlocatie.txt');

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
        },
        datum_ingebruikname: mapDate(findValue(row, gwLocatieHeader, 'datum_ingebruikname')),
        putsoort: findValue(row, gwLocatieHeader, 'putsoort'),
        beheer: {
          vanaf: mapDate(findValue(row, gwLocatieHeader, 'beheer_vanaf')),
          beheerder: {
            naam: findValue(row, gwLocatieHeader, 'beheer_beheerder_contact_naam'),
          },
        },
        opdracht: findValue(row, gwLocatieHeader, 'opdracht')
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

  const gwFilterData = readCsv('./data/filter.txt');

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
        },
        //status: mapStatus(findValue(row, gwFilterHeader, 'status')),
        opdracht: findValue(row, gwFilterHeader, 'opdracht')
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

  const gwFilterMeting = readCsv('./data/filtermeting.txt');

  const gwFilterMetingHeader = mapHeader(gwFilterMeting[0]);


  // Remove excess lines at the top
  gwFilterMeting.splice(0, 8);


  gwFilterMeting.forEach((row, index) => {

  if (!hasRequiredProperties(row, index, gwFilterMetingHeader, [
        'grondwaterlocatie',
      'filter_identificatie',
      'filter_filtertype'
      ])
    ) {
      skippedCounter.grondwaterlocaties++;

      return;
    }



  var object = {
      filtermeting: {
        grondwaterlocatie: findValue(row, gwFilterMetingHeader, 'grondwaterlocatie'),
        filter: {
          identificatie: findValue(row, gwFilterMetingHeader, 'filter_identificatie'),
          filtertype: findValue(row, gwFilterMetingHeader, 'filter_filtertype'),
        }
      }}

    if (hasRequiredProperties(row, index, gwFilterMetingHeader, [
      'watermonster_identificatie',
      'watermonster_monstername_datum',
      'watermonster_observatie_eenheid',
      'watermonster_observatie_parameter',
      'watermonster_observatie_parametergroep',
      'watermonster_observatie_detectieconditie',
      'watermonster_observatie_veld_labo',
      'watermonster_observatie_waarde_numeriek'])) {


        object = {
      filtermeting: {
        grondwaterlocatie: findValue(row, gwFilterMetingHeader, 'grondwaterlocatie'),
        filter: {
          identificatie: findValue(row, gwFilterMetingHeader, 'filter_identificatie'),
          filtertype: findValue(row, gwFilterMetingHeader, 'filter_filtertype'),
        },
        referentiepunt: null,
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

    }

    if (hasRequiredProperties(row, index, gwFilterMetingHeader, [
      'referentiepunt_datum',
      'referentiepunt_meetpunt',
      'referentiepunt_referentie']))
    {
        object['filtermeting']['referentiepunt'] = {datum:mapDate(findValue(row, gwFilterMetingHeader, 'referentiepunt_datum')),
        meetpunt:mapNumber(findValue(row, gwFilterMetingHeader, 'referentiepunt_meetpunt')),
        referentie:findValue(row, gwFilterMetingHeader, 'referentiepunt_referentie')}

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


