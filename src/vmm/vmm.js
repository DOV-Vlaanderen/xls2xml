import * as fs from 'fs';
import { writeFile } from 'fs/promises';
import { XMLParser } from 'fast-xml-parser';
import fetch from 'node-fetch';

import { removeEmptyProperties, mapHeader, findValue, readCsv, mapNumber, mapBetrouwbaarheid, mapMethodeXY, mapMethodeZ, mapDate } from '../utils.js';
import moment from 'moment';
import { json2xml } from 'xml-js';

const putCache = {};
const boringCache = {};
const privatePutten = [];
const privateFilters = [];
const privateBoringen = [];

const xmlObjects = { putten: [], boringen: [], filters: [] };

export async function createUpdateXML() {
  const started = moment();
  await generatePuttenXML();

  if (privatePutten.length) {
    console.log('\nGenereren private putten CSV...');

    const resultString = privatePutten.join('\n');
    fs.writeFile('./dist/vmm/privatePutten.csv', resultString, { flag: 'w+' }, (err) => {
      if (err) {
        console.error(err);
      }
    });
  }

  if (privateBoringen.length) {
    console.log('\nGenereren private boringen CSV...');

    const resultString = privateBoringen.join('\n');
    fs.writeFile('./dist/vmm/privateBoringen.csv', resultString, { flag: 'w+' }, (err) => {
      if (err) {
        console.error(err);
      }
    });
  }

  if (privateFilters.length) {
    console.log('\nGenereren private filters CSV...');

    const resultString = privateFilters.join('\n');
    fs.writeFile('./dist/vmm/privateFilters.csv', resultString, { flag: 'w+' }, (err) => {
      if (err) {
        console.error(err);
      }
    });
  }

  // Write XML files
  if (xmlObjects.putten.length) {
    console.log('\nGenereren putten XML...');

    const resultString = xmlObjects.putten.join('\n');
    const xmlString = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<ns3:dov-schema xmlns:ns3="http://kern.schemas.dov.vlaanderen.be">\n${resultString}\n</ns3:dov-schema>`;

    fs.writeFile('./dist/vmm/putten.xml', xmlString, { flag: 'w+' }, (err) => {
      if (err) {
        console.error(err);
      }
    });

    console.log('\x1b[32m%s\x1b[0m', 'Klaar! Je kan de putten.xml terugvinden in de `dist` folder.');
  } else {
    console.log('\x1b[33m%s\x1b[0m', 'Geen te verwerken putten gevonden.');
  }

  if (xmlObjects.boringen.length) {
    console.log('\nGenereren boringen XML...');

    const resultString = xmlObjects.boringen.join('\n');
    const xmlString = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<ns3:dov-schema xmlns:ns3="http://kern.schemas.dov.vlaanderen.be">\n${resultString}\n</ns3:dov-schema>`;

    fs.writeFile('./dist/vmm/boringen.xml', xmlString, { flag: 'w+' }, (err) => {
      if (err) {
        console.error(err);
      }
    });

    console.log('\x1b[32m%s\x1b[0m', 'Klaar! Je kan de boringen.xml terugvinden in de `dist` folder.');
  } else {
    console.log('\x1b[33m%s\x1b[0m', 'Geen te verwerken boringen gevonden.');
  }

  if (xmlObjects.filters.length) {
    console.log('\nGenereren filtermetingen XML...');

    const resultString = xmlObjects.filters.join('\n');
    const xmlString = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<ns3:dov-schema xmlns:ns3="http://kern.schemas.dov.vlaanderen.be">\n${resultString}\n</ns3:dov-schema>`;

    fs.writeFile('./dist/vmm/filtermetingen.xml', xmlString, { flag: 'w+' }, (err) => {
      if (err) {
        console.error(err);
      }
    });

    console.log('\x1b[32m%s\x1b[0m', 'Klaar! Je kan de filtermetingen.xml terugvinden in de `dist` folder.');
  } else {
    console.log('\x1b[33m%s\x1b[0m', 'Geen te verwerken filtermetingen gevonden.');
  }

  console.log(`Totale rekentijd: ${Math.round(moment().diff(started, 'minutes'))} minuten`);
}

async function generatePuttenXML() {
  // Read csv
  console.log('Inlezen putten...');

  const putData = readCsv('./data/vmm/invoerdata.csv');

  const putHeader = mapHeader(putData[0]);

  const boringData = readCsv('./data/vmm/boringen.csv');

  const boringHeader = mapHeader(boringData[0]);

  // Remove header lines at the top
  putData.splice(0, 1);
  boringData.splice(0, 1);

  // Loop through records
  await readRowsAsync({ putData, putHeader, boringData, boringHeader });
}

function readRowsAsync(opts) {
  const { putData, putHeader, boringData, boringHeader } = opts;

  return new Promise(async (res) => {
    for (let [i, row] of putData.entries()) {
      // Fetch PUT xml from DOV, if available
      const permkey = findValue(row, putHeader, 'permkey_put');

      let put;
      let obj = {};
      if (putCache[permkey]) {
        put = JSON.parse(JSON.stringify(putCache[permkey]));
      } else {
        console.log(`Putinformatie ophalen (${i + 1}/${putData.length}): ${permkey}`);
        const response = await fetch(`https://dov.vlaanderen.be/data/put/${permkey}.json`, {
          method: 'GET',
        });

        obj = await response.json().catch((err) => {
          console.log('Put is niet publiek beschikbaar: ' + permkey);
          privatePutten.push(permkey);
        });

        if (privatePutten.includes(permkey)) {
          if (fs.existsSync(`./data/vmm/niet_publieke_putten/${permkey}.json`)) {
            console.log('Put lokaal ophalen:', permkey);
            const json = fs.readFileSync(`./data/vmm/niet_publieke_putten/${permkey}.json`, { encoding: 'utf-8' }).toString();
            obj = JSON.parse(json);
          }
        }

        if (!obj) {
          continue;
        }

        if (Array.isArray(obj.grondwaterlocatie)) {
          put = obj.grondwaterlocatie[0];
        } else {
          console.log(obj);
          put = obj.grondwaterlocatie;
        }

        // If not available, fetch PUT xml from local files

        putCache[permkey] = JSON.parse(JSON.stringify(put));
      }

      // // Update PUT XYZ and add old XYZ to opmerking
      const oldLigging = JSON.parse(JSON.stringify(put.puntligging));
      put.puntligging.xy.x = mapNumber(findValue(row, putHeader, 'X'));
      put.puntligging.xy.y = mapNumber(findValue(row, putHeader, 'Y'));
      put.puntligging.xy.betrouwbaarheid = mapBetrouwbaarheid(findValue(row, putHeader, 'betrouwbaarheid XY'));
      put.puntligging.xy.methodeOpmeten = mapMethodeXY(findValue(row, putHeader, 'MethodeXY'));
      put.puntligging.xy.origineOpmeten.naam = findValue(row, putHeader, 'OrigineXY');
      put.puntligging.oorspronkelijkMaaiveld.waarde = mapNumber(findValue(row, putHeader, 'Zmaaiveld'));
      put.puntligging.oorspronkelijkMaaiveld.betrouwbaarheid = mapBetrouwbaarheid(findValue(row, putHeader, 'betrouwbaarheid Z'));
      put.puntligging.oorspronkelijkMaaiveld.methodeOpmeten = mapMethodeZ(findValue(row, putHeader, 'MethodeZ'));
      put.puntligging.oorspronkelijkMaaiveld.origineOpmeten.naam = findValue(row, putHeader, 'OrigineZ');

      put.opmerking = [
        {
          tekst: `${findValue(row, putHeader, 'opmerking put')} \nXYZ waarden vóór de automatische bulk update: ${JSON.stringify({
            xy: oldLigging.xy,
            oorspronkelijkMaaiveld: oldLigging.oorspronkelijkMaaiveld,
          })}.`,
          auteur: {
            naam: 'De Rouck',
            voornaam: 'Tinneke',
          },
          datum: moment().format('yyyy-MM-DD'),
        },
      ];

      put = mapPutObjectToValidXML(put);

      // If the PUT is linked to a BORING, we should update the BORING AND the PUT
      if (put.boring) {
        let boring;
        let boringObj = {};

        if (boringCache[put.boring]) {
          boring = JSON.parse(JSON.stringify(boringCache[put.boring]));
        } else {
          // Find boring permkey in boringData
          const record = boringData.find((row) => findValue(row, boringHeader, 'boringnummer') === put.boring);
          const boringPermkey = findValue(record, boringHeader, 'permkey_boring');

          console.log(`Boringinformatie ophalen (${i + 1}/${putData.length}): ${boringPermkey}`);
          const response = await fetch(`https://dov.vlaanderen.be/data/boring/${boringPermkey}.json`, {
            method: 'GET',
          });

          boringObj = await response.json().catch((err) => {
            console.log('Boring is niet publiek beschikbaar: ' + boringPermkey);
            privateBoringen.push(boringPermkey);
          });

          if (privateBoringen.includes(boringPermkey)) {
            if (fs.existsSync(`./data/vmm/niet_publieke_boringen/${boringPermkey}.json`)) {
              console.log('Boring lokaal ophalen:', boringPermkey);
              const json = fs.readFileSync(`./data/vmm/niet_publieke_boringen/${boringPermkey}.json`, { encoding: 'utf-8' }).toString();
              boringObj = JSON.parse(json);
            }
          }

          if (!boringObj) {
            continue;
          }

          if (Array.isArray(boringObj.boring)) {
            boring = boringObj.boring[0];
          } else {
            console.log(boringObj);
            boring = boringObj.boring;
          }
        }

        boringCache[put.boring] = JSON.parse(JSON.stringify(boring));

        const oldLigging = JSON.parse(JSON.stringify({ xy: boring.xy, oorspronkelijkMaaiveld: boring.oorspronkelijkMaaiveld }));
        boring.xy.x = mapNumber(findValue(row, putHeader, 'X'));
        boring.xy.y = mapNumber(findValue(row, putHeader, 'Y'));
        boring.xy.betrouwbaarheid = mapBetrouwbaarheid(findValue(row, putHeader, 'betrouwbaarheid XY'));
        boring.xy.methodeOpmeten = mapMethodeXY(findValue(row, putHeader, 'MethodeXY'));
        boring.xy.origineOpmeten.naam = findValue(row, putHeader, 'OrigineXY');
        boring.oorspronkelijkMaaiveld.waarde = mapNumber(findValue(row, putHeader, 'Zmaaiveld'));
        boring.oorspronkelijkMaaiveld.betrouwbaarheid = mapBetrouwbaarheid(findValue(row, putHeader, 'betrouwbaarheid Z'));
        boring.oorspronkelijkMaaiveld.methodeOpmeten = mapMethodeZ(findValue(row, putHeader, 'MethodeZ'));
        boring.oorspronkelijkMaaiveld.origineOpmeten.naam = findValue(row, putHeader, 'OrigineZ');

        boring.opmerking = [
          {
            tekst: `${findValue(row, putHeader, 'opmerking put')} \nXYZ waarden vóór de automatische bulk update: ${JSON.stringify({
              xy: oldLigging.xy,
              oorspronkelijkMaaiveld: oldLigging.oorspronkelijkMaaiveld,
            })}.`,
            auteur: {
              naam: 'De Rouck',
              voornaam: 'Tinneke',
            },
            datum: moment().format('yyyy-MM-DD'),
          },
        ];

        boring = mapBoringObjectToValidXML(boring);

        const boringJson = JSON.stringify({ boring });
        const boringXml = json2xml(boringJson, { compact: true, spaces: 4 });

        xmlObjects.boringen.push(boringXml);
      }

      // Write to object
      obj.grondwaterlocatie = put;
      const putJson = JSON.stringify(obj);
      const putXml = json2xml(putJson, { compact: true, spaces: 4 });

      xmlObjects.putten.push(putXml);

      // Update filter referentiepunten
      // Fetch filter from DOV, if available
      const permkeyFilter = findValue(row, putHeader, 'permkey_filter');
      console.log(`Filterinformatie ophalen (${i + 1}/${putData.length}): ${permkeyFilter}`);
      const responseFilter = await fetch(`https://dov.vlaanderen.be/data/filter/${permkeyFilter}.json`, {
        method: 'GET',
      });

      let obj2 = await responseFilter.json().catch((err) => {
        console.log('Filter is niet publiek beschikbaar: ' + permkeyFilter);
        privateFilters.push(permkeyFilter);
      });

      if (privateFilters.includes(permkeyFilter)) {
        if (fs.existsSync(`./data/vmm/niet_publieke_filters/${permkeyFilter}.json`)) {
          console.log('Filter lokaal ophalen:', permkeyFilter);
          const json = fs.readFileSync(`./data/vmm/niet_publieke_filters/${permkeyFilter}.json`, { encoding: 'utf-8' }).toString();
          obj2 = JSON.parse(json);
        }
      }

      if (!obj2) {
        continue;
      }

      let filter;
      if (Array.isArray(obj2.filter)) {
        filter = obj2.filter.find((f) => f.dataidentifier.permkey === permkeyFilter);
      } else {
        filter = obj2.filter;
      }

      let filtermeting = {
        grondwaterlocatie: put.identificatie,
        filter: {
          identificatie: filter.identificatie,
          filtertype: filter.filtertype.toLowerCase().replace(/_/g, ' '),
        },
      };

      if (Array.isArray(obj2.filtermeting)) {
        filtermeting = obj2.filtermeting.find((f) => f.filter.identificatie === filter.identificatie);
      } else if (obj2.filtermeting) {
        console.log(obj2);
        filtermeting = obj2.filtermeting;
      }

      filtermeting.referentiepunt = [];
      Array.from(Array(5)).forEach((x, i) => {
        if (findValue(row, putHeader, `DOV Referentie ${i + 1} - DATUM`)) {
          const newRef = {
            datum: mapDate(findValue(row, putHeader, `DOV Referentie ${i + 1} - DATUM`)),
            meetpunt: mapNumber(findValue(row, putHeader, `DOV Referentie ${i + 1} - meetpunt`)),
            referentie: findValue(row, putHeader, `DOV Referentie ${i + 1} - referentiepunt`),
            opmerking: [
              {
                tekst: findValue(row, putHeader, `DOV Referentie ${i + 1} - opmerking`),
                auteur: {
                  naam: 'De Rouck',
                  voornaam: 'Tinneke',
                },
                datum: moment().format('yyyy-MM-DD'),
              },
            ],
          };

          filtermeting.referentiepunt.push(newRef);
        }
      });

      // delete filter.filtermeting;

      // filter.opmerking = [
      //   {
      //     tekst: findValue(row, putHeader, `opmerking filter`),
      //     auteur: {
      //       naam: 'De Rouck',
      //       voornaam: 'Tinneke',
      //     },
      //     datum: moment().format('yyyy-MM-DD'),
      //   },
      // ];

      const filterObj = mapFilterObjectToValidXML({ filter, filtermeting });

      const filterJson = JSON.stringify(filterObj);
      const filterXml = json2xml(filterJson, { compact: true, spaces: 4 });

      xmlObjects.filters.push(filterXml);
    }
    res();
  });
}

