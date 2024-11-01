class BandwidthForUserSignup:
    """Estimate for X users signup at the same time, and X links per user
    How many machines are needed to handle this bandwidth ?
    """

    SERVER_BANDWIDTH = 1 * 1024 * 1024  # KBps
    SERVER_CORE = 8  # Core
    SERVER_RAM = 16  # GB
    MAX_TIME = 3 * 60  # Second
    AVG_FILE_SIZE = 200  # KB

    def __init__(self, users: int, links: int):
        self.users = users
        self.links = links

    @property
    def total_bandwidth_in_time(self):
        return self.SERVER_BANDWIDTH * self.MAX_TIME

    @property
    def total_links(self):
        return self.users * self.links

    @property
    def total_files_size(self):
        return self.AVG_FILE_SIZE * self.total_links

    @property
    def total_machines(self):
        return round(self.total_files_size / self.total_bandwidth_in_time, 2)

    def estimate(self):
        print(f"Total Size: {self.total_files_size / 1024 // 1024} GB")
        print(
            f"Bandwidth for 1 Machine in {self.MAX_TIME} Seconds: "
            f"{self.total_bandwidth_in_time / 1024 // 1024} GB"
        )
        print(f"Total Machines: {self.total_machines}")


BandwidthForUserSignup(1000, 1000).estimate()
