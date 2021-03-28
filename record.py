import constatnts
import os

from analytics.algtest import AlgtestCase
from analytics.windows import WindowsCase


class Record:

    record_count = 0

    def __init__(self, path, index=0):
        # destination path
        self.path = path
        self.original_name = os.path.basename(os.path.normpath(path))

        # object meta data
        self.index = index
        self.is_folder = False
        self.test_type = None
        self.detail = None
        self.is_valid_result = True

        self.number_of_results = 1
        self.partial_results = []

        self.flags = {
            constatnts.RECORD_FLAG_NON_UNIQUE_FOLDER_NAME: False
        }

        # TPM specific data
        self.data = None

        # Meta data
        Record.record_count += 1

    def __repr__(self):
        # todo development print

        # if self.number_of_results > 1:
        #     uh = []
        #     for obj in self.partial_results:
        #         uh.append(obj.detail + '\n')
        #     return '\n\nMULTIPLE\n' + ''.join(uh) + '\n\n'
        # else:
        #     return self.original_name + self.detail + '\n'

        # return self.original_name + self.detail + '\n'

        string = str(self.index) + ';' + str(self.number_of_results) + ';' + self.original_name + '\n'
        return string

        if self.number_of_results > 1:
            return 'not_yet \n'
        else:
            if self.data:
                return str(self.data.firmware_version) + '\n'
            else:
                return 'TOTO BY TU NEMELO BYT\n'

    def get_col(self):
        return parse_data(self)

    def get_meta(self):
        if self.number_of_results > 1:
            for record in self.partial_results:
                if record.is_valid_result:
                    record.data.parse_meta()
                    record.data.parse_properties_fixed()
        else:
            if self.is_valid_result:
                self.data.parse_meta()
                self.data.parse_properties_fixed()

    def get_results(self):
        if self.number_of_results > 1:
            for record in self.partial_results:
                if record.is_valid_result:
                    record.data.parse_algorithms()
                    record.data.parse_commands()
                    record.data.parse_ecc()
                    record.data.parse_performance()
        else:
            if self.is_valid_result:
                self.data.parse_algorithms()
                self.data.parse_commands()
                self.data.parse_ecc()
                self.data.parse_performance()

    def get_performance(self):
        pass

    def find_type(self):
        if os.path.isdir(self.path):
            self.is_folder = True

        # folder contains only folders
        if self.is_folder:
            for path, directories, files in os.walk(self.path):
                # variant 1-5
                if check_variants(self, path, directories, files):
                    break
                # variant 6: test in nested folders
                if len(directories) == 1:
                    for path, directories, files in os.walk(os.path.join(self.path, next(iter(directories), None))):
                        # check recursive variant 1-5
                        if check_variants(self, path, directories, files):
                            break
                    break
                # variant 7: multiple tests
                elif len(directories) > 1:
                    self.number_of_results = len(directories)
                    self.test_type = constatnts.HAS_MULTIPLE_TEST
                    self.detail = constatnts.HAS_MULTIPLE_TEST
                    self.is_valid_result = False
                    for directory in directories:
                        new_directory = Record(os.path.join(path, directory))
                        new_directory.find_type()
                        self.partial_results.append(new_directory)
                    break
                else:
                    self.test_type = constatnts.TEST_TYPE_UNSUPPORTED
                    self.is_valid_result = False
                    break
        else:
            if os.path.basename(os.path.normpath(self.path)) == 'TpmInformation.txt':
                self.test_type = constatnts.TEST_TYPE_WINDOWS
                self.detail = self.path
                self.is_folder = False
            else:
                self.test_type = constatnts.TEST_TYPE_UNSUPPORTED
                self.is_valid_result = False

        if self.test_type == constatnts.TEST_TYPE_WINDOWS:
            self.data = WindowsCase(self.detail)
        elif self.test_type == constatnts.TEST_TYPE_ALGTEST:
            self.data = AlgtestCase(self.detail)

    def set_flag(self, name, value):
        self.flags[name] = value

    def get_data(self):
        return {
            'original_name': self.original_name,
            'manufacturer': self.data.manufacturer,
            'firmware': self.data.firmware_version,
            'vendor': self.data.vendor_string,

            'no_tpm': self.data.no_tpm,
            'inconclusive_ecc': self.data.inconclusive_ecc,
            'supported_algorithms': self.data.supported_algorithms,
            'supported_commands': self.data.supported_commands,
            'supported_ecc': self.data.supported_ecc,
            'properties_fixed': self.data.properties_fixed,
            'performance': self.data.performance
        }


def parse_data(record):
    data = {
        'id': record.index,
        'name': record.original_name,
        'dataset': []
    }

    dataset = []
    if record.number_of_results > 1:
        for record in record.partial_results:
            if record.is_valid_result:
                dataset.append(record.get_data())
    else:
        dataset.append(record.get_data())

    data['dataset'] = dataset

    return data

def check_variants(record, path, directories, files):
    # variant 1: algtest folder with result, detail, performance folders within
    if 'detail' in directories and 'performance' in directories:
        record.test_type = constatnts.TEST_TYPE_ALGTEST
        record.detail = os.path.join(path, 'detail')
        return True

    # variant 2: algtest folder with out
    if directories == ['out']:
        for path, directories, files in os.walk(os.path.join(record.path, 'out')):
            if 'detail' in directories and 'performance' in directories:
                record.test_type = constatnts.TEST_TYPE_ALGTEST
                record.detail = os.path.join(path, 'detail')
            # variant 3: algtest folder with detail files in this folder
            elif not directories:
                record.test_type = constatnts.TEST_TYPE_ALGTEST
                record.detail = path
            break
        return True

    # variant 4: windows test
    if 'TpmInformation.txt' in files:
        record.test_type = constatnts.TEST_TYPE_WINDOWS
        record.detail = os.path.join(path, 'TpmInformation.txt')
        return True

    # variant 5: algtest in non structured way
    if not directories and 'Quicktest_properties-fixed.txt' in files:
        record.test_type = constatnts.TEST_TYPE_ALGTEST
        record.detail = path
        return True

    return False

