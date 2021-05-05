#!/usr/bin/python3
# -*- coding: utf-8 -*-
# (c) B.Kerler 2018-2021 MIT License
import logging
from Library.utils import LogBase, logsetup
from Library.gpt import gpt


class Partition(metaclass=LogBase):
    def __init__(self, mtk, readflash, read_pmt, loglevel=logging.INFO):
        self.mtk = mtk
        self.__logger = logsetup(self, self.__logger, loglevel)
        self.config = self.mtk.config
        self.usbwrite = self.mtk.port.usbwrite
        self.usbread = self.mtk.port.usbread
        self.readflash = readflash
        self.read_pmt = read_pmt

    def get_gpt(self, gpt_num_part_entries, gpt_part_entry_size, gpt_part_entry_start_lba, parttype="user"):
        data = self.readflash(addr=0, length=2 * self.config.pagesize, filename="", parttype=parttype, display=False)
        if data[:9] == b"EMMC_BOOT" and self.read_pmt:
            partdata, partentries = self.read_pmt()
            if partdata == b"":
                return None, None
            else:
                return partdata, partentries
        elif data[:8] == b"UFS_BOOT" and self.read_pmt:
            partdata, partentries = self.read_pmt()
            if partdata == b"":
                return None, None
            else:
                return partdata, partentries
        if data == b"":
            return None, None
        guid_gpt = gpt(
            num_part_entries=gpt_num_part_entries,
            part_entry_size=gpt_part_entry_size,
            part_entry_start_lba=gpt_part_entry_start_lba,
        )
        header = guid_gpt.parseheader(data, self.config.pagesize)
        if "first_usable_lba" in header:
            sectors = header["first_usable_lba"]
            if sectors == 0:
                return None, None
            data = self.readflash(addr=0, length=sectors * self.config.pagesize, filename="",
                                  parttype=parttype, display=False)
            if data == b"":
                return None, None
            guid_gpt.parse(data, self.config.pagesize)
            return data, guid_gpt
        else:
            return None, None

    def get_backup_gpt(self, lun, gpt_num_part_entries, gpt_part_entry_size, gpt_part_entry_start_lba, parttype="user"):
        data = self.readflash(addr=0, length=2 * self.config.pagesize, filename="", parttype=parttype, display=False)
        if data == b"":
            return None
        guid_gpt = gpt(
            num_part_entries=gpt_num_part_entries,
            part_entry_size=gpt_part_entry_size,
            part_entry_start_lba=gpt_part_entry_start_lba,
        )
        header = guid_gpt.parseheader(data, self.config.SECTOR_SIZE_IN_BYTES)
        if "backup_lba" in header:
            sectors = header["first_usable_lba"] - 1
            data = self.readflash(addr=header["backup_lba"] * self.config.pagesize,
                                  length=sectors * self.config.pagesize, filename="",
                                  display=False)
            if data == b"":
                return None
            return data
        else:
            return None
