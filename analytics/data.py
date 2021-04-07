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

    # helper function
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

    # parses meta data from corresponding file
    @abc.abstractmethod
    def parse_meta(self):
        """Parses meta data"""
        return

    # parses fixed properties from corresponding file
    @abc.abstractmethod
    def parse_properties_fixed(self):
        """Parses fixed properties"""
        return

    # parses supported algorithms from corresponding file
    @abc.abstractmethod
    def parse_algorithms(self):
        """Parses algorithms"""
        return

    # parses supported commands from corresponding file
    @abc.abstractmethod
    def parse_commands(self):
        """Parses commands"""
        return

    # parses supported ecc curves from corresponding file
    @abc.abstractmethod
    def parse_ecc(self):
        """Parses ecc"""
        return

    # parses performance metrics from corresponding file
    @abc.abstractmethod
    def parse_performance(self):
        """Parses performance"""
        return
