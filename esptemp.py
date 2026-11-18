import machine
import ds18x20
import onewire
import time
import sys
import select

# Setup DS18B20 1-Wire on GPIO 4
dat_pin = machine.Pin(4)
ds = ds18x20.DS18X20(onewire.OneWire(dat_pin))
roms = ds.scan()
print("Found DS18B20 sensors:", roms)

# Setup control output (e.g. built-in LED on GPIO 2 or relay module)
control_pin = machine.Pin(2, machine.Pin.OUT)
control_pin.value(0)

# Non-blocking serial poll setup
sp = select.poll()
sp.register(sys.stdin, select.POLLIN)

while True:
    # Check for incoming serial commands from the PC GUI
    events = sp.poll(200) # Check every 200ms
    if events:
        line = sys.stdin.readline().strip()
        if line == "GET":
            if roms:
                try:
                    ds.convert_temp()
                    time.sleep_ms(750) # Conversion delay required by DS18B20
                    temp_c = ds.read_temp(roms[0])
                    print(f"TEMP:{temp_c:.2f}")
                except Exception as e:
                    print("TEMP:ERROR")
            else:
                print("TEMP:ERROR")
        elif line.startswith("RELAY:"):
            try:
                val = int(line.split(":")[1])
                control_pin.value(val)
                print(f"RELAY_OK:{val}")
            except Exception:
                print("RELAY_ERROR")

    time.sleep(0.1)