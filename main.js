import Parse from 'args-parser';
import { createGrondwaterXML } from './src/grondwater.js';
import { createOpdrachtXML } from './src/opdracht.js';
import { setVerbose } from './src/utils.js';

const args = Parse(process.argv);

if (args.verbose || args.v) {
  setVerbose();
}

if (args.grondwater) {
  createGrondwaterXML();
}

if (args.opdracht) {
    createOpdrachtXML();
}
