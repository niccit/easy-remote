data = {
    'device_hosts': ['primary.device.ip.address', 'secondary.device.ip.address'],
    'service_port': '8060',  # The default port for Roku devices
    'shows': ['Hallmark', 'Lavern/Shrily', 'TV Land'],
    'channels': ['YouTube TV', 'PlutoTv' 'YouTube TV'],
    'channel_numbers': ['12', '31440', '195316'],
    'frndly_guide_position': 4,
    'netflix_search_int': 5,
    'paramount_search_int': 6,
    'primary_tv_start_time': [6, 29],
    'primary_tv_end_time': [21, 00],
    'primary_tv_channel': "YouTube TV",  # Which show should we launch each morning on the primary TV
    'secondary_tv_start_time': [19, 29],
    'secondary_tv_end_time': [22, 00],
    'secondary_tv_channel': "YouTube TV",  # Which show should we launch each evening on the secondary TV
    'update_delay': 3600,  # Each hour perform general housekeeping
    'interact_delay': 1200,  # Every 20 minutes perform time specific tasks
    'remote_reboot_time': [1, 0]  # Reboot the remote, like pushing the reset button
}
