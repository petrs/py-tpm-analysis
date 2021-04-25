import argparse
import sys
import os
import zipfile
import constatnts
from record import Record
from analytics.data import Data
import json
from shutil import copy

# output directory
output = ''


def create_arg_parser():
    parser = argparse.ArgumentParser(description='Analyzes results from TPM testing.')
    parser.add_argument('input', help='Path to the results directory.')
    parser.add_argument('--output', help='Path to the output folder, will create files on its own')
    parser.add_argument('-d', default=False,
                        dest='check_for_unzips',
                        help='Will not extract an archive if already extracted (by name)')
    return parser


def scan_directory(input_directory, check_for_unzips):
    class FolderExistsException(Exception):
        pass

    rcrds = []
    # unzip
    index = 1
    for line in os.listdir(input_directory):
        file_path = input_directory + '/' + line
        rcrd = Record(file_path)

        if not line.startswith("."):
            if zipfile.is_zipfile(file_path):
                with zipfile.ZipFile(file_path, "r") as zip_ref:
                    try:
                        folder_path = os.path.splitext(file_path)[0]
                        folder_index = 0
                        while os.path.exists(folder_path if folder_index == 0 else folder_path + '_' + str(folder_index)):
                            if check_for_unzips:
                                raise FolderExistsException
                            folder_index += 1
                        if folder_index > 0:
                            rcrd.set_flag(constatnts.RECORD_FLAG_NON_UNIQUE_FOLDER_NAME, True)
                            folder_path += ('_' + str(folder_index))

                        zip_ref.extractall(folder_path)
                        setattr(rcrd, 'path', folder_path)
                    except (FolderExistsException, zipfile.BadZipfile) as ex:
                        continue
            else:
                if line.endswith('.zip'):
                    continue
                setattr(rcrd, 'index', index)
                index += 1
            rcrds.append(rcrd)

    return rcrds


def sort_lists():
    Data.global_supported_algorithms.sort(key=lambda h: int(h, 0))
    Data.global_supported_commands.sort(key=lambda h: int(h, 0))
    Data.global_supported_ecc.sort(key=lambda h: int(h, 0))


def sort_results(cols):
    move_back = []
    cols.sort(key=sort_by_vendor)

    for index, result in enumerate(cols):
        for i, dataset in enumerate(result['dataset']):
            if 'no_tpm' in dataset and i == 0:
                if dataset['no_tpm']:
                    move_back.append(index)
                    break

    for x, index in enumerate(move_back):
        cols.append(cols.pop(index - x))

    for index, result in enumerate(cols):
        result['id'] = index

        name = ''
        if result['dataset'][0]['manufacturer']:
            name += result['dataset'][0]['manufacturer']

        if result['dataset'][0]['firmware']:
            name += ' ' + result['dataset'][0]['firmware']

        if result['dataset'][0]['vendor']:
            name += ' ' + result['dataset'][0]['vendor']

        if name:
            result['name'] = name


def sort_by_vendor(e):
    manufacturer = None
    fw = None
    if 'manufacturer' in e['dataset'][0]:
        manufacturer = e['dataset'][0]['manufacturer']
    if 'firmware' in e['dataset'][0]:
        fw = e['dataset'][0]['firmware']

    return [manufacturer, fw]


def calculate_meta(cols):
    meta = {
        'total': len(cols),
        'total_tpm': 0,
        'supported_algorithms': {},
        'supported_commands': {},
        'supported_ecc': {}
    }

    for column in cols:
        if not column['dataset'][0]['no_tpm']:
            meta['total_tpm'] += 1

        for algorithm in column['dataset'][0]['supported_algorithms']:
            if algorithm in meta['supported_algorithms']:
                meta['supported_algorithms'][algorithm] += 1
            else:
                meta['supported_algorithms'][algorithm] = 1

        for command in column['dataset'][0]['supported_commands']:
            if command in meta['supported_commands']:
                meta['supported_commands'][command] += 1
            else:
                meta['supported_commands'][command] = 1

        for ecc in column['dataset'][0]['supported_ecc']:
            if ecc in meta['supported_ecc']:
                meta['supported_ecc'][ecc] += 1
            else:
                meta['supported_ecc'][ecc] = 1

    return meta


def get_revisions():
    revs = {
        'algorithms': {},
        'commands': {},
        'ecc': {}
    }

    for algorithm in constatnts.supported_algorithms:
        revs['algorithms'][algorithm] = alg_revision(constatnts.supported_algorithms[algorithm])

    for command in constatnts.supported_commands:
        revs['commands'][command] = com_revision(constatnts.supported_commands[command])

    for ec in constatnts.supported_ecc:
        revs['ecc'][ec] = ecc_revision(constatnts.supported_ecc[ec])

    return revs


def alg_revision(name):
    if name in ['TPM_ALG_CAMELLIA']:
        return '1.22'
    if name in ['TPM_ALG_TDES', 'TPM_ALG_SHA3_256', 'TPM_ALG_SHA3_384', 'TPM_ALG_SHA3_512']:
        return '1.24'
    if name in ['TPM_ALG_CMAC']:
        return '1.27'
    if name in ['TPM_ALG_CCM', 'TPM_ALG_GCM', 'TPM_ALG_KW', 'TPM_ALG_KWP', 'TPM_ALG_EAX', 'TPM_ALG_EDDSA']:
        return '1.32'
    if name in []:
        return 'unknown'
    return '1.15'


