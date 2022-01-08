# GrinderController

Simple project based on the Raspberry Pi Pico and MicroPython to control a battery powered screwdriver, based on the
current load of its motor. Also controls battery charging.

The goal is to use this setup to power a (high quality) manual coffee grinder until all beans are ground and therefore
the motor power consumption drops – which is (hopefully) detectable by measuring the battery voltage.

## Hardware Design

To turn the motor on, the powered screwdriver to be used here uses a pushbutton to pull an N-channel MOSFET up. This
button press will be automated via GPIO by using a P-channel MOSFET in parallel to the button.

Another P-channel MOSFET will be able to switch the power jack on or off via GPIO to control charging of the
screwdriver's battery.

The grinding process will be started using an additional pushbutton connected to GPIO.

The Pico is powered from the battery via a switch and a Schottky diode.

For voltage sensing, the Pico's on-board VSYS measurement circuit connected to ADC3 will be used. This (hopefully)
avoids some headaches regarding the Pico's ADC peculiarities.

See also the hw_design files in this repo.

## Measuring the Voltage

This is probably the most interesting part of this project. The Pico's ADC noise properties are not particularly good
according to its datasheet. The goal is to capture with a high sampling rate and do some averaging to counteract this.

The idea on how to do this is to leverage the possibility to use DMA for ADC capturing, and also use DMA sniffing to
sum up the samples in hardware. This way, software only has to do a division as needed.

## License

Released under the MIT license. Copyright (c) 2022 Tobias Modschiedler
