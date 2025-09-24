from xmlschema import XMLSchema
from xmlschema import XMLSchemaValidationError
from collections import defaultdict


class Validator:
    def __init__(self, json_dict: dict, xml_schema: XMLSchema):
        self.json_dict = json_dict
        self.xml_schema = xml_schema
        self.corrected = defaultdict(list)
        self.errors = defaultdict(list)

    def validate(self):
        for key, subjects in self.json_dict.items():
            for subject in subjects:
                try:
                    self.xml_schema.encode({key: subject})
                    self.corrected[key].append(subject)
                except XMLSchemaValidationError as e:
                    self.errors[key].append((subject, e))

    def get_error_rapport(self):
        rapport = ''
        for key in set(self.corrected.keys()) | set(self.errors.keys()):
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
