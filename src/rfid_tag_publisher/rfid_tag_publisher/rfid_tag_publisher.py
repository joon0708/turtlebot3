#!/usr/bin/env python3
import os, time, argparse
from typing import Optional, List
os.environ["ROS_DOMAIN_ID"] = "10"

import rclpy
from rclpy.node import Node
from std_msgs.msg import String as StringMsg
import spidev


def rst_hold_high(bcm_line=24, chip_name="gpiochip0"):
    try:
        import gpiod
    except Exception:
        return None
    try:
        try:
            chip = gpiod.Chip(chip_name)
            line = chip.get_line(bcm_line)
            line.request(consumer="rc522", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[1])
            return ("v1", chip, line)
        except Exception:
            req = gpiod.request_lines(
                chip_name,
                consumer="rc522",
                config={bcm_line: gpiod.LineSettings(direction=gpiod.LineDirection.OUTPUT, output_value=1)}
            )
            return ("v2", req, bcm_line)
    except Exception:
        return None

def rst_release(handle):
    if not handle:
        return
    try:
        ver = handle[0]
        if ver == "v1":
            _, chip, line = handle
            try: line.release()
            except Exception: pass
            try: chip.close()
            except Exception: pass
        else:
            _, req, _line = handle
            try: req.release()
            except Exception: pass
    except Exception:
        pass

class MFRC522:
    CommandReg=0x01; ComIEnReg=0x02; DivIEnReg=0x03; ComIrqReg=0x04; DivIrqReg=0x05; ErrorReg=0x06
    Status2Reg=0x08; FIFODataReg=0x09; FIFOLevelReg=0x0A; ControlReg=0x0C; BitFramingReg=0x0D
    ModeReg=0x11; TxControlReg=0x14; TxASKReg=0x15; CRCResultRegH=0x21; CRCResultRegL=0x22
    TModeReg=0x2A; TPrescalerReg=0x2B; TReloadRegH=0x2C; TReloadRegL=0x2D; VersionReg=0x37
    PCD_IDLE=0x00; PCD_CALCCRC=0x03; PCD_TRANSCEIVE=0x0C; PCD_SOFTRESET=0x0F
    PICC_REQIDL=0x26; PICC_ANTICOLL=0x93
    def __init__(self,bus=0,dev=0,speed=1000000):
        self.spi=spidev.SpiDev(); self.spi.open(bus,dev); self.spi.max_speed_hz=speed; self.spi.mode=0; self.init()
    def _w(self,reg,val): self.spi.xfer2([((reg<<1)&0x7E),val])
    def _r(self,reg): return self.spi.xfer2([((reg<<1)&0x7E)|0x80,0x00])[1]
    def _sb(self,reg,mask): self._w(reg,self._r(reg)|mask)
    def _cb(self,reg,mask): self._w(reg,self._r(reg)&(~mask&0xFF))
    def antenna_on(self):
        if ~(self._r(self.TxControlReg)) & 0x03: self._sb(self.TxControlReg,0x03)
    def init(self):
        self._w(self.CommandReg,self.PCD_SOFTRESET); time.sleep(0.05)
        self._w(self.TModeReg,0x8D); self._w(self.TPrescalerReg,0x3E); self._w(self.TReloadRegL,30); self._w(self.TReloadRegH,0)
        self._w(self.TxASKReg,0x40); self._w(self.ModeReg,0x3D); self.antenna_on()
    def _to_card(self,command,send):
        back=[]; back_len=0; irq_en=0x00; wait_irq=0x00
        if command==self.PCD_TRANSCEIVE: irq_en=0x77; wait_irq=0x30
        self._w(self.ComIEnReg,irq_en|0x80); self._cb(self.ComIrqReg,0x80); self._sb(self.FIFOLevelReg,0x80)
        for c in send: self._w(self.FIFODataReg,c)
        self._w(self.CommandReg,command)
        if command==self.PCD_TRANSCEIVE: self._sb(self.BitFramingReg,0x80)
        i=2000
        while True:
            n=self._r(self.ComIrqReg); i-=1
            if not (i!=0 and not(n&0x01) and not(n&wait_irq)): break
        self._cb(self.BitFramingReg,0x80)
        if i!=0:
            if (self._r(self.ErrorReg)&0x1B)==0x00:
                if command==self.PCD_TRANSCEIVE:
                    n=self._r(self.FIFOLevelReg); last_bits=self._r(self.ControlReg)&0x07
                    back_len=(n-1)*8+last_bits if last_bits else n*8
                    back=[self._r(self.FIFODataReg) for _ in range(n)]
                return True,back,back_len
        return False,[],0
    def request(self):
        self._w(self.BitFramingReg,0x07); ok,back,bl=self._to_card(self.PCD_TRANSCEIVE,[self.PICC_REQIDL])
        if not ok or bl!=0x10: return False,None
        return True,back
    def anticoll(self):
        self._w(self.BitFramingReg,0x00); ok,back,_=self._to_card(self.PCD_TRANSCEIVE,[self.PICC_ANTICOLL,0x20])
        if not ok or len(back)<5: return False,None
        return True,back[:5]