function mapPutObjectToValidXML(put) {
  put.puntligging.xy.methode_opmeten = put.puntligging.xy.methodeOpmeten;
  put.puntligging.xy.origine_opmeten = put.puntligging.xy.origineOpmeten;
  put.puntligging.oorspronkelijkMaaiveld.methode_opmeten = put.puntligging.oorspronkelijkMaaiveld.methodeOpmeten;
  put.puntligging.oorspronkelijkMaaiveld.origine_opmeten = put.puntligging.oorspronkelijkMaaiveld.origineOpmeten;
  put.puntligging.oorspronkelijk_maaiveld = put.puntligging.oorspronkelijkMaaiveld;
  put.puntligging.startTovMaaiveld.gestart_op = put.puntligging.startTovMaaiveld.gestartOp;
  put.puntligging.start_tov_maaiveld = put.puntligging.startTovMaaiveld;
  put.puntligging.beschrijving_locatie = put.puntligging.beschrijvingLocatie;

  delete put.puntligging.xy.methodeOpmeten;
  delete put.puntligging.xy.origineOpmeten;
  delete put.puntligging.beschrijvingLocatie;
  delete put.puntligging.oorspronkelijkMaaiveld;
  delete put.puntligging.oorspronkelijk_maaiveld.methodeOpmeten;
  delete put.puntligging.oorspronkelijk_maaiveld.origineOpmeten;
  delete put.puntligging.startTovMaaiveld;
  delete put.puntligging.start_tov_maaiveld.gestartOp;

  const obj = {
    identificatie: put.identificatie,
    dataidentifier: put.dataidentifier,
    grondwaterlocatieType: put.grondwaterlocatieType,
    boring: put.boring,
    puntligging: put.puntligging,
    diepte: put.diepte,
    datum_ingebruikname: put.datumIngebruikname,
    datum_uitgebruikname: put.datumUitgebruikname,
    putsoort: put.putsoort?.toLowerCase().replace(/_/g, ' ').replace('niet ', 'niet-'),
    beheer: put.beheer,
    afwerking: put.afwerking,
    opmerking: put.opmerking,
  };

  return removeEmptyProperties(obj);
}

