from littlefs import LittleFS

files = ['grinder_controller.py',
         'grinder_controller_states.py',
         'grinder_debouncer.py',
         'grinder_hardware.py',
         'rp_devices.py',
         'RP2040ADC.py',
         'main.py']

output_image = 'GrinderController.littlefs.img'

lfs = LittleFS(block_size=4096, block_count=352, prog_size=256)

for filename in files:
    with open(filename, 'rb') as src_file, lfs.open(filename, 'w') as lfs_file:
        lfs_file.write(src_file.read())

with open(output_image, 'wb') as fh:
    fh.write(lfs.context.buffer)
