import array
import uctypes
import rp_devices as devs
from machine import ADC


# Uses DMA and sniffing to provide fast reading of averaged ADC samples.
# Caution: Uses uctypes to directly fiddle with DMA and ADC registers.
#          For ADC, this should not be problematic. For DMA however,
#          this might clash with other users, including the C Pico SDK,
#          because the DMA channel is not "claimed" in SDK terms.
class Rp2040AdcDmaAveraging(ADC):
    def __init__(self, gpio_pin=26, dma_chan=0, adc_samples=32):
        super().__init__(gpio_pin)  # initializes ADC and pin/pad
        self._adc_samples = adc_samples
        self._adc_channel = gpio_pin - 26

        self._adc = devs.ADC_DEVICE
        self._dma_chan = devs.DMA_CHANS[dma_chan]
        self._dma = devs.DMA_DEVICE

        self._adc_buff = array.array('H', (0 for _ in range(self._adc_samples)))

        self._adc.FCS.THRESH = 1  # request DMA after every value
        self._adc.FCS.DREQ_EN = 1  # enable DMA requests
        self._adc.FCS.ERR = self._adc.FCS.SHIFT = 0
        self._adc.FCS.EN = 1  # enable FIFO – needed for DMA

        self._adc.CS.RROBIN = 0
        self._adc.CS.AINSEL = self._adc_channel

        self._adc.DIV_REG = 0  # full speed ahead

        self._dma_chan.READ_ADDR_REG = devs.ADC_FIFO_ADDR
        self._dma_chan.CTRL_TRIG_REG = 0
        self._dma_chan.CTRL_TRIG.CHAIN_TO = dma_chan  # no chaining
        self._dma_chan.CTRL_TRIG.INCR_WRITE = 1
        self._dma_chan.CTRL_TRIG.IRQ_QUIET = 1
        self._dma_chan.CTRL_TRIG.TREQ_SEL = devs.DREQ_ADC
        self._dma_chan.CTRL_TRIG.DATA_SIZE = 1  # 16-bit
        self._dma_chan.CTRL_TRIG.SNIFF_EN = 1

        self._dma.SNIFF_CTRL_REG = 0
        self._dma.SNIFF_CTRL.CALC = 0xf
        self._dma.SNIFF_CTRL.DMACH = dma_chan
        self._dma.SNIFF_CTRL.EN = 1

    # Discard any data in ADC FIFO
    def _drain_adc_fifo(self) -> None:
        while not self._adc.CS.READY:
            pass
        while not self._adc.FCS.EMPTY:
            _ = self._adc.FIFO_REG

    # Capture ADC samples using DMA
    def capture_start(self) -> None:
        self._drain_adc_fifo()
        self._dma.SNIFF_DATA = 0  # reset accumulator
        self._dma_chan.WRITE_ADDR_REG = uctypes.addressof(self._adc_buff)
        self._dma_chan.TRANS_COUNT_REG = self._adc_samples
        self._dma_chan.CTRL_TRIG.EN = 1
        self._adc.CS.AINSEL = self._adc_channel  # set again because read_u16() might have changed it
        self._adc.CS.START_MANY = 1

    def wait_and_read_average_u12(self) -> int:
        while self._dma_chan.CTRL_TRIG.BUSY:
            pass
        self._adc.CS.START_MANY = 0
        self._dma_chan.CTRL_TRIG.EN = 0
        #  Consider CS.EN = 0 to save power – but does it need to be reconfigured after?

        # DMA sniffing/summing does not work in rp2040js yet, so cannot use
        average = sum(self._adc_buff) // self._adc_samples
        # sniffavg = self._dma.SNIFF_DATA // self._adc_samples
        # print("avg {}, sniffavg {}".format(average, sniffavg))

        return average
