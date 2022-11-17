data = {
    'device_hosts': ['192.168.86.38', '192.168.86.42'],
    'service_port': '8060',  # The default port for Roku devices
    'shows': ['Good Witch', 'Star Trek: Picard', 'Hallmark Movies & Mysteries'],
    'channels': ['Netflix', 'Paramount+', 'FrndlyTV'],
    'channel_numbers': ['12', '31440', '298229'],
    'frndly_guide_position': 4,
    'netflix_search_int': 5,
    'paramount_search_int': 6,
    'primary_tv_start_time': [6, 29],
    'primary_tv_end_time': [21, 00],
    'secondary_tv_start_time': [19, 29],
    'secondary_tv_end_time': [22, 00],
    'update_delay': 3600,  # Each hour perform general housekeeping
    'interact_delay': 1200,  # Every 20 minutes perform time specific tasks
    'test_mode': False,  # This is only used for testing purposes - it should normally be FALSE
    'test_delay': 600  # How long to wait between test cycles
}
