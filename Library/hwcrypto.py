#!/usr/bin/python3
# -*- coding: utf-8 -*-
# (c) B.Kerler 2018-2021 MIT License
import logging
from Library.utils import LogBase, logsetup
from Library.hwcrypto_gcpu import GCpu
from Library.hwcrypto_dxcc import dxcc
from Library.hwcrypto_sej import sej
from Library.cqdma import cqdma

class crypto_setup:
    hwcode = None
    dxcc_base = None
    gcpu_base = None
    da_payload_addr = None
    sej_base = None
    read32 = None
    write32 = None
    writemem = None
    blacklist = None
    cqdma_base = None
    ap_dma_mem = None

class hwcrypto(metaclass=LogBase):
    def __init__(self, setup, loglevel=logging.INFO):
        self.__logger = logsetup(self, self.__logger, loglevel)

        self.dxcc = dxcc(setup, loglevel)
        self.gcpu = GCpu(setup, loglevel)
        self.sej = sej(setup, loglevel)
        self.cqdma = cqdma(setup, loglevel)
        self.hwcode = setup.hwcode
        self.setup = setup
        self.read32 = setup.read32
        self.write32 = setup.write32

    def aes_hwcrypt(self, data, iv=None, encrypt=True, mode="cbc", btype="sej"):
        if btype == "sej":
            if encrypt:
                if mode == "cbc":
                    return self.sej.hw_aes128_cbc_encrypt(buf=data, encrypt=True)
            else:
                if mode == "cbc":
                    return self.sej.hw_aes128_cbc_encrypt(buf=data, encrypt=False)
            if mode=="rpmb":
                return self.sej.generate_rpmb(meid=data)
        elif btype == "gcpu":
            addr = self.setup.da_payload_addr
            if mode == "ebc":
                return self.gcpu.aes_read_ebc(data=data, encrypt=encrypt)
            if mode == "cbc":
                if self.gcpu.aes_setup_cbc(addr=addr, data=data, iv=iv, encrypt=encrypt):
                    return self.gcpu.aes_read_cbc(addr=addr, encrypt=encrypt)
        elif btype == "dxcc":
            if mode == "fde":
                return self.dxcc.generate_fde()
            elif mode == "rpmb":
                return self.dxcc.generate_rpmb()
            elif mode == "t-fde":
                return self.dxcc.generate_trustonic_fde()
            elif mode == "prov":
                return self.dxcc.generate_provision_key()
        else:
            self.error("Unknown aes_hwcrypt type: " + btype)
            self.error("aes_hwcrypt supported types are: sej")
            return bytearray()

    def disable_hypervisor(self):
        self.write32(0x1021a060,self.read32(0x1021a060)|0x1)

    def disable_range_blacklist(self, btype, refreshcache):
        if btype == "gcpu":
            self.info("GCPU Init Crypto Engine")
            self.gcpu.init()
            self.gcpu.acquire()
            self.gcpu.init()
            self.gcpu.acquire()
            self.info("Disable Caches")
            refreshcache(0xB1)
            self.info("GCPU Disable Range Blacklist")
            self.gcpu.disable_range_blacklist()
        elif btype == "cqdma":
            self.info("Disable Caches")
            refreshcache(0xB1)
            self.info("CQDMA Disable Range Blacklist")
            self.cqdma.disable_range_blacklist()
