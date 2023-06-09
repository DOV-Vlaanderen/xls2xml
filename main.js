import Parse from 'args-parser';
import { createBodemXML } from './src/bodem.js';
import { createGrondwaterXML } from './src/grondwater.js';
import { setVerbose } from './src/utils.js';

const args = Parse(process.argv);

if (args.verbose || args.v) {
  setVerbose();
}

if (args.bodem) {
  createBodemXML();
}

if (args.grondwater) {
  createGrondwaterXML();
}