class RFIDTagPublisher(Node):
    def __init__(self):
        super().__init__("rfid_tag_publisher")
        
        # Declare parameters
        self.declare_parameter('bus', 0)
        self.declare_parameter('device', 0)
        self.declare_parameter('hold_ms', 80)
        self.declare_parameter('cooldown', 1.0)
        self.declare_parameter('grace_ms', 200)
        self.declare_parameter('whitelist', '')
        self.declare_parameter('rst_bcm', 24)
        
        # Get parameters
        self.bus = self.get_parameter('bus').value
        self.device = self.get_parameter('device').value
        hold_ms = self.get_parameter('hold_ms').value
        self.cooldown_sec = self.get_parameter('cooldown').value
        grace_ms = self.get_parameter('grace_ms').value
        whitelist_str = self.get_parameter('whitelist').value
        rst_bcm = self.get_parameter('rst_bcm').value
        
        self.hold_s = hold_ms / 1000.0
        self.grace_s = grace_ms / 1000.0
        
        # Parse whitelist
        if whitelist_str:
            whitelist = [u.strip().replace("-", ":") for u in whitelist_str.split(",") if u.strip()]
            self.whitelist = {u.upper() for u in whitelist}
        else:
            self.whitelist = None
        
        self.pub = self.create_publisher(StringMsg, "/rfid/tag", 10)
        self.rst_handle = rst_hold_high(rst_bcm) if rst_bcm >= 0 else None
        self.reader = MFRC522(bus=self.bus, dev=self.device)
        self.last_publish = 0.0
        self.active = False
        self.active_uid = None
        self.t_first = 0.0
        self.t_last = 0.0
        self.create_timer(0.03, self._tick)

    def _publish(self,uid:str):
        m=StringMsg(); m.data=uid; self.pub.publish(m)

    def _read_uid_once(self):
        ok,_=self.reader.request()
        if not ok: return None
        ok,uid5=self.reader.anticoll()
        if not ok: return None
        return ":".join(f"{b:02X}" for b in uid5[:-1])

    def _tick(self):
        now=time.time()
        if (now-self.last_publish)<self.cooldown_sec: return
        uid=self._read_uid_once()

        if uid and self.whitelist and uid.upper() not in self.whitelist:
            uid=None

        if uid:
            if not self.active or uid!=self.active_uid:
                self.active=True; self.active_uid=uid; self.t_first=now; self.t_last=now
            else:
                self.t_last=now
        else:
            if self.active and (now-self.t_last)<=self.grace_s:
                pass
            else:
                self.active=False; self.active_uid=None

        if self.active and (now-self.t_first)>=self.hold_s:
            self._publish(self.active_uid)
            self.last_publish=now
            self.active=False; self.active_uid=None

    def destroy_node(self):
        try: rst_release(self.rst_handle)
        except Exception: pass
        super().destroy_node()

def parse_args():
    ap=argparse.ArgumentParser()
    ap.add_argument("--bus",type=int,default=0)
    ap.add_argument("--device",type=int,default=0)
    ap.add_argument("--hold-ms",type=int,default=80)
    ap.add_argument("--cooldown",type=float,default=1.0)
    ap.add_argument("--grace-ms",type=int,default=200)
    ap.add_argument("--whitelist",type=str,default="")
    ap.add_argument("--rst-bcm",type=int,default=24)
    return ap.parse_args()

def main():
    rclpy.init()
    node = RFIDTagPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__=="__main__":
    main()