def com_revision(name):
    if name in ['CC_PolicyNvWritten']:
        return '0.99'
    if name in []:
        return '1.16'
    if name in ['CC_PolicyTemplate', 'CC_CreateLoaded', 'CC_PolicyAuthorizeNV', 'CC_Vendor_TCG_Test', 'CC_EncryptDecrypt2']:
        return '1.38'
    if name in ['CC_AC_GetCapability', 'CC_AC_Send', 'CC_Policy_AC_SendSelect']:
        return '1.59'
    if name in []:
        return 'unknown'
    return '0.96'


def ecc_revision(name):
    if name in []:
        return '1.22'
    if name in []:
        return '1.24'
    if name in []:
        return '1.27'
    if name in ['TPM_ECC_BP_P256_R1', 'TPM_ECC_BP_P384_R1', 'TPM_ECC_BP_P512_R1', 'TPM_ECC_CURVE_25519']:
        return '1.32'
    if name in []:
        return 'unknown'
    return '1.15'


def create_supporting_files(cols, out):

    # unused code, but it does generate some general statistics
    stats = {
        'manufacturer': {},
        'firmware': {},
        'revision': {},
        'family': {}
    }
    for col in cols:
        if col['dataset'][0]['manufacturer'] not in stats['manufacturer']:
            stats['manufacturer'][col['dataset'][0]['manufacturer']] = 1
        else:
            stats['manufacturer'][col['dataset'][0]['manufacturer']] += 1
        if col['dataset'][0]['manufacturer'] not in stats['firmware']:
            stats['firmware'][col['dataset'][0]['manufacturer']] = {}
        if col['dataset'][0]['firmware'] not in stats['firmware'][col['dataset'][0]['manufacturer']]:
            stats['firmware'][col['dataset'][0]['manufacturer']][col['dataset'][0]['firmware']] = 1
        else:
            stats['firmware'][col['dataset'][0]['manufacturer']][col['dataset'][0]['firmware']] += 1
        if 'TPMx_PT_REVISION' in col['dataset'][0]['properties_fixed']:
            if col['dataset'][0]['properties_fixed']['TPMx_PT_REVISION'] not in stats['revision']:
                stats['revision'][col['dataset'][0]['properties_fixed']['TPMx_PT_REVISION']] = 1
            else:
                stats['revision'][col['dataset'][0]['properties_fixed']['TPMx_PT_REVISION']] += 1
        if 'TPMx_PT_FAMILY_INDICATOR' in col['dataset'][0]['properties_fixed']:
            if col['dataset'][0]['properties_fixed']['TPMx_PT_FAMILY_INDICATOR'] not in stats['family']:
                stats['family'][col['dataset'][0]['properties_fixed']['TPMx_PT_FAMILY_INDICATOR']] = 1
            else:
                stats['family'][col['dataset'][0]['properties_fixed']['TPMx_PT_FAMILY_INDICATOR']] += 1

    with open(os.path.join(out, 'data.json'), 'w') as support_file:
        support_file.write(json.dumps(cols))

    with open(os.path.join(out, 'meta.json'), 'w') as support_file:
        support_file.write(json.dumps(calculate_meta(cols)))

    with open(os.path.join(out, 'revision.json'), 'w') as support_file:
        support_file.write(json.dumps(get_revisions()))

    lists = os.path.join(out, 'lists')
    os.makedirs(lists, exist_ok=True)
    with open(os.path.join(lists, 'supported_algorithms.json'), 'w') as support_file:
        support_file.write(json.dumps(Data.global_supported_algorithms))

    with open(os.path.join(lists, 'supported_commands.json'), 'w') as support_file:
        support_file.write(json.dumps(Data.global_supported_commands))

    with open(os.path.join(lists, 'supported_ecc.json'), 'w') as support_file:
        support_file.write(json.dumps(Data.global_supported_ecc))

    with open(os.path.join(lists, 'fixed_properties.json'), 'w') as support_file:
        support_file.write(json.dumps(Data.global_properties_fixed))

    with open(os.path.join(lists, 'performance_metrics.json'), 'w') as support_file:
        support_file.write(json.dumps(Data.global_performance))

    dictionary = os.path.join(out, 'dictionary')
    os.makedirs(dictionary, exist_ok=True)

    with open(os.path.join(dictionary, 'algorithms.json'), 'w') as support_file:
        support_file.write(json.dumps(constatnts.supported_algorithms))

    with open(os.path.join(dictionary, 'commands.json'), 'w') as support_file:
        support_file.write(json.dumps(constatnts.supported_commands))

    with open(os.path.join(dictionary, 'ecc.json'), 'w') as support_file:
        support_file.write(json.dumps(constatnts.supported_ecc))

    copy('distributable/index.html', out)
    copy('distributable/script.js', out)
    copy('distributable/styles.css', out)


if __name__ == "__main__":
    arg_parser = create_arg_parser()
    parsed_args = arg_parser.parse_args(sys.argv[1:])
    if os.path.exists(parsed_args.input):
        output = parsed_args.output
        if not os.path.exists(output):
            try:
                os.makedirs(output)
            except OSError:
                print("Creation of the directory %s failed" % output)
                exit(1)
        records = scan_directory(parsed_args.input, parsed_args.check_for_unzips)

        columns = []
        for record in records:
            record.find_type()
            record.get_meta()
            record.get_results()
            record.get_performance()

            columns.append(record.get_col())

        # sort lists
        sort_lists()
        sort_results(columns)
        create_supporting_files(columns, output)
    else:
        print("Input directory does not exist.")
        exit(1)