function mapBoringObjectToValidXML(boring) {
  boring.xy.methode_opmeten = boring.xy.methodeOpmeten;
  boring.xy.origine_opmeten = boring.xy.origineOpmeten;
  boring.oorspronkelijkMaaiveld.methode_opmeten = boring.oorspronkelijkMaaiveld.methodeOpmeten;
  boring.oorspronkelijkMaaiveld.origine_opmeten = boring.oorspronkelijkMaaiveld.origineOpmeten;
  boring.oorspronkelijk_maaiveld = boring.oorspronkelijkMaaiveld;
  boring.startTovMaaiveld.gestart_op = boring.startTovMaaiveld.gestartOp;
  boring.start_tov_maaiveld = boring.startTovMaaiveld;
  boring.beschrijving_locatie = boring.beschrijvingLocatie;

  delete boring.xy.methodeOpmeten;
  delete boring.xy.origineOpmeten;
  delete boring.beschrijvingLocatie;
  delete boring.oorspronkelijkMaaiveld;
  delete boring.oorspronkelijk_maaiveld.methodeOpmeten;
  delete boring.oorspronkelijk_maaiveld.origineOpmeten;
  delete boring.startTovMaaiveld;
  delete boring.start_tov_maaiveld.gestartOp;

  if (boring.wetKader) {
    boring.wetKader.niet_ingedeeld = boring.wetKader.nietIngedeeld;
    delete boring.wetKader.nietIngedeeld;
  }

  if (boring.details?.boormethode?.length) {
    boring.details.boormethode = boring.details.boormethode.map(bm => {
      bm.methode = bm.methode.toLowerCase().replace(/_/g, ' ');
      return bm;
    });
  }

  const obj = {
    identificatie: boring.identificatie,
    dataidentifier: boring.dataidentifier,
    xy: boring.xy,
    oorspronkelijk_maaiveld: boring.oorspronkelijk_maaiveld,
    start_tov_maaiveld: boring.start_tov_maaiveld,
    diepte_van: boring.diepteVan,
    diepte_tot: boring.diepteTot,
    datum_aanvang: boring.datumAanvang,
    helling: boring.helling,
    richting: boring.richting,
    doel: boring.doel ? (boring.doel.slice(0, 1) + boring.doel.slice(1).toLowerCase()).replace(/_/g, ' ') : null,
    boringtype: boring.boringtype,
    wet_kader: boring.wetKader,
    uitvoerder: boring.uitvoerder,
    opdrachtgever: boring.opdrachtgever,
    dataleverancier: boring.dataleverancier,
    boormeester: boring.boormeester,
    boorgatmeting: boring.boorgatmeting,
    stalen: boring.stalen,
    details: boring.details,
    opmerking: boring.opmerking,
  };

  return removeEmptyProperties(obj);
}

