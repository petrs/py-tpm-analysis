from .data import Data
import os
import constatnts

class WindowsCase(Data):
    def parse_properties_fixed(self):
        if os.path.isfile(self.detail):
            with open(self.detail, 'r', encoding="utf-16le") as properties_file:
                read_capabilities = False
                for line in properties_file:
                    if "Capabilities" in line:
                        read_capabilities = True
                    elif read_capabilities:
                        if line.strip().startswith('-TPM'):
                            dash = line.find('-')
                            colon = line.find(':')
                            if dash and colon:
                                capability = line[dash+1:colon].strip()
                                capability = capability.replace('TPM', 'TPMx')
                                value = line[colon+1:]
                                value = value.strip()

                                additional_info = self.get_property_value(line, value)

                                self.properties_fixed[capability] = value + additional_info
                                if capability not in Data.global_properties_fixed: Data.global_properties_fixed.append(capability)
                        else:
                            read_capabilities = False

    def parse_algorithms(self):
        if os.path.isfile(self.detail):
            with open(self.detail, 'r', encoding="utf-16le") as properties_file:
                read_algorithms = False
                for line in properties_file:
                    if "Supported Algorithms" in line:
                        read_algorithms = True
                    elif read_algorithms:
                        if line.strip().startswith('-TPM') and ":" not in line:
                            dash = line.find('-')
                            if dash:
                                value = line[dash+1:]
                                value = value.strip()

                                try:
                                    key = list(constatnts.supported_algorithms.keys())[list(constatnts.supported_algorithms.values()).index(value)]
                                except ValueError:
                                    if value == 'TPM_ALG_SHA1':
                                        key = '0x4'
                                    else:
                                        continue

                                self.supported_algorithms.append(key)
                                if key not in Data.global_supported_algorithms: Data.global_supported_algorithms.append(key)

                        else:
                            read_algorithms = False

    def parse_commands(self):
        if os.path.isfile(self.detail):
            with open(self.detail, 'r', encoding="utf-16le") as properties_file:
                read_commands = False
                for line in properties_file:
                    if "Supported Commands" in line:
                        read_commands = True
                    elif read_commands:
                        if line.strip().startswith('-TPM') and ":" not in line:
                            dash = line.find('-')
                            if dash:
                                value = line[dash + 1:]
                                value = value.strip()

                                if "TPM2" in value:
                                    value = value.replace('TPM2_', 'CC_')
                                else:
                                    value = value.replace('TPM_', 'CC_')

                                try:
                                    key = list(constatnts.supported_commands.keys())[list(constatnts.supported_commands.values()).index(value)]
                                except ValueError:
                                    continue

                                self.supported_commands.append(key)
                                if key not in Data.global_supported_commands: Data.global_supported_commands.append(key)
                        else:
                            read_commands = False

    def parse_ecc(self):
        self.inconclusive_ecc = True

    def parse_performance(self):
        pass

    def parse_meta(self):
        manufacturer = ''
        vendor_string = ''
        fw = ''
        no_tpm = False

        if os.path.isfile(self.detail):
            with open(self.detail, 'r', encoding="utf-16le") as properties_file:
                for line in properties_file:

                    if "TPM Manufacturer ID" in line:
                        x = line.find(':')
                        manufacturer = line[x+1:]
                        manufacturer = manufacturer.strip()
                    elif "TPM Manufacturer Version" in line:
                        x = line.find(':')
                        fw = line[x + 1:]
                        fw = fw.strip()

        self.manufacturer = manufacturer.replace('\0', '')
        self.vendor_string = vendor_string.replace('\0', '')
        self.firmware_version = fw
        self.no_tpm = no_tpm
