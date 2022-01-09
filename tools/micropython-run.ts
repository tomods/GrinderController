// This file is based on https://github.com/wokwi/rp2040js/blob/master/demo/micropython-run.ts
// It includes some basic input simulation to test GrinderController.

import { RP2040 } from '../src';
import { GDBTCPServer } from '../src/gdb/gdb-tcp-server';
import { USBCDC } from '../src/usb/cdc';
import { GPIOPinState, GPIOPinListener } from '../src/gpio-pin'
import { ConsoleLogger, LogLevel } from '../src/utils/logging';
import { bootromB1 } from './bootrom';
import { loadUF2, loadMicropythonFlashImage } from './load-flash';
import { hrtime } from 'process';
// import { TaskTimer } from 'tasktimer';
const NanoTimer = require('nanotimer');

const fs = require('fs');
const ws = fs.createWriteStream('/tmp/timelog');
const mcu = new RP2040();

const buttonGpio = mcu.gpio[3];
buttonGpio.setInputValue(true);

const ledGpio = mcu.gpio[25];
ledGpio.addListener((state: GPIOPinState, oldState: GPIOPinState) => {
  console.log(`rp2040js: LED change from ${oldState} to ${state}`);
});

const adc = mcu.adc;
let adcChannelValues = [0, 0, 0, 3456, 0];
let captureStartedForChannel = -1;
let lasttime = hrtime.bigint();
const timer = new NanoTimer();
timer.setInterval(() => {
  if (captureStartedForChannel >= 0) {
    const channel = captureStartedForChannel;
    captureStartedForChannel = -1;
    adc.completeADCRead(adcChannelValues[channel], false);

    // const now = hrtime.bigint();
    // const took = now - lasttime;
    // lasttime = now;
    // ws.write(took.toString() + '\n');
  }
}, '', '2u');
adc.onADCRead = (channel) => { captureStartedForChannel = channel };

mcu.loadBootrom(bootromB1);
mcu.logger = new ConsoleLogger(LogLevel.Error);
loadUF2('rp2-pico-20210902-v1.17.uf2', mcu);

if (fs.existsSync('littlefs.img')) {
  loadMicropythonFlashImage('littlefs.img', mcu);
}

// const gdbServer = new GDBTCPServer(mcu, 3333);
// console.log(`RP2040 GDB Server ready! Listening on port ${gdbServer.port}`);

const cdc = new USBCDC(mcu.usbCtrl);
cdc.onSerialData = (value) => {
  process.stdout.write(value);
};

process.stdin.setRawMode(true);
process.stdin.on('data', (chunk) => {
  // 24 is Ctrl+X
  if (chunk[0] === 24) {
    process.exit(0);
  }
  for (const byte of chunk) {
    cdc.sendSerialByte(byte);
  }
});

mcu.PC = 0x10000000;
mcu.execute();

setTimeout(() => adcChannelValues[3] = 1111, 1000 * 10);
setTimeout(() => buttonGpio.setInputValue(false), 1000 * 12);
setTimeout(() => buttonGpio.setInputValue(true),  1000 * 12 + 300);
setTimeout(() => adcChannelValues[3] = 900, 1000 * 12 + 100);
setTimeout(() => adcChannelValues[3] = 999, 1000 * 15);
setTimeout(() => buttonGpio.setInputValue(false), 1000 * 18);
setTimeout(() => buttonGpio.setInputValue(true),  1000 * 22);
setTimeout(() => adcChannelValues[3] = 4000, 1000 * 30);
setTimeout(() => buttonGpio.setInputValue(false), 1000 * 32);
setTimeout(() => buttonGpio.setInputValue(true),  1000 * 32 + 2);
setTimeout(() => buttonGpio.setInputValue(false), 1000 * 32 + 4);
setTimeout(() => buttonGpio.setInputValue(true),  1000 * 32 + 300);
setTimeout(() => buttonGpio.setInputValue(false), 1000 * 34);
setTimeout(() => buttonGpio.setInputValue(true), 1000 * 36);
