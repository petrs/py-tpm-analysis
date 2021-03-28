import abc


class Data(object):
    __metaclass__ = abc.ABCMeta

    global_supported_algorithms = []
    global_supported_commands = []
    global_supported_ecc = []

    global_properties_fixed = []
    global_performance = {}

    def __init__(self, detail):
        self.detail = detail

        self.manufacturer = None
        self.vendor_string = None
        self.firmware_version = None
        self.no_tpm = False

        self.inconclusive_ecc = False

        self.test_version = None
        self.tpm_version = None

        self.pc = None

        self.properties_fixed = {}
        self.performance = {}
        self.supported_algorithms = []
        self.supported_commands = []
        self.supported_ecc = []

    @staticmethod
    def get_property_value(line, value):
        additional_info = ''
        if '0x' in value:
            additional_info = ' ('
            try:
                if 'MANUFACTURER' in line or 'VENDOR_STRING' in line or 'FAMILY_INDICATOR' in line:
                    string = bytearray.fromhex(value.replace('0x', '')).decode()
                    additional_info += string
                else:
                    raise ValueError
            except (UnicodeDecodeError, ValueError):
                additional_info += str(int(value, 0))
            additional_info += ')'
        return additional_info

    @abc.abstractmethod
    def parse_meta(self):
        """Parses meta data"""
        return

    @abc.abstractmethod
    def parse_properties_fixed(self):
        """Parses fixed properties"""
        return

    @abc.abstractmethod
    def parse_algorithms(self):
        """Parses algorithms"""
        return

    @abc.abstractmethod
    def parse_commands(self):
        """Parses commands"""
        return

    @abc.abstractmethod
    def parse_ecc(self):
        """Parses ecc"""
        return

    @abc.abstractmethod
    def parse_performance(self):
        """Parses performance"""
        return
