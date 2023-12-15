import moment from 'moment';
import * as fs from 'fs';

export const BETROUWBAARHEID = {
  GOED: 'goed',
  ONBEKEND: 'onbekend',
  TWIJFELACHTIG: 'twijfelachtig',
};

export const METHODE_XY = {
  GOOGLE: 'gedigitaliseerd in Google Earth',
  GRB: 'gedigitaliseerd op GRB',
  KADASTER: 'gedigitaliseerd op kadasterplan',
  ORTHO: 'gedigitaliseerd op orthofoto',
  POPP: 'gedigitaliseerd op Popp-kaart',
  TOPOKAART: 'gedigitaliseerd op topokaart',
  DOSSIERCOORDINATEN: 'gedigitaliseerd op coördinaten uit dossier',
  GPS_10m: 'GPS (nk 10m)',
  GPS_FLEPOS: 'GPS - RTK FLEPOS (nk 2-3cm)',
  GPS_STATISCH: 'GPS statische fasemeting (nk 0,5cm)',
  ONBEKEND: 'methode onbekend',
  TOPOMETING: 'topografisch ingemeten',
  TOTAALSTATION: 'totaalstation',
  DOSSIER: 'uit dossier',
};

export const METHODE_Z = {
  TOPOKAART: 'afgeleid van topokaart',
  MAAIVELD: 'berekend op basis van hoogteverschil met maaiveld',
  DHM_100: 'DHM_v1 100m*100m',
  DHM_25: 'DHM_v1 25m*25m',
  DHM_5: 'DHM_v1 5m*5m',
  DHM_V2: 'DHM_v2',
  GOOGLE: 'gedigitaliseerd in Google Earth',
  GPS: 'GPS',
  GPS_FLEPOS_1: 'GPS - RTK FLEPOS',
  GPS_FLEPOS_2: 'GPS - RTK FLEPOS (model hBG03)',
  GPS_FLEPOS_3: 'GPS - RTK FLEPOS (model hBG18)',
  GPS_STATISCH: 'GPS statische fasemeting',
  ONBEKEND: 'methode onbekend',
  NIET_TE_ACHTERHALEN: 'niet te achterhalen',
  TOPOMETING: 'topografisch ingemeten',
  TOTAALSTATION: 'totaalstation',
  DOSSIER: 'uit dossier',
};

export const STATUS = {
  PUBLIEK: 'publiek',
  PERMANENT_INTERN: 'permanent intern',
  INTERN_IN_VERWERKING: 'intern in verwerking',
  INTERN_AFGEWERKT: 'intern afgewerkt',
  VOOR_PARTNERS: 'voor partners',
};

export let verbose = false;

export function setVerbose() {
  verbose = true;
}

export function mapHeader(header) {
  const result = {};
  header.forEach((el, i) => {
    result[el.toLowerCase()] = i;
  });

  return result;
}

export function findValue(row, header, property) {
  const index = header[property.toLowerCase()];
  return row[index];
}

export function mapDetectieDonditie(condition) {
  if (condition === '<' || condition === '>') {
    return condition;
  }

  return null;
}

export function mapNumber(value) {
  if (!value) {
    return null;
  }

  value = value.replace(/ /g, '').replace(/,/g, '.');

  if (Number.isNaN(+value)) {
    return null;
  }

  return Math.round(+value * 100) / 100;
}

export function mapDate(value) {
  value = value.replace( /(\d{2})[-/](\d{2})[-/](\d+)/, "$2/$1/$3")
  if (!value || value.toLowerCase() === 'onbekend' || value.toLowerCase() === 'niet beschikbaar' || value.toLowerCase() === 'niet gekend') {
    return null;
  }
  return moment(value.replace("'", '')).format('yyyy-MM-DD');
}

export function mapTime(value) {
  if (!value || value.toLowerCase() === 'onbekend' || value.toLowerCase() === 'niet beschikbaar' || value.toLowerCase() === 'niet gekend') {
    return null;
  }

  if (value.match(/^[0-9]{4}$/g)) {
    return value.substr(0, 2) + ':' + value.substr(2, 2);
  }

  if (value.match(/^[0-9]{2}$/g)) {
    return value + ':00';
  }

  if (value.match(/^[0-9]{1}$/g)) {
    return '0' + value + ':00';
  }

  if (value.match(/^[0-9]{2}:[0-9]{2}$/g)) {
    return value;
  }

  return null;
}

export function mapBetrouwbaarheid(value) {
  return value && Object.values(BETROUWBAARHEID).includes(value.toLowerCase()) ? value.toLowerCase() : BETROUWBAARHEID.ONBEKEND;
}

export function mapMethodeXY(value) {
  return value && Object.values(METHODE_XY).includes(value.toLowerCase()) ? value.toLowerCase() : METHODE_XY.ONBEKEND;
}

export function mapMethodeZ(value) {
  return value && Object.values(METHODE_Z).includes(value.toLowerCase()) ? value.toLowerCase() : METHODE_Z.ONBEKEND;
}

export function mapStatus(value) {
  return value && Object.values(STATUS).includes(value.toLowerCase()) ? value.toLowerCase() : STATUS.PUBLIEK;
}

export function mapStartTovMaaiveld(value) {
  !mapNumber(value) ? 'MAAIVELD' : mapNumber(value) > 0 ? 'BOVEN_MV' : 'ONDER_MV'
}



export function removeEmptyProperties(obj) {
  if (Array.isArray(obj)) {
    for (let item of obj) {
      item = removeEmptyProperties(item);
    }
  } else {
    for (const property in obj) {
      if (obj[property] === undefined || obj[property] === null || obj[property] === '') {
        delete obj[property];
      } else if (typeof obj[property] === 'object' && !(obj instanceof Date)) {
        obj[property] = removeEmptyProperties(obj[property]);
      }
    }
  }

  return obj;
}

export function hasRequiredProperties(row, index, header, properties) {
  let valid = true;
  properties.forEach((property) => {
    if (!findValue(row, header, property)) {
      valid = false;
      if (verbose) {
        console.log('\x1b[33m%s\x1b[0m', 'Rij met ontbrekende waarde: ' + (index + 1).toString() + ' -> ' + property + ' ontbreekt');
      }
    }
  });

  return valid;
}

export function readCsv(path) {
  const data = fs
    .readFileSync(path, {encoding: 'utf-8'})
    .toString()
    .trimEnd('\n')
    .split('\n')
    .map((e) => e.trim())
    .map((e) => e.split('\t').map((e) => e.trim()))
    .filter(row => !!row.find(item => item));

  return data;
}
