from xmlschema import XMLSchema
from xmlschema import XMLSchemaValidationError
from collections import defaultdict


class Validator:
    def __init__(self, json_dict: dict, xml_schema: XMLSchema, validation: str = 'strict'):
        """
        validation: 'strict' (standaard) laat objecten met XSD-fouten weg uit de XML.
                    'lax' neemt alle objecten op in de XML en rapporteert XSD-fouten enkel als waarschuwing.
                    Bedoeld voor bv. nieuwe parameters/eenheden die nog niet in de DOV-codelijsten zitten.
                    Let op: zo'n XML wordt door DOV pas aanvaard als de codelijsten aangepast zijn.
        """
        assert validation in ('strict', 'lax')
        self.json_dict = json_dict
        self.xml_schema = xml_schema
        self.validation = validation
        self.corrected = defaultdict(list)
        self.errors = defaultdict(list)
        self.warnings = defaultdict(list)

    def validate(self):
        for key, subjects in self.json_dict.items():
            if isinstance(subjects, list):
                for subject in subjects:
                    if self.validation == 'lax':
                        _, errs = self.xml_schema.encode({key: [subject]}, validation='lax', namespaces={
                            'gml': 'http://www.opengis.net/gml/3.2',
                        })
                        self.corrected[key].append(subject)
                        if errs:
                            self.warnings[key].append((subject, errs))
                        continue
                    try:
                        self.xml_schema.encode({key: [subject]}, namespaces={
                            'gml': 'http://www.opengis.net/gml/3.2',
                        })
                        self.corrected[key].append(subject)
                    except XMLSchemaValidationError as e:
                        self.errors[key].append((subject, e))
            else:
                self.corrected[key] = subjects

    def get_error_rapport(self):
        rapport = ''
        for key in (set(self.corrected.keys()) | set(self.errors.keys())) - {'@xmlns:gml'}:
            correct = self.corrected[key]
            wrong = self.errors[key]

            n = len(wrong) + len(correct)

            rapport += f'# Summary {key}: ' + \
                       f'{n} object{"s" if n > 1 or n == 0 else ""} of type {key} have been detected. ' + \
                       f'{len(correct) if wrong else "All"} of which have been succesfully converted to xml\n'

            if wrong:
                rapport += f'{len(wrong)} {"was" if len(wrong) == 1 else "were"} not converted:\n'

                for i, error in enumerate(wrong):
                    o, e = error
                    e = str(e).replace("\n", "\n\t\t")
                    rapport += f'\t {i + 1}. {key} with values {o}:\n\tThe following error occured:\n'
                    rapport += f'\t\t{e}\n'
                    rapport += '-------------------------------------\n'

            if self.warnings[key]:
                rapport += f'WAARSCHUWING (lax-modus): {len(self.warnings[key])} {key}-object(en) bevatten XSD-fouten ' \
                           f'maar zijn toch in de XML opgenomen:\n'
                for i, (o, errs) in enumerate(self.warnings[key]):
                    rapport += f'\t {i + 1}. {key} with values {o}:\n'
                    for e in errs:
                        reason = getattr(e, 'reason', None) or str(e).split('\n')[0]
                        path = getattr(e, 'path', None)
                        rapport += f'\t\t- {reason}' + (f' (pad: {path})' if path else '') + '\n'
                    rapport += '-------------------------------------\n'

        return rapport

    def iter_errors(self):
        for e in self.errors.items():
            yield e

    def iter_correct(self):
        for e in self.corrected.items():
            yield e

    def __str__(self):
        return f'Validator({self.xml_schema})'

    def __repr__(self):
        return self.__str__()

    def get_keys(self):
        return set(self.errors.keys()) | set(self.corrected.keys())

    def get_n_correct(self, item):
        return len(self.corrected[item])

    def get_n_error(self, item):
        return len(self.errors[item])
