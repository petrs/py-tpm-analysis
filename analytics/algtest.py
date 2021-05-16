from .data import Data
import os
import glob

# This parser is an extended and modified version of the original
# parser found in https://github.com/crocs-muni/tpm2-algtest
# made by Šimon Struk

class AlgtestCase(Data):
    def parse_performance(self):
        perf_csvs = glob.glob(os.path.join(self.detail, 'Perf_*.csv'))
        perf_csvs.sort()
        command = ''

        heap = {}

        for filepath in perf_csvs:
            filename = os.path.basename(filepath)

            if ':' in filename:
                params_idx = filename.find(':')
            else:
                params_idx = filename.find('_', filename.find('_') + 1)

            suffix_idx = filename.find('.csv')
            new_command = filename[5:suffix_idx if params_idx == -1 else params_idx]
            params = filename[params_idx + 1:suffix_idx].split('_')
            if new_command != command:
                command = new_command
                heap[command] = {}

            if command == 'GetRandom':
                test_case_name = 'Length\n32 bytes'

            elif command in ['Sign', 'VerifySignature', 'RSA_Encrypt', 'RSA_Decrypt']:
                test_case_name = f'{params[0]} {params[1]}\n{params[2]}'

            elif command == 'EncryptDecrypt':
                test_case_name = f'{params[0]} - {params[3]}\nKey len: {params[1]} Mode: {params[2]}\n' \
                                 f'Data length: 256 bytes'

            elif command == 'HMAC':
                test_case_name = 'Hash algorithm\nSHA-256\nData length: 256 bytes'

            elif command == 'Hash':
                test_case_name = f'Hash algorithm\n{params[0]}\nData length: 256 bytes'

            else:
                test_case_name = f'Key parameters:\n{" ".join(params)}'

            heap[command][test_case_name] = {}

            with open(filepath, 'r') as infile:
                avg_op, min_op, max_op, total, success, fail, error = compute_stats(infile)

                heap[command][test_case_name]['avg_op (ms/op)'] = f'{avg_op:.2f}'
                heap[command][test_case_name]['min_op (ms/op)'] = f'{min_op:.2f}'
                heap[command][test_case_name]['max_op (ms/op)'] = f'{max_op:.2f}'
                heap[command][test_case_name]['iterations'] = f'{total}'
                heap[command][test_case_name]['success'] = f'{success}'
                heap[command][test_case_name]['fail'] = f'{fail}'

        self.performance = heap

        for command in heap:
            if command not in Data.global_performance:
                Data.global_performance[command] = {}

            for case in heap[command]:
                if case not in Data.global_performance[command]:
                    Data.global_performance[command][case] = {
                        'avg_op (ms/op)': '',
                        'min_op (ms/op)': '',
                        'max_op (ms/op)': '',
                        'iterations': '',
                        'success': '',
                        'fail': '',
                    }

    def parse_properties_fixed(self):
        qt_properties = os.path.join(self.detail, 'Quicktest_properties-fixed.txt')
        if os.path.isfile(qt_properties):
            with open(qt_properties, 'r') as properties_file:
                will_read = False
                tmp_name = None
                for line in properties_file:
                    if line.startswith('ERROR'):
                        break
                    elif line.startswith('TPM'):
                        if ":" in line:
                            x = line.find(':')
                            name = line[0:x]
                            value = line[x+1:]

                            if name.startswith('TPM2'):
                                name = name.replace('TPM2', 'TPMx', 1)
                            else:
                                name = name.replace('TPM', 'TPMx', 1)

                            if len(value) > 1:
                                # mam hodnotu na radku
                                if name not in self.properties_fixed:
                                    value = value.strip()
                                    if value == '""':
                                        value = 'empty'

                                    additional_info = self.get_property_value(line, value)

                                    self.properties_fixed[name] = value + additional_info
                                    if name not in Data.global_properties_fixed: Data.global_properties_fixed.append(name)
                                continue
                            else:
                                will_read = True
                                tmp_name = name
                    elif will_read:
                        if 'raw' in line or 'UINT32' in line:
                            continue
                        else:
                            x = line.find(':')
                            if x:
                                value = line[x + 1:]
                                if tmp_name not in self.properties_fixed:
                                    value = value.strip()
                                    if value == '""':
                                        value = 'empty'
                                    self.properties_fixed[tmp_name] = value
                                    if tmp_name not in Data.global_properties_fixed: Data.global_properties_fixed.append(tmp_name)
                                will_read = False
                                tmp_name = None
                                continue

    def parse_algorithms(self):
        qt_algorithms = os.path.join(self.detail, 'Quicktest_algorithms.txt')
        if os.path.isfile(qt_algorithms):
            with open(qt_algorithms, 'r') as infile:
                for line in infile:
                    if line.startswith('TPMA_ALGORITHM') or "value" in line:
                        line = line[line.find('0x'):]
                        line = line[:line.find(' ')]
                        line = line.lower()
                        self.supported_algorithms.append(line)
                        if line not in Data.global_supported_algorithms: Data.global_supported_algorithms.append(line)

    def parse_commands(self):
        qt_commands = os.path.join(self.detail, 'Quicktest_commands.txt')
        if os.path.isfile(qt_commands):
            with open(qt_commands, 'r') as infile:
                for line in infile:
                    if line.startswith('  commandIndex:'):
                        line = line[line.find('0x'):]
                        line = line.strip(' \t\n\r')
                        self.supported_commands.append(line)
                        if line not in Data.global_supported_commands: Data.global_supported_commands.append(line)

    def parse_ecc(self):
        qt_ecc_curves = os.path.join(self.detail, 'Quicktest_ecc-curves.txt')
        if os.path.isfile(qt_ecc_curves):
            with open(os.path.join(self.detail, 'Quicktest_ecc-curves.txt'), 'r') as infile:
                for line in infile:
                    if line.startswith('ERROR'):
                        break
                    line = line[line.find('0x'):]
                    line = line.replace(')', '')
                    line = int(line, 0)
                    line = hex(line)
                    self.supported_ecc.append(line)
                    if line not in Data.global_supported_ecc: Data.global_supported_ecc.append(line)

    def parse_meta(self):
        def get_val(line):
            return line[line.find('0x') + 2:-1]

        manufacturer = ''
        vendor_str = ''
        fw = ''
        no_tpm = False
        qt_properties = os.path.join(self.detail, 'Quicktest_properties-fixed.txt')
        if os.path.isfile(qt_properties):
            with open(qt_properties, 'r') as properties_file:
                read_vendor_str = False
                read_vendor_str1 = False
                read_manufacturer_str = False
                read_fw1_str = False
                read_fw2_str = False
                fw1 = ''
                fw2 = ''
                for line in properties_file:
                    if read_vendor_str:
                        val = get_val(line)
                        if len(val) % 2 != 0:
                            val = "0" + val
                        vendor_str += bytearray.fromhex(val).decode()
                        read_vendor_str = False
                    elif read_manufacturer_str:
                        val = get_val(line)
                        if len(val) % 2 != 0:
                            val = "0" + val
                        manufacturer = bytearray.fromhex(val).decode()
                        read_manufacturer_str = False
                    elif read_vendor_str1:
                        vendor_str += bytearray.fromhex(get_val(line)).decode()
                        read_vendor_str1 = False
                    elif line.startswith('TPM2_PT_MANUFACTURER'):
                        read_manufacturer_str = True
                    elif line.startswith('TPM2_PT_FIRMWARE_VERSION_1'):
                        read_fw1_str = True
                    elif read_fw1_str:
                        fw1 = line[line.find('0x') + 2:-1]
                        read_fw1_str = False
                    elif line.startswith('TPM2_PT_FIRMWARE_VERSION_2'):
                        read_fw2_str = True
                    elif read_fw2_str:
                        fw2 = line[line.find('0x') + 2:-1]
                        read_fw2_str = False
                    elif line.startswith('TPM2_PT_VENDOR_STRING_'):
                        read_vendor_str = True
                    elif line.startswith('TPM_PT_MANUFACTURER'):
                        manufacturer = bytearray.fromhex(get_val(line)).decode()
                    elif line.startswith('TPM_PT_FIRMWARE_VERSION_1'):
                        fw1 = get_val(line)
                        assert (len(fw1) == 8)
                    elif line.startswith('TPM_PT_FIRMWARE_VERSION_2'):
                        fw2 = get_val(line)
                        assert (len(fw2) == 8)
                    elif line.startswith('TPM_PT_VENDOR_STRING_'):
                        read_vendor_str1 = True
                    elif line.startswith('ERROR'):
                        no_tpm = True
                try:
                    if no_tpm:
                        fw = ''
                        raise ValueError
                    fw1 = "0" * (8 - len(fw1)) + fw1
                    fw2 = "0" * (8 - len(fw2)) + fw2
                    fw = str(int(fw1[0:4], 16)) + '.' + str(int(fw1[4:8], 16)) + '.' + str(int(fw2[0:4], 16)) + '.' + str(int(fw2[4:8], 16))
                except:
                    fw = ""
        else:
            no_tpm = True

        self.manufacturer = manufacturer.strip().replace('\x00', '')
        self.vendor_string = vendor_str.strip()
        self.firmware_version = fw
        self.no_tpm = no_tpm


def compute_stats(infile, *, rsa2048=False):
    ignore = 5 if rsa2048 else 0
    success, fail, sum_op, min_op, max_op, avg_op = 0, 0, 0, 10000000000, 0, 0
    error = None
    for line in infile:
        if line.startswith('duration'):
            continue
        if ignore > 0:
            ignore -= 1
            continue
        t, rc = line.split(',')[:2]
        rc = rc.replace(' ', '')
        rc = rc.replace('\n', '')
        if rc == '0000':
            success += 1
        else:
            error = rc
            fail += 1
            continue
        t = float(t)
        sum_op += t
        if t > max_op:
            max_op = t
        if t < min_op:
            min_op = t
    total = success + fail
    if success != 0:
        avg_op = (sum_op / success)
    else:
        min_op = 0

    return avg_op * 1000, min_op * 1000, max_op * 1000, total, success, fail, error