function mapFilterObjectToValidXML({ filter, filtermeting }) {
  const meting = {
    grondwaterlocatie: filtermeting.grondwaterlocatie,
    filter: {
      identificatie: filtermeting.filter.identificatie,
      filtertype: filtermeting.filter.filtertype.toLowerCase().replace(/_/g, ' '),
    },
    referentiepunt: filtermeting.referentiepunt,
    opmerking: filtermeting.opmerking
  };

  // filter.ligging.aquifer = filter.ligging.aquifer.replace('VALUE_', '');
  // delete filter.ligging.grondwatersysteem;
  // filter.ligging.afgesloten_volgens_gwdecreet = filter.ligging.afgeslotenVolgensGwdecreet;
  // delete filter.ligging.afgeslotenVolgensGwdecreet;
  // filter.ligging.regime = filter.ligging.regime.toLowerCase().replace(/_/g, ' ');

  // if (filter.opbouw?.onderdeel) {
  //   filter.opbouw.onderdeel = filter.opbouw.onderdeel.map(od => {
  //     od.filterelement = od.filterelement.toLowerCase().replace(/_/g, ' ')
  //     return od;
  //   });
  // }

  // const f = {
  //   identificatie: filter.identificatie,
  //   dataidentifier: filter.dataidentifier,
  //   filtertype: filter.filtertype.toLowerCase().replace(/_/g, ' '),
  //   grondwaterlocatie: filter.grondwaterlocatie,
  //   meetnet: filter.meetnet.replace('VALUE_', ''),
  //   datum_ingebruikname: filter.datumIngebruikname,
  //   monsternameMogelijk: filter.monsternameMogelijk,
  //   ligging: filter.ligging,
  //   opbouw: filter.opbouw,
  //   opmerking: filter.opmerking
  // }

  return removeEmptyProperties({ filtermeting: meting });
}
